# API Error Response Shapes

All Home Assistant API endpoints in PilotSuite HA integration use a standardized error response format based on `CommonErrorResponse` Pydantic model.

## Standard Error Format

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable error description",
  "field": "optional_field_name",
  "context": {}
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | `string` | ✅ | Machine-readable error code |
| `message` | `string` | ✅ | Human-readable error description |
| `field` | `string` | ❌ | Field that caused the error (validation) |
| `context` | `object` | ❌ | Additional debug information |

---

## Error Codes

### HTTP 400 - Bad Request / Validation Errors

```json
{
  "code": "VALIDATION_ERROR",
  "message": "user_id is required",
  "field": "user_id",
  "context": {"received": null}
}
```

```json
{
  "code": "VALIDATION_ERROR",
  "message": "comfort_bias must be a number between 0.0 and 1.0",
  "field": "comfort_bias",
  "context": {"received": "invalid", "expected_type": "float"}
}
```

```json
{
  "code": "INVALID_PAYLOAD",
  "message": "Request body must be a JSON object",
  "field": null,
  "context": {"received_type": "string"}
}
```

### HTTP 401 - Unauthorized

```json
{
  "code": "UNAUTHORIZED",
  "message": "Authentication required",
  "field": null,
  "context": {}
}
```

```json
{
  "code": "INVALID_TOKEN",
  "message": "The provided authentication token is invalid or expired",
  "field": null,
  "context": {}
}
```

### HTTP 403 - Forbidden

```json
{
  "code": "FORBIDDEN",
  "message": "You do not have permission to access this resource",
  "field": null,
  "context": {"resource": "user_preferences", "user_id": "abc123"}
}
```

### HTTP 404 - Not Found

```json
{
  "code": "NOT_FOUND",
  "message": "User preference not found",
  "field": null,
  "context": {"user_id": "abc123", "zone_id": "living_room"}
}
```

```json
{
  "code": "NOT_FOUND",
  "message": "The requested entity does not exist",
  "field": null,
  "context": {"entity_id": "light.living_room"}
}
```

### HTTP 422 - Unprocessable Entity

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "field": "comfort_bias",
  "context": {"errors": ["Value must be between 0.0 and 1.0"]}
}
```

### HTTP 500 - Internal Server Error

```json
{
  "code": "INTERNAL_ERROR",
  "message": "An unexpected error occurred",
  "field": null,
  "context": {}
}
```

```json
{
  "code": "INTERNAL_ERROR",
  "message": "Failed to retrieve user preferences",
  "field": null,
  "context": {"reason": "database_timeout", "user_id": "abc123"}
}
```

---

## Error Code Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `INVALID_PAYLOAD` | 400 | Request body is malformed |
| `INVALID_JSON` | 400 | Request body is not valid JSON |
| `UNAUTHORIZED` | 401 | Authentication required |
| `INVALID_TOKEN` | 401 | Token is invalid or expired |
| `FORBIDDEN` | 403 | Permission denied |
| `NOT_FOUND` | 404 | Resource does not exist |
| `RESOURCE_CONFLICT` | 409 | Resource already exists |
| `VALIDATION_ERROR` | 422 | Request validation failed (Pydantic) |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | External service unavailable |

---

## Usage in API Views

```python
from aiohttp import web
from .models import CommonErrorResponse
from . import _error_response

class UserPreferencesView(HomeAssistantView):
    """GET all preferences for a user."""

    async def get(self, request: web.Request) -> web.Response:
        user_id = request.match_info.get("user_id", "")
        if not user_id:
            return _error_response(
                code="VALIDATION_ERROR",
                message="user_id is required",
                field="user_id",
                status=400,
            )
```

## Migration Notes

- Old format `{"error": "message"}` → New format `{"code": "ERROR_CODE", "message": "..."}`
- Old format `{"message": "..."}` → New format with explicit `code` field
- Always include `context` when it helps debugging but never sensitive data (tokens, passwords)

---

## See Also

- [models.py](../../custom_components/copilot_ha/api/models.py) - `CommonErrorResponse` Pydantic model
- [user_preference.py](../../custom_components/copilot_ha/api/user_preference.py) - Migrated endpoints
