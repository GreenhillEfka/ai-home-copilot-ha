/**
 * Shared UI state components and telemetry helpers for PilotSuite screens.
 *
 * Provides:
 *  - StateSkeleton
 *  - StateEmpty
 *  - StateError
 *  - GlobalDegradedBanner
 *  - Unified UI telemetry event bus for state + retry events
 */

(function () {
  'use strict';

  const UI_STATE_EVENTS = Object.freeze({
    LOADING_SHOWN: 'ui_state_loading_shown',
    EMPTY_SHOWN: 'ui_state_empty_shown',
    ERROR_SHOWN: 'ui_state_error_shown',
    GLOBAL_DEGRADED_ON: 'ui_global_degraded_on',
    GLOBAL_DEGRADED_OFF: 'ui_global_degraded_off',
    RETRY_CLICKED: 'ui_state_retry_clicked',
    RETRY_SUCCEEDED: 'ui_state_retry_succeeded',
    RETRY_FAILED: 'ui_state_retry_failed'
  });

  const UI_ERROR_CLASS = Object.freeze({
    AUTH: 'auth',
    NETWORK: 'network',
    UNKNOWN: 'unknown'
  });

  // Stable public contract marker (for consumers / docs).
  const UI_STATE_API_VERSION = '1.0.1';

  const TELEMETRY_EVENT_KEYS = new Set(Object.values(UI_STATE_EVENTS));

  function isBrowser() {
    return typeof window !== 'undefined' && typeof document !== 'undefined';
  }

  class UiStateTelemetry {
    constructor(target = isBrowser() ? window : null) {
      this.target = target || null;
      this._listeners = new Map();
    }

    get isEnabled() {
      return !!this.target;
    }

    _ensurePayload(payload = {}) {
      return {
        ...payload,
        emittedAt: payload.emittedAt || new Date().toISOString()
      };
    }

    emit(eventName, payload = {}) {
      if (!this.isEnabled) {
        return { ...this._ensurePayload(payload), eventName };
      }

      const detail = this._ensurePayload(payload);
      detail.event = eventName;

      if (!TELEMETRY_EVENT_KEYS.has(eventName)) {
        console.warn(`[UI State Telemetry] unknown event: ${eventName}`);
      }

      const event = new CustomEvent(eventName, {
        detail,
        bubbles: true,
        cancelable: false
      });

      this.target.dispatchEvent(event);
      return event;
    }

    on(eventName, handler, options) {
      if (!this.isEnabled) return () => {};
      this.target.addEventListener(eventName, handler, options);
      return () => this.off(eventName, handler, options);
    }

    off(eventName, handler, options) {
      if (!this.isEnabled) return;
      this.target.removeEventListener(eventName, handler, options);
    }

    once(eventName, handler, options) {
      if (!this.isEnabled) return () => {};
      const wrapped = (...args) => {
        this.off(eventName, wrapped, options);
        return handler(...args);
      };
      this.on(eventName, wrapped, options);
      return () => this.off(eventName, wrapped, options);
    }
  }

  const telemetry = new UiStateTelemetry(isBrowser() ? window : null);

  function resolveElement(selectorOrElement) {
    if (!isBrowser()) return null;
    if (typeof selectorOrElement === 'string') return document.querySelector(selectorOrElement);
    return selectorOrElement || null;
  }

  function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function createStateShell({
    title,
    message,
    detail,
    icon,
    actionLabel,
    ariaLabel,
    stateClass,
    actionType
  }) {
    const actionText = actionLabel ? `<button type="button" class="ui-state-action" data-ui-state-action="${actionType || stateClass}">${escapeHtml(actionLabel)}</button>` : '';

    return `
      <section class="ui-state-shell ${stateClass}" aria-label="${escapeHtml(ariaLabel || title)}">
        <div class="ui-state-icon-wrap" aria-hidden="true">${icon}</div>
        <div class="ui-state-content">
          <h3 class="ui-state-title">${escapeHtml(title)}</h3>
          <p class="ui-state-message">${escapeHtml(message)}</p>
          ${detail ? `<p class="ui-state-detail">${escapeHtml(detail)}</p>` : ''}
          ${actionText}
        </div>
      </section>
    `;
  }

  class StateSkeleton {
    constructor(options = {}) {
      this.options = {
        container: null,
        scope: 'global',
        title: 'Ladevorgang',
        message: 'Daten werden geladen…',
        icon: '<span class="ui-state-spinner" aria-hidden="true">⟳</span>',
        ...options
      };
      this.root = null;
    }

    render(containerOverride = null) {
      const container = resolveElement(containerOverride || this.options.container);
      if (!container) {
        return null;
      }

      const html = createStateShell({
        type: 'skeleton',
        title: this.options.title,
        message: this.options.message,
        detail: this.options.detail,
        icon: this.options.icon,
        actionLabel: this.options.actionLabel,
        ariaLabel: this.options.ariaLabel || this.options.title,
        stateClass: 'ui-state-skeleton'
      });

      container.innerHTML = html;
      this.root = container.firstElementChild;
      telemetry.emit(UI_STATE_EVENTS.LOADING_SHOWN, {
        scope: this.options.scope,
        source: this.options.source || 'state_skeleton',
        message: this.options.message
      });
      return this;
    }

    clear() {
      if (this.root) {
        this.root.remove();
        this.root = null;
      }
      return this;
    }
  }

  class StateEmpty {
    constructor(options = {}) {
      this.options = {
        container: null,
        scope: 'global',
        title: 'Keine Daten',
        message: 'Es sind noch keine Daten verfügbar.',
        icon: '<span class="ui-state-icon" aria-hidden="true">📭</span>',
        actionLabel: null,
        onAction: null,
        ...options
      };
      this.root = null;
      this._boundClick = null;
    }

    _bindAction() {
      if (!this.root || !this.options.onAction || !this.options.actionLabel) {
        return;
      }

      const button = this.root.querySelector('[data-ui-state-action="empty"]');
      if (!button) return;

      this._boundClick = async () => {
        telemetry.emit(UI_STATE_EVENTS.RETRY_CLICKED, {
          scope: this.options.scope,
          action: this.options.actionLabel,
          source: this.options.source || 'state_empty'
        });

        try {
          button.disabled = true;
          button.textContent = 'Bitte warten...';
          const maybePromise = this.options.onAction();
          await Promise.resolve(maybePromise);
          telemetry.emit(UI_STATE_EVENTS.RETRY_SUCCEEDED, {
            scope: this.options.scope,
            action: this.options.actionLabel,
            source: this.options.source || 'state_empty'
          });
          button.disabled = false;
          button.textContent = this.options.actionLabel;
        } catch (error) {
          telemetry.emit(UI_STATE_EVENTS.RETRY_FAILED, {
            scope: this.options.scope,
            action: this.options.actionLabel,
            source: this.options.source || 'state_empty',
            error: error ? (error.message || String(error)) : 'unknown'
          });
          button.disabled = false;
          button.textContent = this.options.actionLabel;
        }
      };

      button.addEventListener('click', this._boundClick);
    }

    render(containerOverride = null) {
      const container = resolveElement(containerOverride || this.options.container);
      if (!container) {
        return null;
      }

      const html = createStateShell({
        title: this.options.title,
        message: this.options.message,
        detail: this.options.detail,
        icon: this.options.icon,
        actionLabel: this.options.actionLabel,
        ariaLabel: this.options.ariaLabel || this.options.title,
        stateClass: 'ui-state-empty',
        actionType: 'empty'
      });

      container.innerHTML = html;
      this.root = container.firstElementChild;
      this._bindAction();

      telemetry.emit(UI_STATE_EVENTS.EMPTY_SHOWN, {
        scope: this.options.scope,
        source: this.options.source || 'state_empty',
        message: this.options.message
      });

      return this;
    }

    clear() {
      if (this.root) {
        this.root.remove();
        this.root = null;
      }
      return this;
    }
  }

  class StateError {
    constructor(options = {}) {
      this.options = {
        container: null,
        scope: 'global',
        degraded: false,
        errorClass: UI_ERROR_CLASS.UNKNOWN,
        title: 'Es ist ein Fehler aufgetreten',
        message: 'Die Anfrage konnte nicht verarbeitet werden.',
        icon: '<span class="ui-state-icon" aria-hidden="true">⚠️</span>',
        actionLabel: 'Erneut versuchen',
        onRetry: null,
        ...options
      };
      this.root = null;
      this._boundRetry = null;
    }

    _bindRetry() {
      if (!this.root || !this.options.onRetry || !this.options.actionLabel) return;

      const button = this.root.querySelector('[data-ui-state-action="error"]');
      if (!button) return;

      this._boundRetry = async () => {
        telemetry.emit(UI_STATE_EVENTS.RETRY_CLICKED, {
          scope: this.options.scope,
          source: this.options.source || 'state_error',
          action: this.options.actionLabel
        });

        button.disabled = true;
        button.textContent = 'Bitte warten...';

        try {
          const result = this.options.onRetry();
          await Promise.resolve(result);
          telemetry.emit(UI_STATE_EVENTS.RETRY_SUCCEEDED, {
            scope: this.options.scope,
            source: this.options.source || 'state_error',
            action: this.options.actionLabel
          });
        } catch (error) {
          telemetry.emit(UI_STATE_EVENTS.RETRY_FAILED, {
            scope: this.options.scope,
            source: this.options.source || 'state_error',
            action: this.options.actionLabel,
            error: error ? (error.message || String(error)) : 'unknown'
          });
        } finally {
          button.disabled = false;
          button.textContent = this.options.actionLabel;
        }
      };

      button.addEventListener('click', this._boundRetry);
    }

    render(containerOverride = null) {
      const container = resolveElement(containerOverride || this.options.container);
      if (!container) {
        return null;
      }

      const html = createStateShell({
        title: this.options.title,
        message: this.options.message,
        detail: this.options.detail,
        icon: this.options.icon,
        actionLabel: this.options.actionLabel,
        ariaLabel: this.options.ariaLabel || this.options.title,
        stateClass: 'ui-state-error',
        actionType: 'error'
      });

      container.innerHTML = html;
      this.root = container.firstElementChild;
      this._bindRetry();

      telemetry.emit(UI_STATE_EVENTS.ERROR_SHOWN, {
        scope: this.options.scope,
        source: this.options.source || 'state_error',
        message: this.options.message,
        detail: this.options.detail,
        degraded: !!this.options.degraded,
        error_class: this.options.errorClass || UI_ERROR_CLASS.UNKNOWN
      });

      return this;
    }

    clear() {
      if (this.root) {
        this.root.remove();
        this.root = null;
      }
      return this;
    }
  }

  class GlobalDegradedBanner {
    constructor(options = {}) {
      this.options = {
        container: 'body',
        message: 'Warte auf Wiederverbindung · Teilfunktionen sind eingeschränkt.',
        scope: 'global',
        source: 'global_degraded_banner',
        autoWire: true,
        showClose: false,
        ...options
      };

      this.root = null;
      this.visible = false;
      this._listeners = [];

      this._ensureBanner();
      if (this.options.autoWire) {
        this._wireEvents();
      }
    }

    _ensureBanner() {
      if (!isBrowser()) return;

      let container;
      if (this.options.container === 'body') {
        container = document.body;
      } else {
        container = resolveElement(this.options.container);
      }
      if (!container) return;

      const existing = container.querySelector('.ui-global-degraded-banner');
      if (existing) {
        this.root = existing;
        return;
      }

      const host = document.createElement('div');
      host.className = 'ui-global-degraded-banner';
      host.setAttribute('role', 'status');
      host.setAttribute('aria-live', 'polite');
      host.setAttribute('hidden', 'true');
      host.innerHTML = `
        <div class="ui-global-degraded-banner__inner">
          <span class="ui-state-banner-icon" aria-hidden="true">⚠️</span>
          <p>${escapeHtml(this.options.message)}</p>
          ${this.options.showClose ? '<button type="button" class="ui-global-degraded-banner__close" data-action="close">Ausblenden</button>' : ''}
        </div>
      `;

      container.appendChild(host);
      this.root = host;

      if (this.options.showClose) {
        host.querySelector('[data-action="close"]').addEventListener('click', () => {
          this.hide('user-close');
        });
      }
    }

    _wireEvents() {
      if (!isBrowser()) return;
      this._listeners.push(
        telemetry.on(UI_STATE_EVENTS.ERROR_SHOWN, (event) => {
          const payload = event && event.detail ? event.detail : {};
          if (payload.degraded) {
            const message = payload.message || payload.detail || this.options.message;
            this.show(message, payload);
          }
        })
      );
      this._listeners.push(
        telemetry.on(UI_STATE_EVENTS.GLOBAL_DEGRADED_OFF, () => {
          this.hide('event');
        })
      );
    }

    show(message = null, payload = {}) {
      if (!this.root) return;
      if (message) {
        const messageNode = this.root.querySelector('p');
        if (messageNode) {
          messageNode.textContent = message;
        }
      }

      this.root.removeAttribute('hidden');
      requestAnimationFrame(() => {
        if (!this.root) return;
        this.root.classList.add('is-visible');
      });
      this.visible = true;

      telemetry.emit(UI_STATE_EVENTS.GLOBAL_DEGRADED_ON, {
        scope: this.options.scope,
        source: this.options.source,
        reason: payload.reason || null,
        sourceEvent: payload.event || payload.source || null
      });
      return this;
    }

    hide(reason = 'manual') {
      if (!this.root || !this.visible) {
        return this;
      }

      this.root.classList.remove('is-visible');
      this.root.setAttribute('hidden', 'true');
      this.visible = false;

      telemetry.emit(UI_STATE_EVENTS.GLOBAL_DEGRADED_OFF, {
        scope: this.options.scope,
        source: this.options.source,
        reason
      });
      return this;
    }

    setVisible(active, payload = {}) {
      if (active) {
        this.show(payload.message, payload);
      } else {
        this.hide('setVisible:false');
      }
      return this;
    }

    destroy() {
      this._listeners.forEach(dispose => {
        if (typeof dispose === 'function') dispose();
      });
      this._listeners = [];
      if (this.root) {
        this.root.remove();
      }
      this.root = null;
      this.visible = false;
    }
  }

  class UiStateToolkit {
    constructor({scope = 'global', degradedBanner = null} = {}) {
      this.scope = scope;
      this.degradedBanner = degradedBanner || null;
      this.events = UI_STATE_EVENTS;
      this.telemetry = telemetry;

      if (!this.degradedBanner) {
        this.degradedBanner = new GlobalDegradedBanner({ autoWire: false, scope });
      }
    }

    loading(container, options = {}) {
      return new StateSkeleton({ scope: this.scope, ...options }).render(container);
    }

    empty(container, options = {}) {
      return new StateEmpty({ scope: this.scope, ...options }).render(container);
    }

    error(container, options = {}) {
      return new StateError({ scope: this.scope, ...options }).render(container);
    }

    getBanner() {
      return this.degradedBanner;
    }

    setGlobalDegraded(active, payload = {}) {
      this.degradedBanner.setVisible(active, { message: payload.message, ...payload });
    }
  }

  window.UiState = {
    apiVersion: UI_STATE_API_VERSION,

    // Canonical UI telemetry event names.
    // Prefer using these constants instead of ad-hoc strings in widgets/cards.
    EventKeys: UI_STATE_EVENTS,
    Events: UI_STATE_EVENTS, // alias (stable)

    ErrorClass: UI_ERROR_CLASS,

    telemetry,

    // Convenience wrapper: accepts either a full event name ("ui_state_*" string)
    // or an enum-key ("LOADING_SHOWN"), and forwards to telemetry.emit().
    emit(eventNameOrKey, payload = {}) {
      const resolved = UI_STATE_EVENTS[eventNameOrKey] || eventNameOrKey;
      return telemetry.emit(resolved, payload);
    },

    StateSkeleton,
    StateEmpty,
    StateError,
    GlobalDegradedBanner,
    UiStateToolkit
  };
})();
