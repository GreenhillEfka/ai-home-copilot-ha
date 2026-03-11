from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, TypedDict

from aiohttp.web import Response, json_response

from homeassistant.core import HomeAssistant
from homeassistant.components import webhook

from .const import (
    CONF_TOKEN,
    CONF_WEBHOOK_ID,
    DOMAIN,
    HEADER_AUTH,
    HEADER_AUTH_LEGACY,
    ENV_LEGACY_HEADER_SUNSET_AT,
)

_LOGGER = logging.getLogger(__name__)

ENV_WEBHOOK_SIGNING_SECRET_PRIMARY = "PILOTSUITE_WEBHOOK_SIGNING_SECRET_PRIMARY"
ENV_WEBHOOK_SIGNING_SECRET_SECONDARY = "PILOTSUITE_WEBHOOK_SIGNING_SECRET_SECONDARY"
ENV_WEBHOOK_SIGNING_TIMESTAMP_TTL_SECONDS = "PILOTSUITE_WEBHOOK_SIGNING_TIMESTAMP_TTL_SECONDS"

HEADER_WEBHOOK_TIMESTAMP = "X-Webhook-Timestamp"
HEADER_WEBHOOK_NONCE = "X-Webhook-Nonce"
HEADER_WEBHOOK_SIGNATURE = "X-Webhook-Signature"

_SIGNATURE_SCHEME = "sha256="
_NONCE_RE = re.compile(r"^[0-9a-f]{32}$")

_SIGNING_NONCE_CACHE: dict[tuple[str, str], int] = {}
_SIGNING_NONCE_CACHE_LOCK = asyncio.Lock()
_SIGNING_NONCE_CACHE_MAX_ENTRIES = 10_000

# Canonical webhook event types (Core ↔ HA contract)
EVENT_TYPE_STATUS = "status"
EVENT_TYPE_MOOD = "mood"
EVENT_TYPE_SUGGESTION = "suggestion"
EVENT_TYPE_NEURON = "neuron"

_ALLOWED_EVENT_TYPES = {
    EVENT_TYPE_STATUS,
    EVENT_TYPE_MOOD,
    EVENT_TYPE_SUGGESTION,
    EVENT_TYPE_NEURON,
}

# Canonical aliases should continue to map directly; legacy aliases are only accepted in
# transition mode.
_EVENT_TYPE_CANONICAL_TO_CANONICAL = {
    EVENT_TYPE_STATUS: EVENT_TYPE_STATUS,
    EVENT_TYPE_MOOD: EVENT_TYPE_MOOD,
    EVENT_TYPE_SUGGESTION: EVENT_TYPE_SUGGESTION,
    EVENT_TYPE_NEURON: EVENT_TYPE_NEURON,
}

_EVENT_TYPE_LEGACY_ALIASES = {
    "mood_changed": EVENT_TYPE_MOOD,
    "suggestion_new": EVENT_TYPE_SUGGESTION,
    "neuron_update": EVENT_TYPE_NEURON,
}

_EVENT_TYPE_ALIAS_TO_CANONICAL = {
    **_EVENT_TYPE_CANONICAL_TO_CANONICAL,
    **_EVENT_TYPE_LEGACY_ALIASES,
}


class ErrorCodeSpec(TypedDict, total=False):
    status: int
    message: str
    required_details: tuple[str, ...]


ERROR_CODE_SPECS: dict[str, ErrorCodeSpec] = {
    # Envelope + payload validation
    "invalid_json": {
        "status": 400,
        "message": "Request body must be a valid JSON object.",
        "required_details": (),
    },
    "invalid_payload": {
        "status": 400,
        "message": "Request body must be a JSON object.",
        "required_details": ("expected",),
    },
    "missing_type": {
        "status": 400,
        "message": "Webhook envelope must include a non-empty 'type' field.",
        "required_details": ("required_field",),
    },
    "missing_data": {
        "status": 400,
        "message": "Webhook envelope must include a 'data' field.",
        "required_details": ("required_field",),
    },
    "invalid_data": {
        "status": 400,
        "message": "Webhook envelope field 'data' must be a JSON object.",
        "required_details": ("field", "expected"),
    },
    "unknown_type": {
        "status": 400,
        "message": "Unsupported webhook event type.",
        "required_details": ("received", "allowed"),
    },
    "legacy_type_unsupported": {
        "status": 400,
        "message": "Legacy webhook event type is not supported in sunset mode.",
        "required_details": ("received", "canonical_type", "mode"),
    },
    # Auth
    "invalid_token": {
        "status": 401,
        "message": "Webhook auth token is missing or invalid.",
        "required_details": ("sources",),
    },
    "legacy_header_sunset": {
        "status": 401,
        "message": "Legacy webhook auth header is no longer accepted after the configured sunset interval.",
        "required_details": ("header", "mode", "sunset_at", "sunset_at_raw"),
    },
    # Webhook signing (HMAC) verification
    "missing_signature_headers": {
        "status": 401,
        "message": "Webhook signature verification is enabled but required signature headers are missing or invalid.",
        "required_details": ("missing",),
    },
    "stale_timestamp": {
        "status": 401,
        "message": "Webhook signature timestamp is outside the allowed TTL window.",
        "required_details": ("ttl_seconds", "timestamp"),
    },
    "replay_detected": {
        "status": 401,
        "message": "Webhook nonce replay detected within the allowed TTL window.",
        "required_details": ("ttl_seconds",),
    },
    "invalid_signature": {
        "status": 401,
        "message": "Webhook signature verification failed.",
        "required_details": (),
    },
    # Resource guards
    "rate_limited": {
        "status": 429,
        "message": "Webhook rate limit exceeded.",
        "required_details": ("retry_after_seconds",),
    },
    "payload_too_large": {
        "status": 413,
        "message": "Webhook payload size exceeds allowed limit.",
        "required_details": ("max_bytes",),
    },
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _signing_config() -> dict[str, Any] | None:
    """Return signing config when enabled.

    Signing verification is opt-in: it is enabled when
    ``PILOTSUITE_WEBHOOK_SIGNING_SECRET_PRIMARY`` is set.
    """

    primary = os.getenv(ENV_WEBHOOK_SIGNING_SECRET_PRIMARY, "").strip()
    if not primary:
        return None

    secondary = os.getenv(ENV_WEBHOOK_SIGNING_SECRET_SECONDARY, "").strip() or None
    ttl_raw = os.getenv(ENV_WEBHOOK_SIGNING_TIMESTAMP_TTL_SECONDS, "").strip()
    ttl_default = 300
    ttl_min = 1
    ttl_max = 86_400

    ttl = ttl_default
    if ttl_raw:
        try:
            ttl = int(ttl_raw)
        except Exception:  # noqa: BLE001
            _LOGGER.warning(
                "Invalid %s value %r; using default %s",
                ENV_WEBHOOK_SIGNING_TIMESTAMP_TTL_SECONDS,
                ttl_raw,
                ttl_default,
            )
            ttl = ttl_default

    if ttl < ttl_min:
        _LOGGER.warning(
            "%s=%s below minimum %s; clamping",
            ENV_WEBHOOK_SIGNING_TIMESTAMP_TTL_SECONDS,
            ttl,
            ttl_min,
        )
        ttl = ttl_min
    if ttl > ttl_max:
        _LOGGER.warning(
            "%s=%s above maximum %s; clamping",
            ENV_WEBHOOK_SIGNING_TIMESTAMP_TTL_SECONDS,
            ttl,
            ttl_max,
        )
        ttl = ttl_max

    return {
        "primary": primary,
        "secondary": secondary,
        "ttl_seconds": ttl,
    }


def _compute_hmac_digest(*, secret: str, timestamp: int, nonce: str, body_bytes: bytes) -> str:
    signing_input = f"{timestamp}.{nonce}.".encode("utf-8") + body_bytes
    return hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).hexdigest()


def _parse_signature_headers(request) -> tuple[int | None, str | None, str | None, dict[str, Any]]:
    missing: list[str] = []
    raw_timestamp = (request.headers.get(HEADER_WEBHOOK_TIMESTAMP) or "").strip()
    raw_nonce = (request.headers.get(HEADER_WEBHOOK_NONCE) or "").strip().lower()
    raw_signature = (request.headers.get(HEADER_WEBHOOK_SIGNATURE) or "").strip()

    if not raw_timestamp:
        missing.append(HEADER_WEBHOOK_TIMESTAMP)
    if not raw_nonce:
        missing.append(HEADER_WEBHOOK_NONCE)
    if not raw_signature:
        missing.append(HEADER_WEBHOOK_SIGNATURE)

    timestamp: int | None = None
    if raw_timestamp:
        try:
            timestamp = int(raw_timestamp)
        except Exception:  # noqa: BLE001
            missing.append(HEADER_WEBHOOK_TIMESTAMP)

    nonce: str | None = None
    if raw_nonce and _NONCE_RE.fullmatch(raw_nonce):
        nonce = raw_nonce
    elif raw_nonce:
        missing.append(HEADER_WEBHOOK_NONCE)

    digest: str | None = None
    if raw_signature.startswith(_SIGNATURE_SCHEME):
        candidate = raw_signature[len(_SIGNATURE_SCHEME) :]
        if len(candidate) == 64:
            try:
                int(candidate, 16)
            except Exception:  # noqa: BLE001
                pass
            else:
                digest = candidate.lower()
    if raw_signature and digest is None:
        missing.append(HEADER_WEBHOOK_SIGNATURE)

    details: dict[str, Any] = {"missing": sorted(set(missing))}
    return timestamp, nonce, digest, details


async def _nonce_seen_or_mark(*, scope: str, nonce: str, now_epoch: int, ttl_seconds: int) -> bool:
    """Return True if nonce was seen in-window; else mark it and return False."""

    expires_at = now_epoch + ttl_seconds
    key = (scope, nonce)

    async with _SIGNING_NONCE_CACHE_LOCK:
        expired_keys = [
            cache_key
            for cache_key, expiry in _SIGNING_NONCE_CACHE.items()
            if expiry <= now_epoch
        ]
        for cache_key in expired_keys:
            del _SIGNING_NONCE_CACHE[cache_key]

        existing = _SIGNING_NONCE_CACHE.get(key)
        if existing is not None and existing > now_epoch:
            return True

        _SIGNING_NONCE_CACHE[key] = expires_at

        if len(_SIGNING_NONCE_CACHE) > _SIGNING_NONCE_CACHE_MAX_ENTRIES:
            over = len(_SIGNING_NONCE_CACHE) - _SIGNING_NONCE_CACHE_MAX_ENTRIES
            victims = sorted(_SIGNING_NONCE_CACHE.items(), key=lambda item: item[1])[:over]
            for victim_key, _expiry in victims:
                _SIGNING_NONCE_CACHE.pop(victim_key, None)

        return False


async def _verify_webhook_signature(
    request,
    *,
    body_bytes: bytes,
    scope: str,
    now_epoch: int,
    ttl_seconds: int,
    secret_primary: str,
    secret_secondary: str | None,
) -> tuple[bool, str | None, dict[str, Any] | None]:
    timestamp, nonce, digest, parse_details = _parse_signature_headers(request)
    if timestamp is None or nonce is None or digest is None:
        return False, "missing_signature_headers", parse_details

    if abs(now_epoch - timestamp) > ttl_seconds:
        return False, "stale_timestamp", {"ttl_seconds": ttl_seconds, "timestamp": timestamp}

    def _matches(secret: str) -> bool:
        expected = _compute_hmac_digest(
            secret=secret,
            timestamp=timestamp,
            nonce=nonce,
            body_bytes=body_bytes,
        )
        return hmac.compare_digest(expected, digest)

    if not _matches(secret_primary) and not (secret_secondary and _matches(secret_secondary)):
        return False, "invalid_signature", None

    if await _nonce_seen_or_mark(
        scope=scope,
        nonce=nonce,
        now_epoch=now_epoch,
        ttl_seconds=ttl_seconds,
    ):
        return False, "replay_detected", {"ttl_seconds": ttl_seconds}

    return True, None, None


def _parse_iso_utc(raw_value: str) -> datetime:
    value = raw_value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _legacy_header_window(*, now: datetime | None = None) -> dict[str, Any]:
    """Return transition/sunset mode for the legacy auth header window.

    Controlled via env var ``PILOTSUITE_WEBHOOK_LEGACY_HEADER_SUNSET_AT`` (ISO-8601).
    - Empty / unset → transition mode (legacy header accepted)
    - Invalid value → fail-closed (sunset)
    - Past timestamp → sunset mode (legacy header rejected)
    - Future timestamp → transition mode until timestamp
    """

    raw = os.getenv(ENV_LEGACY_HEADER_SUNSET_AT, "").strip()
    if not raw:
        return {"mode": "transition", "sunset_at": None, "sunset_at_raw": ""}

    try:
        sunset_at = _parse_iso_utc(raw)
    except Exception:  # noqa: BLE001
        _LOGGER.warning(
            "Invalid %s value %r; treating legacy header as sunset (reject)",
            ENV_LEGACY_HEADER_SUNSET_AT,
            raw,
        )
        sunset_at = datetime.fromtimestamp(0, tz=timezone.utc)

    now_ts = now or _utcnow()
    mode = "transition" if now_ts < sunset_at else "sunset"
    return {"mode": mode, "sunset_at": sunset_at, "sunset_at_raw": raw}


def _resolve_auth_tokens(request, *, now: datetime | None = None) -> tuple[list[tuple[str, str, dict[str, Any] | None]], dict[str, Any]]:
    """Collect auth tokens from canonical, bearer, and legacy headers.

    Returns tuple of (tokens, window) where tokens is a list of (source, token, error)
    and window is the current legacy-header window metadata.
    """

    window = _legacy_header_window(now=now)
    tokens: list[tuple[str, str, dict[str, Any] | None]] = []

    canonical = (request.headers.get(HEADER_AUTH) or "").strip()
    if canonical:
        tokens.append(("canonical", canonical, None))

    bearer_header = (request.headers.get("Authorization") or "").strip()
    if bearer_header.lower().startswith("bearer "):
        bearer_token = bearer_header.split(" ", 1)[1].strip()
        if bearer_token:
            tokens.append(("bearer", bearer_token, None))

    legacy = (request.headers.get(HEADER_AUTH_LEGACY) or "").strip()
    if legacy:
        if window["mode"] == "transition":
            tokens.append(("legacy", legacy, None))
        else:
            sunset_at = window["sunset_at"]
            tokens.append(
                (
                    "legacy",
                    legacy,
                    {
                        "header": HEADER_AUTH_LEGACY,
                        "mode": window["mode"],
                        "sunset_at": sunset_at.isoformat() if sunset_at else window["sunset_at_raw"],
                        "sunset_at_raw": window["sunset_at_raw"],
                    },
                )
            )

    return tokens, window


def _legacy_aliases_enabled() -> bool:
    """Return True when legacy alias event types are still allowed.

    Controlled via env var:
    - "transition" (default): legacy aliases accepted and mapped to canonical types.
    - "sunset": legacy aliases rejected with deterministic error code.
    """

    mode = os.getenv("PILOTSUITE_WEBHOOK_ALIAS_MODE", "transition").strip().lower()
    return mode not in {"sunset", "disabled", "off", "false", "0"}


def _normalize_event_type(raw_event_type: object, *, allow_legacy_aliases: bool = True) -> str:
    """Map legacy and canonical event types to canonical contract values.

    Returns a canonical type for known events, or the normalized raw string for
    unknown events.
    """

    if isinstance(raw_event_type, str):
        key = raw_event_type.strip().lower()
    else:
        key = ""

    if not key:
        return ""

    if (not allow_legacy_aliases) and key in _EVENT_TYPE_LEGACY_ALIASES:
        return key

    return _EVENT_TYPE_ALIAS_TO_CANONICAL.get(key, key)


def _normalize_error_details(code: str, provided: dict[str, Any] | None) -> dict[str, Any] | None:
    spec = ERROR_CODE_SPECS.get(code)
    if not spec:
        return provided

    details = dict(provided or {})
    for field in spec.get("required_details", ()):
        details.setdefault(field, None)
    return details or None


def _resolve_error_spec(code: str) -> ErrorCodeSpec | None:
    return ERROR_CODE_SPECS.get(code)


def _error_response(
    *,
    status: int | None = None,
    code: str,
    message: str | None = None,
    details: dict[str, Any] | None = None,
) -> Response:
    spec = _resolve_error_spec(code)
    resolved_status = status if status is not None else (spec["status"] if spec else 400)
    resolved_message = message or (spec["message"] if spec else "Webhook error")
    normalized_details = _normalize_error_details(code, details)

    payload: dict[str, Any] = {
        "ok": False,
        "error": {
            "code": code,
            "message": resolved_message,
        },
    }
    if normalized_details:
        payload["error"]["details"] = normalized_details
    return json_response(payload, status=resolved_status)


def _ok_response() -> Response:
    return json_response({"ok": True}, status=200)


def _make_webhook_url(hass: HomeAssistant, webhook_id: str) -> str:
    # Public base url or internal depending on HA config.
    return webhook.async_generate_url(hass, webhook_id)


async def async_ensure_webhook(hass: HomeAssistant, entry) -> str:
    webhook_id = entry.data.get(CONF_WEBHOOK_ID)
    if webhook_id:
        return webhook_id

    webhook_id = webhook.async_generate_id()
    hass.config_entries.async_update_entry(entry, data={**entry.data, CONF_WEBHOOK_ID: webhook_id})
    return webhook_id



def _merge_coordinator_data(coordinator, updates: dict) -> dict:
    """Merge partial updates into existing coordinator data dict."""
    current = coordinator.data if isinstance(coordinator.data, dict) else {}
    merged = {**current, **updates}
    return merged


async def async_register_webhook(hass: HomeAssistant, entry, coordinator) -> str:
    webhook_id = await async_ensure_webhook(hass, entry)

    async def _handle(hass: HomeAssistant, webhook_id: str, request):
        token_expected = (entry.data | entry.options).get(CONF_TOKEN)
        tokens, _window = _resolve_auth_tokens(request)

        def _matches_expected(candidate: str) -> bool:
            if not token_expected:
                return True
            return candidate == token_expected

        has_valid_token = any(
            error is None and _matches_expected(candidate) for _, candidate, error in tokens
        )
        sunset_error = next(
            (error for source, _, error in tokens if source == "legacy" and error is not None),
            None,
        )

        if token_expected and not has_valid_token:
            if sunset_error:
                return _error_response(
                    code="legacy_header_sunset",
                    details=sunset_error,
                )

            sources = [src for src, _, err in tokens if err is None] or ["missing"]
            _LOGGER.warning(
                "Rejected webhook: invalid_token (sources=%s)",
                sources,
            )
            return _error_response(
                code="invalid_token",
                details={"sources": sources},
            )

        signing = _signing_config()
        if signing:
            body_bytes = await request.read()
            now_epoch = int(_utcnow().timestamp())
            auth_scope_token = (
                token_expected
                if token_expected
                else next((candidate for _src, candidate, err in tokens if err is None), "")
            )
            scope = f"{webhook_id}:{auth_scope_token or 'missing'}"
            ok, error_code, details = await _verify_webhook_signature(
                request,
                body_bytes=body_bytes,
                scope=scope,
                now_epoch=now_epoch,
                ttl_seconds=int(signing["ttl_seconds"]),
                secret_primary=str(signing["primary"]),
                secret_secondary=signing.get("secondary"),
            )
            if not ok and error_code:
                _LOGGER.warning(
                    "Rejected webhook: %s (signing enabled)",
                    error_code,
                )
                return _error_response(code=error_code, details=details)

            try:
                payload = json.loads(body_bytes.decode("utf-8"))
            except Exception:  # noqa: BLE001
                return _error_response(
                    code="invalid_json",
                )
        else:
            try:
                payload = await request.json()
            except Exception:  # noqa: BLE001
                return _error_response(
                    code="invalid_json",
                )

        if not isinstance(payload, dict):
            return _error_response(
                code="invalid_payload",
                details={"expected": "object"},
            )

        if "type" not in payload or not isinstance(payload.get("type"), str) or not payload.get("type", "").strip():
            return _error_response(
                code="missing_type",
                details={"required_field": "type"},
            )

        if "data" not in payload:
            return _error_response(
                code="missing_data",
                details={"required_field": "data"},
            )

        data = payload.get("data")
        if not isinstance(data, dict):
            return _error_response(
                code="invalid_data",
                details={"field": "data", "expected": "object"},
            )

        # Typed envelope: {"type": "mood|neuron|suggestion|status", "data": {...}}
        allow_legacy_aliases = _legacy_aliases_enabled()
        raw_event_type = payload.get("type")
        event_type = _normalize_event_type(raw_event_type, allow_legacy_aliases=allow_legacy_aliases)

        if event_type in _EVENT_TYPE_LEGACY_ALIASES:
            return _error_response(
                code="legacy_type_unsupported",
                details={
                    "received": raw_event_type,
                    "canonical_type": _EVENT_TYPE_LEGACY_ALIASES[event_type],
                    "mode": "sunset",
                },
            )

        if event_type not in _ALLOWED_EVENT_TYPES:
            return _error_response(
                code="unknown_type",
                details={
                    "received": raw_event_type,
                    "allowed": sorted(_ALLOWED_EVENT_TYPES),
                },
            )

        if event_type == EVENT_TYPE_MOOD:
            # Add-on pushes mood change: merge into coordinator data
            updates = {
                "mood": data,
                "dominant_mood": data.get("mood", "unknown"),
                "mood_confidence": data.get("confidence", 0.0),
            }
            merged = _merge_coordinator_data(coordinator, updates)
            coordinator.async_set_updated_data(merged)
            _LOGGER.debug("Webhook: mood push received – %s", data.get("mood"))

        elif event_type == EVENT_TYPE_NEURON:
            # Add-on pushes neuron state update
            updates = {"neurons": data.get("neurons", {})}
            merged = _merge_coordinator_data(coordinator, updates)
            coordinator.async_set_updated_data(merged)
            _LOGGER.debug("Webhook: neuron update received")

        elif event_type == EVENT_TYPE_SUGGESTION:
            # Add-on pushes new suggestion – fire HA event for suggestion panel
            hass.bus.async_fire(
                f"{DOMAIN}_suggestion_received",
                {"suggestion": data},
            )
            _LOGGER.debug("Webhook: suggestion push received")

        else:
            # Legacy status push (online/version)
            online = data.get("online")
            version = data.get("version")

            updates = {}
            if online is not None:
                updates["ok"] = bool(online)
            if isinstance(version, str):
                updates["version"] = version

            if updates:
                merged = _merge_coordinator_data(coordinator, updates)
                coordinator.async_set_updated_data(merged)

        return _ok_response()

    webhook.async_register(
        hass,
        DOMAIN,
        f"PilotSuite webhook ({entry.entry_id})",
        webhook_id,
        _handle,
    )

    return webhook_id


async def async_unregister_webhook(hass: HomeAssistant, webhook_id: str) -> None:
    webhook.async_unregister(hass, webhook_id)
