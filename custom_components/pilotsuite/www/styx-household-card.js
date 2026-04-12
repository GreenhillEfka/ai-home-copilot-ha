/**
 * PilotSuite Styx Household Overview Card v1.0.0
 *
 * Lovelace custom card for household status at a glance.
 * Displays: health score, zone states, weather warnings, proactive alerts,
 * energy prices, fuel prices, persons home, notifications.
 *
 * Reads from multiple existing sensors:
 * - sensor.pilotsuite_home_health_score
 * - sensor.pilotsuite_weather_warnings
 * - sensor.pilotsuite_electricity_tariff
 * - sensor.pilotsuite_fuel_price_comparison
 * - sensor.pilotsuite_proactive_alerts
 * - sensor.pilotsuite_persons_home
 * - sensor.pilotsuite_habitus_zones
 */

const _HouseholdBase = window.StyxCardBase || HTMLElement;

class StyxHouseholdCard extends _HouseholdBase {
  constructor() {
    super();
    if (!this.shadowRoot) {
      this.attachShadow({ mode: 'open' });
      this._config = {};
      this._hass = null;
    }
  }

  static getConfigElement() {
    return document.createElement('hui-generic-entity-row');
  }

  static getStubConfig() {
    return { title: 'Haushaltsuebersicht' };
  }

  setConfig(config) {
    this._config = {
      title: config.title || 'Haushaltsuebersicht',
      show_weather: config.show_weather !== false,
      show_prices: config.show_prices !== false,
      show_alerts: config.show_alerts !== false,
      show_zones: config.show_zones !== false,
      weather_entity: config.weather_entity || 'weather.home',
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 5;
  }

  /* _esc and _sensorVal inherited from StyxCardBase when available */
  _esc(s) {
    if (typeof super._esc === 'function') return super._esc(s);
    if (typeof window.styxEsc === 'function') return window.styxEsc(s);
    const el = document.createElement('span');
    el.textContent = s || '';
    return el.innerHTML;
  }

  _sensorVal(entityId, fallback) {
    if (typeof super._sensorVal === 'function') return super._sensorVal(entityId, fallback);
    if (!this._hass) return fallback;
    const prefixes = ['sensor.pilotsuite_', 'sensor.copilot_ha_', 'sensor.copilot_'];
    const suffixes = entityId.startsWith('sensor.') ? [entityId] :
      prefixes.map(p => p + entityId);
    for (const eid of suffixes) {
      const s = this._hass.states[eid];
      if (s) return { state: s.state, attrs: s.attributes || {} };
    }
    return fallback;
  }

  _renderHealthScore() {
    const health = this._sensorVal('home_health_score', null);
    if (!health) return '';
    const score = parseInt(health.state, 10) || 0;
    let color = '#4caf50';
    let label = 'Gut';
    if (score < 50) { color = '#f44336'; label = 'Kritisch'; }
    else if (score < 75) { color = '#ff9800'; label = 'Achtung'; }

    return `
      <div class="section health-section" role="region" aria-label="Haus-Gesundheit">
        <div class="health-ring" style="--score:${score};--color:${color}">
          <svg viewBox="0 0 100 100" role="img" aria-labelledby="health-gauge-title">
            <title id="health-gauge-title">Haushaltsdaten-Anzeige</title>
            <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="8"/>
            <circle cx="50" cy="50" r="42" fill="none" stroke="${color}" stroke-width="8"
              stroke-dasharray="${2 * Math.PI * 42}" stroke-dashoffset="${2 * Math.PI * 42 * (1 - score / 100)}"
              stroke-linecap="round" transform="rotate(-90 50 50)"
              style="transition: stroke-dashoffset 0.8s ease;"/>
            <text x="50" y="46" text-anchor="middle" fill="${color}" font-size="20" font-weight="700">${score}</text>
            <text x="50" y="60" text-anchor="middle" fill="var(--secondary-text-color,#9fb1c3)" font-size="9">${label}</text>
          </svg>
        </div>
        <div class="health-label">Haus-Gesundheit</div>
      </div>`;
  }

  _renderPersons() {
    const persons = this._sensorVal('persons_home', null);
    if (!persons) return '';
    const count = parseInt(persons.state, 10) || 0;
    const names = persons.attrs.person_names || persons.attrs.persons || [];
    return `
      <div class="stat-chip">
        <span class="stat-icon">mdi:account-group</span>
        <span class="stat-val">${count}</span>
        <span class="stat-label">${names.length ? names.join(', ') : (count === 1 ? 'Person' : 'Personen')}</span>
      </div>`;
  }

  _renderWeather() {
    if (!this._config.show_weather || !this._hass) return '';

    // HA weather entity
    const weather = this._hass.states[this._config.weather_entity];
    const warnings = this._sensorVal('weather_warnings', null);

    let weatherHtml = '';
    if (weather) {
      const temp = weather.attributes.temperature || '--';
      const cond = weather.state || '--';
      const condMap = {
        sunny: 'Sonnig', cloudy: 'Bewoelkt', rainy: 'Regnerisch',
        'partly-cloudy': 'Teilweise bewoelkt', snowy: 'Schnee',
        fog: 'Nebel', lightning: 'Gewitter', clear: 'Klar',
        'clear-night': 'Klar (Nacht)', partlycloudy: 'Teilweise bewoelkt',
      };
      weatherHtml = `
        <div class="weather-current">
          <span class="weather-temp">${temp}°C</span>
          <span class="weather-cond">${this._esc(condMap[cond] || cond)}</span>
        </div>`;
    }

    let warningHtml = '';
    if (warnings && parseInt(warnings.state, 10) > 0) {
      const attrs = warnings.attrs;
      const severity = attrs.highest_severity || 'minor';
      const sevColor = severity === 'extreme' ? '#f44336' : severity === 'severe' ? '#ff5722' : '#ff9800';
      const warnList = (attrs.warnings || []).slice(0, 3);
      warningHtml = `
        <div class="warnings" style="border-color:${sevColor}40">
          <div class="warn-header" style="color:${sevColor}">
            ${warnings.state} Wetterwarnungen (${this._esc(severity)})
          </div>
          ${warnList.map(w => `<div class="warn-item">${this._esc(w.headline || w.event || w.description || '')}</div>`).join('')}
        </div>`;
    }

    if (!weatherHtml && !warningHtml) return '';
    return `
      <div class="section" role="region" aria-label="Wetter und Umwelt">
        <div class="section-title">Wetter & Umwelt</div>
        ${weatherHtml}
        ${warningHtml}
      </div>`;
  }

  _renderAlerts() {
    if (!this._config.show_alerts) return '';
    const alerts = this._sensorVal('proactive_alerts', null);
    if (!alerts || parseInt(alerts.state, 10) === 0) return '';

    const attrs = alerts.attrs;
    const alertList = (attrs.alerts || []).slice(0, 5);
    const priorityColors = { critical: '#f44336', warning: '#ff9800', advisory: '#2196f3', info: '#4caf50' };

    return `
      <div class="section" role="region" aria-label="Warnungen und Hinweise">
        <div class="section-title">Warnungen & Hinweise</div>
        ${alertList.map(a => {
          const pColor = priorityColors[a.priority] || '#607d8b';
          return `
            <div class="alert-item" style="border-left-color:${pColor}">
              <span class="alert-priority" style="color:${pColor}">${this._esc(a.priority || '')}</span>
              <span class="alert-text">${this._esc(a.title || a.message || '')}</span>
            </div>`;
        }).join('')}
      </div>`;
  }

  _renderPrices() {
    if (!this._config.show_prices) return '';

    const elec = this._sensorVal('electricity_tariff', null);
    const fuel = this._sensorVal('fuel_price_comparison', null);

    if (!elec && !fuel) return '';

    let elecHtml = '';
    if (elec) {
      const price = parseFloat(elec.state) || 0;
      const level = (elec.attrs.current_level || '').toLowerCase();
      const levelColor = level === 'guenstig' || level === 'low' ? '#4caf50' :
                         level === 'teuer' || level === 'high' ? '#f44336' : '#ff9800';
      elecHtml = `
        <div class="price-card">
          <div class="price-label">Strom</div>
          <div class="price-value" style="color:${levelColor}">${price.toFixed(1)} ct/kWh</div>
          <div class="price-level" style="color:${levelColor}">${this._esc(level || 'normal')}</div>
          ${elec.attrs.min_hour ? `<div class="price-hint">Guenstigste Stunde: ${this._esc(elec.attrs.min_hour)}</div>` : ''}
        </div>`;
    }

    let fuelHtml = '';
    if (fuel) {
      const diesel = parseFloat(fuel.attrs.diesel_avg_eur_l) || 0;
      const benzin = parseFloat(fuel.attrs.benzin_avg_eur_l || fuel.attrs.e10_avg_eur_l) || 0;
      fuelHtml = `
        <div class="price-card">
          <div class="price-label">Treibstoff</div>
          ${diesel ? `<div class="price-row"><span>Diesel</span><span>${diesel.toFixed(3)} EUR/L</span></div>` : ''}
          ${benzin ? `<div class="price-row"><span>Benzin</span><span>${benzin.toFixed(3)} EUR/L</span></div>` : ''}
          ${fuel.attrs.savings_vs_diesel_eur ? `<div class="price-hint">Ersparnis EV: ${fuel.attrs.savings_vs_diesel_eur} EUR/100km</div>` : ''}
        </div>`;
    }

    return `
      <div class="section" role="region" aria-label="Preise und Tarife">
        <div class="section-title">Preise & Tarife</div>
        <div class="prices-grid">${elecHtml}${fuelHtml}</div>
      </div>`;
  }

  _renderZones() {
    if (!this._config.show_zones) return '';
    const zones = this._sensorVal('habitus_zones', null);
    if (!zones) return '';

    const zoneList = zones.attrs.zones || zones.attrs.zone_list || [];
    if (zoneList.length === 0) return '';

    const zoneIcons = {
      living: 'mdi:sofa', bath: 'mdi:shower', kitchen: 'mdi:chef-hat',
      office: 'mdi:desk', bedroom: 'mdi:bed', hallway: 'mdi:door',
      terrace: 'mdi:flower', outside: 'mdi:tree',
    };

    return `
      <div class="section" role="region" aria-label="Zonen-Status">
        <div class="section-title">Zonen-Status</div>
        <div class="zones-grid">
          ${zoneList.slice(0, 12).map(z => {
            const name = z.name || z.name_de || z.zone_id || '';
            const status = z.status || z.mode || 'idle';
            const entities = z.entity_count || (z.entity_ids ? z.entity_ids.length : 0);
            const occupied = z.occupied || z.occupancy || false;
            const icon = zoneIcons[z.zone_type || z.zone_id] || 'mdi:home';
            const statusColor = status === 'active' ? '#4caf50' : status === 'sleeping' ? '#9c27b0' : '#607d8b';

            return `
              <div class="zone-chip" style="border-color:${statusColor}40">
                <span class="zone-dot" style="background:${occupied ? '#4caf50' : '#607d8b'}"></span>
                <span class="zone-name">${this._esc(name)}</span>
                <span class="zone-entities">${entities}</span>
              </div>`;
          }).join('')}
        </div>
      </div>`;
  }

  _render() {
    const designTokens = typeof this._designTokens === 'function' ? this._designTokens() : '';
    this.shadowRoot.innerHTML = `
      <style>
        ${designTokens}
        :host { display: block; }
        .card {
          background: var(--card-background-color, #1a1a2e);
          border-radius: var(--ha-card-border-radius, 12px);
          padding: 16px;
          color: var(--primary-text-color, #e6eef6);
          font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        .title { font-size: 16px; font-weight: 600; }
        .top-row {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-bottom: 16px;
          flex-wrap: wrap;
        }
        .health-section {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .health-ring { width: 80px; height: 80px; }
        .health-ring svg { width: 100%; height: 100%; }
        .health-label {
          font-size: 12px;
          color: var(--secondary-text-color, #9fb1c3);
        }
        .stat-chip {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          background: rgba(255,255,255,0.04);
          border-radius: 8px;
        }
        .stat-icon { font-size: 16px; }
        .stat-val { font-size: 18px; font-weight: 700; }
        .stat-label { font-size: 11px; color: var(--secondary-text-color, #9fb1c3); }
        .section {
          margin-bottom: 16px;
        }
        .section-title {
          font-size: 13px;
          font-weight: 600;
          color: var(--secondary-text-color, #9fb1c3);
          margin-bottom: 8px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .weather-current {
          display: flex;
          align-items: baseline;
          gap: 8px;
          margin-bottom: 8px;
        }
        .weather-temp { font-size: 24px; font-weight: 700; }
        .weather-cond { font-size: 14px; color: var(--secondary-text-color, #9fb1c3); }
        .warnings {
          padding: 8px 12px;
          border-radius: 8px;
          border-left: 3px solid #ff9800;
          background: rgba(255,152,0,0.05);
        }
        .warn-header {
          font-size: 12px;
          font-weight: 600;
          margin-bottom: 4px;
        }
        .warn-item {
          font-size: 11px;
          color: var(--secondary-text-color, #9fb1c3);
          margin-bottom: 2px;
        }
        .alert-item {
          display: flex;
          gap: 8px;
          align-items: center;
          padding: 6px 10px;
          margin-bottom: 4px;
          border-left: 3px solid #607d8b;
          background: rgba(255,255,255,0.03);
          border-radius: 0 6px 6px 0;
        }
        .alert-priority {
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          min-width: 50px;
        }
        .alert-text {
          font-size: 12px;
          flex: 1;
        }
        .prices-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 8px;
        }
        .price-card {
          padding: 10px;
          background: rgba(255,255,255,0.04);
          border-radius: 8px;
        }
        .price-label {
          font-size: 11px;
          color: var(--secondary-text-color, #9fb1c3);
          margin-bottom: 4px;
        }
        .price-value {
          font-size: 18px;
          font-weight: 700;
        }
        .price-level {
          font-size: 11px;
          font-weight: 600;
        }
        .price-row {
          display: flex;
          justify-content: space-between;
          font-size: 12px;
          margin-bottom: 2px;
        }
        .price-hint {
          font-size: 10px;
          color: var(--secondary-text-color, #9fb1c3);
          margin-top: 4px;
        }
        .zones-grid {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
        .zone-chip {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border-radius: 6px;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.08);
          font-size: 12px;
        }
        .zone-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          flex-shrink: 0;
        }
        .zone-name { font-weight: 500; }
        .zone-entities {
          font-size: 10px;
          color: var(--secondary-text-color, #9fb1c3);
          padding: 0 4px;
          background: rgba(255,255,255,0.06);
          border-radius: 4px;
        }
      </style>
      <div class="card">
        <div class="header">
          <span class="title">${this._esc(this._config.title)}</span>
        </div>
        <div class="top-row">
          ${this._renderHealthScore()}
          ${this._renderPersons()}
        </div>
        ${this._renderWeather()}
        ${this._renderAlerts()}
        ${this._renderPrices()}
        ${this._renderZones()}
      </div>`;
  }
}

if (typeof registerStyxCard === 'function') {
  registerStyxCard('styx-household-card', StyxHouseholdCard, {
    name: 'PilotSuite Haushaltsuebersicht',
    description: 'Haushaltsuebersicht mit Gesundheits-Score, Wetter, Preise und Zonen-Status',
  });
} else {
  customElements.define('styx-household-card', StyxHouseholdCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: 'styx-household-card',
    name: 'PilotSuite Haushaltsuebersicht',
    description: 'Haushaltsuebersicht mit Gesundheits-Score, Wetter, Preise und Zonen-Status',
  });
}
