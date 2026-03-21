/**
 * PilotSuite Zone Dashboard Card v2.1.0
 *
 * Lovelace custom card showing zone status, mood, neuron activity,
 * and quick actions. Reads from sensor.copilot_ha_habitus_zones and
 * sensor.copilot_ha_zone_modes entities.
 *
 * v14.2.0 additions:
 * - Health Score Badge (from sensor.pilotsuite_zonen_gesundheit)
 * - Module State Indicators (from sensor.pilotsuite_autonomie_status)
 * - Autonomy Action Mini-Log (from sensor.pilotsuite_autonomie_verlauf)
 *
 * Features:
 * - Zone Status (active/inactive indicator)
 * - Health Score Badge (color-coded 0-100)
 * - Module State Indicators (licht, musik, etc.)
 * - Mood gauges (Comfort, Joy, Frugality per zone)
 * - Neuron Activity visualization
 * - Autonomy Action Mini-Log (last 3 actions)
 * - Quick Actions (toggle, scene selection)
 */

const ZONE_ICON_MAP = {
  // English keys (frontend cards)
  living_room: 'mdi:sofa',
  bedroom: 'mdi:bed',
  kitchen: 'mdi:chef-hat',
  bathroom: 'mdi:shower',
  office: 'mdi:desk',
  outdoor: 'mdi:tree',
  default: 'mdi:floor-plan',
  // German zone IDs from zone_auto_setup.py (habitus zones)
  wohnbereich:    'mdi:sofa',
  badbereich:     'mdi:shower',
  kochbereich:    'mdi:stove',
  buerobereich:   'mdi:desk',
  gangbereich:    'mdi:door-open',
  schlafbereich:  'mdi:bed',
  kellerbereich:  'mdi:home-floor-negative-1',
  zimmer_mira:    'mdi:bed-single-outline',
  zimmer_paul:    'mdi:bed-single-outline',
  aussenbereich:  'mdi:tree',
};

const MOOD_GAUGE_DEFS = [
  { key: 'comfort', label: 'Comfort', start: '#2196f3', end: '#4caf50' },
  { key: 'joy', label: 'Joy', start: '#ff9800', end: '#f9d71c' },
  { key: 'frugality', label: 'Frugality', start: '#9c27b0', end: '#00bcd4' },
];

const MODE_ICONS = {
  party: 'mdi:party-popper',
  kids_sleep: 'mdi:baby-face-outline',
  movie: 'mdi:movie-open',
  guest: 'mdi:account-group',
  focus: 'mdi:head-lightbulb',
  away: 'mdi:home-export-outline',
  night: 'mdi:weather-night',
  romantic: 'mdi:heart',
  relaxing: 'mdi:meditation',
  focus_work: 'mdi:briefcase',
};

const _ZoneBase = window.StyxCardBase || HTMLElement;

class StyxZoneCard extends _ZoneBase {
  constructor() {
    super();
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
  }

  static getConfigElement() {
    return document.createElement('hui-generic-entity-row');
  }

  static getStubConfig() {
    return {
      entity: 'sensor.copilot_ha_habitus_zones',
      show_mood: true,
      show_neuron_activity: true,
      show_quick_actions: true,
      show_health_score: true,
      show_module_states: true,
      show_autonomy_log: true,
      show_presence_hold: true,
    };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define an entity');
    }
    this._config = {
      ...config,
      show_mood: config.show_mood !== false,
      show_neuron_activity: config.show_neuron_activity !== false,
      show_quick_actions: config.show_quick_actions !== false,
      show_health_score: config.show_health_score !== false,
      show_module_states: config.show_module_states !== false,
      show_autonomy_log: config.show_autonomy_log !== false,
      show_presence_hold: config.show_presence_hold !== false,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  _getZoneIcon(zoneId) {
    // Strip "zone:" prefix, then normalize
    const key = zoneId.replace(/^zone:/, '').toLowerCase().replace(/[^a-z_]/g, '_');
    return ZONE_ICON_MAP[key] || ZONE_ICON_MAP.default;
  }

  _getModeIcon(modeId) {
    return MODE_ICONS[modeId] || 'mdi:toggle-switch';
  }

  _getZonesData() {
    if (!this._hass || !this._config.entity) return { zones: [], active_zones: 0 };

    const state = this._hass.states[this._config.entity];
    if (!state) return { zones: [], active_zones: 0 };

    const attrs = state.attributes || {};
    const zones = attrs.zones || [];

    return {
      zones: zones,
      total_zones: attrs.total_zones || zones.length,
      active_zones: attrs.active_zones || 0,
      modes: attrs.modes || {},
    };
  }

  _getMoodData(zoneId) {
    const prefix = `sensor.pilotsuite_mood_${zoneId}`;
    return MOOD_GAUGE_DEFS.map(def => {
      const entityId = `${prefix}_${def.key}`;
      const state = this._hass?.states[entityId];
      const parsed = state ? parseFloat(state.state) : null;
      const hasNumeric = Number.isFinite(parsed);

      return {
        ...def,
        entityId,
        value: hasNumeric ? Math.max(0, Math.min(100, parsed)) : null,
        available: Boolean(state) && hasNumeric,
      };
    });
  }

  _getNeuronActivity(zoneId) {
    const nodeEntity = this._hass?.states['sensor.pilotsuite_brain_graph_nodes'];
    if (!nodeEntity) {
      return {
        available: false,
        active: null,
        total: null,
        score: null,
        missingReason: 'Sensordaten fehlen',
      };
    }

    const nodes = Array.isArray(nodeEntity.attributes?.nodes) ? nodeEntity.attributes.nodes : [];
    const zoneNodes = nodes.filter(n => n.zone === zoneId || (Array.isArray(n.rooms) && n.rooms.includes(zoneId)));

    if (zoneNodes.length === 0) {
      return {
        available: false,
        active: null,
        total: null,
        score: null,
        missingReason: 'Subsensoren fehlen',
      };
    }

    const scoreValues = zoneNodes
      .map(n => Number(n.score))
      .filter(v => Number.isFinite(v));

    return {
      available: true,
      active: zoneNodes.filter(n => n.state === 'on').length,
      total: zoneNodes.length,
      score: scoreValues.length > 0
        ? scoreValues.reduce((acc, value) => acc + value, 0) / scoreValues.length
        : null,
      scoreMissing: scoreValues.length === 0,
    };
  }

  _hasNeuronActivity(zoneId) {
    const nodeEntity = this._hass?.states['sensor.pilotsuite_brain_graph_nodes'];
    if (!nodeEntity) return false;
    const nodes = Array.isArray(nodeEntity.attributes?.nodes) ? nodeEntity.attributes.nodes : [];
    return nodes.some(n => n.zone === zoneId || (Array.isArray(n.rooms) && n.rooms.includes(zoneId)));
  }

  _getHealthScore(zoneId) {
    const healthEntity = this._hass?.states['sensor.pilotsuite_zonen_gesundheit'];
    if (!healthEntity) return null;

    const zones = healthEntity.attributes?.zones;
    if (!zones || typeof zones !== 'object') return null;

    // Helper to clamp and validate a score value
    const _clamp = (v) => {
      const parsed = Number(v);
      return Number.isFinite(parsed) ? Math.max(0, Math.min(100, Math.round(parsed))) : null;
    };

    // Try object format: zones[key] = { score, status, zone_name }
    // Keys may or may not have "zone:" prefix
    const candidates = [zoneId, `zone:${zoneId}`, zoneId.replace(/_/g, ' ')];
    for (const key of candidates) {
      const entry = zones[key];
      if (entry !== undefined && entry !== null) {
        // Object format with .score property
        if (typeof entry === 'object' && entry.score !== undefined) {
          return _clamp(entry.score);
        }
        // Direct numeric value (legacy fallback)
        const direct = _clamp(entry);
        if (direct !== null) return direct;
      }
    }

    // Also try stripping "zone:" from zoneId if it already has the prefix
    if (zoneId.startsWith('zone:')) {
      const stripped = zoneId.slice(5);
      const entry = zones[stripped];
      if (entry !== undefined && entry !== null) {
        if (typeof entry === 'object' && entry.score !== undefined) {
          return _clamp(entry.score);
        }
        const direct = _clamp(entry);
        if (direct !== null) return direct;
      }
    }

    // Try matching by zone_id or name keys in array format
    if (Array.isArray(zones)) {
      const match = zones.find(z =>
        z.zone_id === zoneId || z.zone_id === `zone:${zoneId}` ||
        z.name?.toLowerCase().replace(/\s+/g, '_') === zoneId
      );
      if (match) {
        const s = match.score ?? match.health_score;
        if (s !== undefined) return _clamp(s);
      }
    }

    return null;
  }

  _getHealthColor(score) {
    if (score >= 80) return 'var(--ps-green, #22c55e)';
    if (score >= 50) return 'var(--ps-orange, #f59e0b)';
    return 'var(--ps-red, #ef4444)';
  }

  _getHealthLabel(score) {
    if (score >= 80) return 'healthy';
    if (score >= 50) return 'degraded';
    return 'critical';
  }

  // ── Presence Hold ─────────────────────────────────────────────────────────

  _getPresenceHoldState(zone) {
    return zone?.presence_hold || 'auto';
  }

  _buildHoldPills(zoneId, holdState) {
    const pills = [
      { value: 'auto',      label: 'Auto', icon: 'mdi:auto-mode' },
      { value: 'force_on',  label: 'An',   icon: 'mdi:account-check' },
      { value: 'force_off', label: 'Aus',  icon: 'mdi:account-cancel' },
    ];
    return `
      <div class="zone-card-hold" data-zone="${zoneId}">
        <span class="hold-label">Anwesenheit:</span>
        <div class="hold-pills">
          ${pills.map(p => `
            <button class="hold-pill ${p.value === 'force_on' ? 'force-on' : ''} ${p.value === 'force_off' ? 'force-off' : ''} ${holdState === p.value ? 'active' : ''}"
              data-hold="${p.value}"
              title="${p.label}"
              aria-label="Anwesenheit: ${p.label}"
              aria-pressed="${holdState === p.value}">
              <span class="mdi-icon">${p.icon}</span>
              <span>${p.label}</span>
            </button>
          `).join('')}
        </div>
      </div>`;
  }

  _callPresenceHoldService(zoneId, hold) {
    if (!this._hass) return;
    
    // Set syncing state on the pill
    this._setHoldSyncState(zoneId, 'syncing');
    
    // Use copilot_ha REST command if available, otherwise dispatch event for companion handler
    try {
      this._hass.callService('rest_command', 'zone_presence_hold', {
        entity_id: `zone.${zoneId}`,
        hold,
      });
      // Poll for confirmation after 500ms and timeout after 5s
      this._pollHoldSyncStatus(zoneId, hold, Date.now());
    } catch (_) {
      // Fallback: dispatch DOM event for external handler (companion app / automation)
      this.dispatchEvent(new CustomEvent('presence-hold', {
        detail: { zoneId, hold },
        bubbles: true,
        composed: true,
      }));
      this._setHoldSyncState(zoneId, 'pending');
    }
  }
  
  _setHoldSyncState(zoneId, state) {
    // state: 'syncing' | 'synced' | 'failed' | 'pending'
    const card = this.shadowRoot?.querySelector(`.zone-card[data-zone="${zoneId}"]`);
    if (!card) return;
    
    const holdContainer = card.querySelector('.zone-card-hold');
    if (!holdContainer) return;
    
    // Remove previous sync states
    holdContainer.classList.remove('syncing', 'synced', 'failed');
    
    if (state === 'syncing') {
      holdContainer.classList.add('syncing');
      holdContainer.setAttribute('data-sync-status', 'syncing');
    } else if (state === 'failed') {
      holdContainer.classList.add('failed');
      holdContainer.setAttribute('data-sync-status', 'failed');
    } else {
      holdContainer.removeAttribute('data-sync-status');
    }
  }
  
  _pollHoldSyncStatus(zoneId, expectedHold, startTime) {
    const TIMEOUT_MS = 5000;
    const POLL_INTERVAL_MS = 500;
    
    const check = () => {
      const elapsed = Date.now() - startTime;
      
      if (elapsed > TIMEOUT_MS) {
        // Timeout → mark failed
        this._setHoldSyncState(zoneId, 'failed');
        return;
      }
      
      // Check if zone data reflects the expected hold state
      const { zones } = this._getZonesData();
      const zone = zones.find(z => (z.zone_id || z.name?.toLowerCase().replace(/\s+/g, '_')) === zoneId);
      
      if (zone && zone.presence_hold === expectedHold) {
        // Sync confirmed
        this._setHoldSyncState(zoneId, 'synced');
        // Clear synced indicator after 2s
        setTimeout(() => this._setHoldSyncState(zoneId, 'idle'), 2000);
        return;
      }
      
      // Continue polling
      setTimeout(check, POLL_INTERVAL_MS);
    };
    
    // Start first check after a short delay
    setTimeout(check, POLL_INTERVAL_MS);
  }

  _getModuleStates(zoneId) {
    // Read zone_modules from the sensor entity configured in Lovelace YAML
    // (sensor.copilot_ha_habitus_zones — set as `entity` in YAML config)
    const configEntity = this._hass?.states[this._config.entity];
    if (!configEntity) return [];

    const attrs = configEntity.attributes || {};
    // Try zone-specific module states with various key formats
    const zm = attrs.zone_modules;
    if (zm && typeof zm === 'object') {
      const zoneModules = zm[zoneId] || zm[`zone:${zoneId}`]
        || (zoneId.startsWith('zone:') ? zm[zoneId.slice(5)] : null);
      if (zoneModules && typeof zoneModules === 'object') {
        return Object.entries(zoneModules).map(([name, state]) => ({
          name,
          state: typeof state === 'string' ? state : (state?.state || 'off'),
        }));
      }
    }

    // Try modules attribute with zone keys
    const modules = attrs.modules;
    if (modules && typeof modules === 'object') {
      const zoneModules = modules[zoneId] || modules[`zone:${zoneId}`]
        || (zoneId.startsWith('zone:') ? modules[zoneId.slice(5)] : null);
      if (zoneModules && typeof zoneModules === 'object') {
        return Object.entries(zoneModules).map(([name, state]) => ({
          name,
          state: typeof state === 'string' ? state : (state?.state || 'off'),
        }));
      }
    }

    // Fallback: global modules (same for all zones)
    if (modules && typeof modules === 'object' && !Array.isArray(modules)) {
      // Only use if it's a flat module->state map (not zone-keyed)
      const firstValue = Object.values(modules)[0];
      if (typeof firstValue === 'string') {
        return Object.entries(modules).map(([name, state]) => ({ name, state }));
      }
    }

    return [];
  }

  _getModuleChipColor(state) {
    switch (state) {
      case 'active': return 'var(--ps-green, #22c55e)';
      case 'learning': return 'var(--ps-orange, #f59e0b)';
      default: return '#6b7280';
    }
  }

  _getAutonomyActions(zoneId) {
    const historyEntity = this._hass?.states['sensor.pilotsuite_autonomie_verlauf'];
    if (!historyEntity) return [];

    const actions = historyEntity.attributes?.recent_actions;
    if (!Array.isArray(actions)) return [];

    // Filter for this zone only — exclude global actions (they belong in the dashboard header, not per-zone cards)
    const zoneActions = actions
      .filter(a => a.zone === zoneId || a.zone_id === zoneId)
      .slice(0, 3);

    return zoneActions;
  }

  _formatActionTime(timestamp) {
    if (!timestamp) return '';
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      if (diffMins < 1) return 'gerade eben';
      if (diffMins < 60) return `vor ${diffMins}m`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `vor ${diffHours}h`;
      return `vor ${Math.floor(diffHours / 24)}d`;
    } catch {
      return '';
    }
  }

  _buildMissingTileValue(label, subtitle = '') {
    const esc = typeof window.styxEsc === 'function' ? window.styxEsc : s => s;
    const subtitleHtml = subtitle ? `<div class="value-subtitle">${esc(subtitle)}</div>` : '';
    return `
      <div class="missing-value">
        <div class="value-na">n/a</div>
        <div class="value-title">${esc(label)}</div>
        ${subtitleHtml}
      </div>`;
  }

  _buildMoodGauge(mood) {
    if (!mood?.available) {
      return `<div class="mood-gauge mood-gauge-missing">${this._buildMissingTileValue(mood?.label || 'n/a')}</div>`;
    }

    return this._buildGaugeSvg(mood.value, mood.start, mood.end, mood.label);
  }

  _buildPartialBadges(moodData, neuronActivity, trackNeuron = true) {
    const missing = [];

    const missingMoods = (moodData || []).filter(m => m.available === false);
    if (missingMoods.length > 0) {
      missing.push(`Mood: ${missingMoods.map(m => m.label).join(', ')}`);
    }

    if (trackNeuron) {
      if (!neuronActivity || neuronActivity.available === false) {
        missing.push('Neuronen');
      } else if (neuronActivity.scoreMissing) {
        missing.push('Neuronen (Score)');
      }
    }

    return missing.length
      ? `<div class="partial-badges">${missing.map(item => `<span class="partial-badge">${item}</span>`).join('')}</div>`
      : '';
  }

  _buildGaugeSvg(value, startColor, endColor, label, size = 70) {
    const esc = typeof window.styxEsc === 'function' ? window.styxEsc : s => s;
    const cx = size / 2;
    const cy = size / 2;
    const r = size * 0.35;
    const circumference = 2 * Math.PI * r;
    const pct = Math.max(0, Math.min(100, value));
    const offset = circumference - (circumference * pct) / 100;
    const gradId = `zg_${label.toLowerCase()}_${Math.random().toString(36).substr(2, 9)}`;

    return `
      <svg viewBox="0 0 ${size} ${size}" class="mood-gauge"
        role="img" aria-label="${esc(label)} Anzeige: ${Math.round(pct)} Prozent">
        <title>${esc(label)}: ${Math.round(pct)}%</title>
        <defs>
          <linearGradient id="${gradId}" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="${startColor}"/>
            <stop offset="100%" stop-color="${endColor}"/>
          </linearGradient>
        </defs>
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--ps-surface, #1e2a36)" stroke-width="5"/>
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="url(#${gradId})" stroke-width="5"
          stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"
          stroke-linecap="round" transform="rotate(-90 ${cx} ${cy})"
          style="transition: stroke-dashoffset 0.5s ease;"/>
        <text x="${cx}" y="${cy - 2}" text-anchor="middle"
          fill="var(--ps-text, var(--primary-text-color, #e6eef6))" font-size="12" font-weight="600"
          font-family="system-ui,sans-serif">${Math.round(pct)}</text>
        <text x="${cx}" y="${cy + 10}" text-anchor="middle"
          fill="var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8))" font-size="0.75rem"
          font-family="system-ui,sans-serif">${esc(label)}</text>
      </svg>`;
  }

  _buildNeuronBar(activity) {
    if (!activity || activity.available === false) {
      const reason = activity?.missingReason || 'Sensordaten fehlen';
      return `<div class="neuron-bar-container neuron-missing">${this._buildMissingTileValue('Neuronen', reason)}</div>`;
    }

    const { active, total, score, scoreMissing } = activity;
    const pct = total > 0 ? (active / total) * 100 : 0;
    const activeLabel = Number.isFinite(total) ? `${active}/${total} aktiv` : 'n/a';
    const scorePct = Number.isFinite(score) ? Math.max(0, Math.min(100, score * 100)) : null;
    const scoreLabel = scorePct === null ? 'n/a' : `${Math.round(scorePct)}%`;

    return `
      <div class="neuron-bar-container" role="group" aria-label="Neuronenaktivitaet: ${activeLabel}, Score ${scoreLabel}">
        <div class="neuron-bar-label">
          <span class="mdi-icon">🧠</span>
          <span>Neuronen</span>
        </div>
        <div class="neuron-bar-track" role="progressbar" aria-valuenow="${Math.round(pct)}" aria-valuemin="0" aria-valuemax="100" aria-label="Aktive Neuronen: ${activeLabel}">
          <div class="neuron-bar-fill" style="width: ${pct}%"></div>
          ${scoreMissing ? '' : `<div class="neuron-score-marker" style="left: ${scorePct}%"></div>`}
        </div>
        <div class="neuron-bar-stats">
          <span>${activeLabel}</span>
          <span>Score: ${scoreLabel}</span>
        </div>
      </div>
    `;
  }

  _buildHealthBadge(zoneId) {
    const score = this._getHealthScore(zoneId);
    if (score === null) return '';

    const color = this._getHealthColor(score);
    const label = this._getHealthLabel(score);

    return `<span class="health-badge" style="--health-color: ${color}" title="Gesundheit: ${score}% (${label})" aria-label="Zonen-Gesundheit: ${score} Prozent, ${label}">${score}</span>`;
  }

  _buildModuleChips(zoneId) {
    const modules = this._getModuleStates(zoneId);
    if (modules.length === 0) return '';

    const esc = typeof window.styxEsc === 'function' ? window.styxEsc : s => s;
    const chips = modules.map(m => {
      const color = this._getModuleChipColor(m.state);
      return `<span class="module-chip" style="--chip-color: ${color}" title="${esc(m.name)}: ${esc(m.state)}" aria-label="${esc(m.name)} ${esc(m.state)}">
        <span class="module-chip-dot"></span>
        <span class="module-chip-label">${esc(m.name)}</span>
      </span>`;
    }).join('');

    return `<div class="module-chips">${chips}</div>`;
  }

  _buildAutonomyLog(zoneId) {
    const actions = this._getAutonomyActions(zoneId);
    if (actions.length === 0) return '';

    const esc = typeof window.styxEsc === 'function' ? window.styxEsc : s => s;
    const actionItems = actions.map(a => {
      const timeStr = this._formatActionTime(a.timestamp || a.time);
      const desc = a.description || a.action || 'Aktion';
      return `<div class="action-log-item">
        <span class="action-log-desc">${esc(desc)}</span>
        <span class="action-log-time">${esc(timeStr)}</span>
      </div>`;
    }).join('');

    return `
      <details class="autonomy-log">
        <summary class="autonomy-log-header">
          <span class="mdi-icon">🤖</span>
          <span>Autonomie-Log (${actions.length})</span>
        </summary>
        <div class="action-log-items">
          ${actionItems}
        </div>
      </details>`;
  }

  _buildZoneCard(zone) {
    const esc = typeof window.styxEsc === 'function' ? window.styxEsc : s => s;
    const zoneId = zone.zone_id || zone.name?.toLowerCase().replace(/\s+/g, '_') || 'unknown';
    const zoneName = zone.name || zoneId;
    const isActive = zone.mode && zone.mode !== 'inactive';
    const hasMode = Boolean(zone.mode);
    const moodData = this._config.show_mood ? this._getMoodData(zoneId) : [];
    const neuronActivity = this._config.show_neuron_activity ? this._getNeuronActivity(zoneId) : null;
    const partialBadgesHtml = this._buildPartialBadges(moodData, neuronActivity, this._config.show_neuron_activity);
    const hasPartialData = Boolean(partialBadgesHtml);

    const moodGauges = this._config.show_mood
      ? moodData.map(m => this._buildMoodGauge(m)).join('')
      : '';

    const neuronBar = this._config.show_neuron_activity && neuronActivity
      ? this._buildNeuronBar(neuronActivity)
      : '';

    const healthScore = this._getHealthScore(zoneId);
    const healthBadge = this._config.show_health_score
      ? (healthScore !== null
          ? this._buildHealthBadge(zoneId)
          : '<span class="health-badge unavailable" title="Keine Gesundheitsdaten für diese Zone" aria-label="Zone Gesundheit: nicht verfügbar">—</span>')
      : '';
    const moduleChips = this._config.show_module_states ? this._buildModuleChips(zoneId) : '';
    const autonomyLog = this._config.show_autonomy_log ? this._buildAutonomyLog(zoneId) : '';
    const holdState = this._config.show_presence_hold ? this._getPresenceHoldState(zone) : null;
    const holdPills = holdState !== null ? this._buildHoldPills(zoneId, holdState) : '';

    const modeIcon = hasMode ? this._getModeIcon(zone.mode) : 'mdi:home';
    const modeLabel = zone.mode || 'inaktiv';
    const hasNeuronData = this._hasNeuronActivity(zoneId);

    return `
      <div class="zone-card ${isActive ? 'active' : 'inactive'} ${hasPartialData ? 'partial' : ''} ${!hasNeuronData ? 'data-unavailable' : ''}" data-zone="${esc(zoneId)}" role="region" aria-label="Zone ${esc(zoneName)}">
        <div class="zone-header">
          <div class="zone-info">
            <span class="zone-icon mdi-icon">${this._getZoneIcon(zoneId)}</span>
            <span class="zone-name">${esc(zoneName)}</span>
            ${healthBadge}
          </div>
          <div class="zone-status ${isActive ? 'active' : ''} ${hasPartialData ? 'partial' : ''} ${!hasNeuronData ? 'unavailable' : ''}">
            <span class="status-dot"></span>
            <span class="status-text">${!hasNeuronData ? 'Daten fehlen' : (hasPartialData ? 'Teildaten' : (isActive ? 'Aktiv' : 'Inaktiv'))}</span>
          </div>
        </div>

        ${partialBadgesHtml}

        ${isActive ? `
          <div class="zone-mode">
            <span class="mdi-icon">${modeIcon}</span>
            <span class="mode-label">${esc(modeLabel)}</span>
          </div>
        ` : ''}

        ${moduleChips}

        ${moodGauges ? `
          <div class="mood-gauges">
            ${moodGauges}
          </div>
        ` : ''}

        ${neuronBar}

        ${autonomyLog}

        ${holdPills}

        ${this._config.show_quick_actions ? `
          <div class="quick-actions">
            <button class="action-btn light-toggle" data-action="light" title="Licht umschalten" aria-label="Licht umschalten in ${esc(zoneName)}">
              <span class="mdi-icon">💡</span>
            </button>
            <button class="action-btn scene-btn" data-action="scene" title="Szene waehlen" aria-label="Szene waehlen fuer ${esc(zoneName)}">
              <span class="mdi-icon">🎬</span>
            </button>
            <button class="action-btn thermostat-btn" data-action="thermostat" title="Thermostat anpassen" aria-label="Thermostat anpassen in ${esc(zoneName)}">
              <span class="mdi-icon">🌡️</span>
            </button>
          </div>
        ` : ''}
      </div>
    `;
  }

  _render() {
    const { zones, total_zones, active_zones } = this._getZonesData();
    const title = this._config.title || 'Zonen';

    const zoneCards = zones.length > 0
      ? zones.map(z => this._buildZoneCard(z)).join('')
      : '<div class="no-zones">Keine Zonen konfiguriert</div>';

    const esc = typeof window.styxEsc === 'function' ? window.styxEsc : s => s;

    this.shadowRoot.innerHTML = `
      <style>
        ${typeof this._designTokens === 'function' ? this._designTokens() : ''}
        :host { display: block; }
        .card {
          background: var(--ps-bg, var(--card-background-color, #0a0e14));
          border-radius: var(--ps-radius, var(--ha-card-border-radius, 12px));
          padding: 16px;
          color: var(--ps-text, var(--primary-text-color, #e6eef6));
          font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid var(--ps-border, #263343);
        }
        .title {
          font-size: 18px;
          font-weight: 600;
        }
        .zone-count {
          font-size: 12px;
          color: var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8));
        }
        .zone-count .active {
          color: var(--ps-green, #22c55e);
          font-weight: 600;
        }
        .zones-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 12px;
        }
        .zone-card {
          background: var(--ps-surface, #0f1419);
          border-radius: var(--ps-radius-sm, 10px);
          padding: 14px;
          border: 1px solid var(--ps-border, #1e2a36);
          transition: all 0.2s ease;
        }
        .zone-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        .zone-card.active {
          border-left: 3px solid var(--ps-green, #22c55e);
        }
        .zone-card.inactive {
          border-left: 3px solid #4b5563;
          opacity: 0.7;
        }
        .zone-card.partial {
          border-left: 3px solid var(--ps-orange, #f59e0b);
        }
        .zone-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }
        .zone-info {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .zone-icon {
          font-size: 20px;
        }
        .zone-name {
          font-size: 14px;
          font-weight: 500;
        }
        .zone-status {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.75rem;
          color: var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8));
        }
        .zone-status.active {
          color: var(--ps-green, #22c55e);
        }
        .zone-status.partial {
          color: var(--ps-orange, #f59e0b);
        }
        .zone-status.unavailable {
          color: #d97706;
        }
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #4b5563;
        }
        .zone-status.active .status-dot {
          background: var(--ps-green, #22c55e);
          box-shadow: 0 0 6px var(--ps-green, #22c55e);
        }
        .zone-status.partial .status-dot {
          background: var(--ps-orange, #f59e0b);
          box-shadow: 0 0 6px var(--ps-orange, #f59e0b);
        }
        .zone-status.unavailable .status-dot {
          background: #6b7280;
          box-shadow: none;
        }
        .zone-card.data-unavailable {
          opacity: 0.8;
        }
        .partial-badges {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
          margin-bottom: 10px;
        }
        .partial-badge {
          font-size: 0.75rem;
          color: var(--ps-orange, #f59e0b);
          background: rgba(245, 158, 11, 0.12);
          border: 1px solid rgba(245, 158, 11, 0.4);
          border-radius: 999px;
          width: fit-content;
          padding: 4px 8px;
          text-transform: uppercase;
          letter-spacing: 0.2px;
          line-height: 1.2;
        }
        .zone-mode {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: var(--ps-orange, #fbbf24);
          margin-bottom: 10px;
          padding: 6px 10px;
          background: rgba(251, 191, 36, 0.1);
          border-radius: 6px;
          width: fit-content;
        }
        .mood-gauges {
          display: flex;
          justify-content: space-around;
          margin: 12px 0;
          padding: 10px;
          background: rgba(30, 42, 54, 0.5);
          border-radius: var(--ps-radius-sm, 8px);
        }
        .mood-gauge {
          width: 70px;
          height: 70px;
        }
        .mood-gauge.mood-gauge-missing {
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px dashed rgba(245, 158, 11, 0.35);
          border-radius: 50%;
          background: rgba(30, 42, 54, 0.35);
          color: var(--ps-orange, #f59e0b);
        }
        .missing-value {
          text-align: center;
          line-height: 1.1;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2px;
        }
        .value-na {
          font-size: 18px;
          font-weight: 700;
        }
        .value-title {
          font-size: 0.75rem;
          color: var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8));
          font-weight: 500;
        }
        .value-subtitle {
          font-size: 0.75rem;
          color: var(--ps-orange, #fbbf24);
        }
        .neuron-bar-container.neuron-missing {
          min-height: 42px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(30, 42, 54, 0.5);
          border-radius: 6px;
          padding: 6px 4px;
        }
        .neuron-bar-container {
          margin: 10px 0;
        }
        .neuron-bar-label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.75rem;
          color: var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8));
          margin-bottom: 4px;
        }
        .neuron-bar-track {
          height: 6px;
          background: var(--ps-surface, #1e2a36);
          border-radius: 3px;
          position: relative;
          overflow: hidden;
        }
        .neuron-bar-fill {
          height: 100%;
          background: linear-gradient(90deg, var(--ps-accent, #2196f3), var(--ps-green, #22c55e));
          border-radius: 3px;
          transition: width 0.5s ease;
        }
        .neuron-score-marker {
          position: absolute;
          top: -2px;
          width: 2px;
          height: 10px;
          background: var(--ps-orange, #f59e0b);
          transform: translateX(-50%);
        }
        .neuron-bar-stats {
          display: flex;
          justify-content: space-between;
          font-size: 0.75rem;
          color: var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8));
          margin-top: 4px;
        }
        .quick-actions {
          display: flex;
          gap: 8px;
          margin-top: 12px;
          padding-top: 10px;
          border-top: 1px solid var(--ps-border, #1e2a36);
        }
        .action-btn {
          flex: 1;
          padding: 8px;
          border: none;
          border-radius: 6px;
          background: var(--ps-surface, #1e2a36);
          color: var(--ps-text, #e6eef6);
          cursor: pointer;
          font-size: 16px;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .action-btn:hover {
          background: #2d3a4a;
          transform: scale(1.05);
        }
        .action-btn:active {
          transform: scale(0.95);
        }
        /* v14.2.0: Health Score Badge */
        .health-badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 28px;
          height: 20px;
          padding: 0 5px;
          border-radius: 10px;
          font-size: 11px;
          font-weight: 700;
          color: #fff;
          background: var(--health-color, #6b7280);
          line-height: 1;
          margin-left: 4px;
        }
        .health-badge.unavailable {
          background: #6b7280;
          color: #d1d5db;
          cursor: help;
        }

        /* v14.2.0: Module State Chips */
        .module-chips {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
          margin-bottom: 10px;
        }
        .module-chip {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 3px 8px;
          border-radius: 999px;
          font-size: 11px;
          color: var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8));
          background: rgba(30, 42, 54, 0.6);
          border: 1px solid color-mix(in srgb, var(--chip-color, #6b7280) 40%, transparent);
        }
        .module-chip-dot {
          display: inline-block;
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--chip-color, #6b7280);
          box-shadow: 0 0 4px color-mix(in srgb, var(--chip-color, #6b7280) 60%, transparent);
        }
        .module-chip-label {
          text-transform: capitalize;
        }

        /* v14.2.0: Autonomy Action Mini-Log */
        .autonomy-log {
          margin: 10px 0 0;
          border-radius: 6px;
          overflow: hidden;
        }
        .autonomy-log-header {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8));
          cursor: pointer;
          padding: 6px 8px;
          background: rgba(30, 42, 54, 0.5);
          border-radius: 6px;
          user-select: none;
          list-style: none;
        }
        .autonomy-log-header::-webkit-details-marker {
          display: none;
        }
        .autonomy-log[open] .autonomy-log-header {
          border-radius: 6px 6px 0 0;
        }
        .autonomy-log-header:hover {
          background: rgba(30, 42, 54, 0.8);
        }
        .action-log-items {
          background: rgba(30, 42, 54, 0.3);
          padding: 4px 8px;
          border-radius: 0 0 6px 6px;
        }
        .action-log-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 4px 0;
          font-size: 11px;
          border-bottom: 1px solid rgba(38, 51, 67, 0.5);
        }
        .action-log-item:last-child {
          border-bottom: none;
        }
        .action-log-desc {
          color: var(--ps-text, var(--primary-text-color, #e6eef6));
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          margin-right: 8px;
        }
        .action-log-time {
          color: var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8));
          white-space: nowrap;
          font-size: 10px;
        }

        .no-zones {
          text-align: center;
          padding: 40px;
          color: var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8));
        }
        .mdi-icon {
          font-family: 'Material Design Icons', sans-serif;
          font-style: normal;
        }

        /* v14.8: Presence Hold Control */
        .zone-card-hold {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 0 4px;
          border-top: 1px solid var(--border-color, rgba(255,255,255,0.06));
        }
        .hold-label {
          font-size: 0.75rem;
          color: var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8));
          white-space: nowrap;
        }
        .hold-pills {
          display: flex;
          gap: 4px;
          flex-wrap: wrap;
        }
        .hold-pill {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 3px 8px;
          border-radius: 999px;
          font-size: 11px;
          cursor: pointer;
          border: 1px solid var(--border-color, rgba(255,255,255,0.12));
          background: transparent;
          color: var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8));
          transition: border-color 0.15s, color 0.15s, background 0.15s;
          font-family: inherit;
        }
        .hold-pill:hover {
          border-color: var(--ps-primary, #6366f1);
          color: var(--ps-primary, #6366f1);
        }
        .hold-pill.active {
          background-color: var(--ps-primary, #6366f1);
          border-color: var(--ps-primary, #6366f1);
          color: #fff;
        }
        .hold-pill.force-on.active {
          background-color: #22c55e;
          border-color: #22c55e;
        }
        .hold-pill.force-off.active {
          background-color: #ef4444;
          border-color: #ef4444;
        }
        .hold-pill .mdi {
          font-size: 0.85rem;
        }
        
        /* Sync status indicators for hold pills */
        .zone-card-hold.syncing .hold-pills::after {
          content: "";
          display: inline-block;
          width: 12px;
          height: 12px;
          margin-left: 6px;
          border: 2px solid var(--ps-primary, #6366f1);
          border-top-color: transparent;
          border-radius: 50%;
          animation: hold-spin 1s linear infinite;
        }
        @keyframes hold-spin {
          to { transform: rotate(360deg); }
        }
        .zone-card-hold.failed {
          background: rgba(239, 68, 68, 0.08);
          border-radius: 6px;
        }
        .zone-card-hold.failed .hold-label::after {
          content: " ⚠";
          color: #ef4444;
        }
        .zone-card-hold.synced .hold-pills::after {
          content: "✓";
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 14px;
          height: 14px;
          margin-left: 6px;
          background: #22c55e;
          color: white;
          border-radius: 50%;
          font-size: 8px;
        }
      </style>
      <ha-card>
        <div class="card">
          <div class="header">
            <span class="title">${esc(title)}</span>
            <span class="zone-count">
              <span class="active">${active_zones}</span> / ${total_zones} aktiv
            </span>
          </div>
          <div class="zones-grid">
            ${zoneCards}
          </div>
        </div>
      </ha-card>
    `;

    // Add event listeners for quick actions
    this._setupEventListeners();
  }

  _setupEventListeners() {
    const buttons = this.shadowRoot.querySelectorAll('.action-btn');
    buttons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const action = e.currentTarget.dataset.action;
        const zoneCard = e.currentTarget.closest('.zone-card');
        const zoneId = zoneCard?.dataset.zone;

        if (action === 'light') {
          this._toggleLight(zoneId);
        } else if (action === 'scene') {
          this._showSceneSelector(zoneId);
        } else if (action === 'thermostat') {
          this._adjustThermostat(zoneId);
        }
      });
    });

    // Close other autonomy logs when one opens (accordion behavior)
    const details = this.shadowRoot.querySelectorAll('.autonomy-log');
    details.forEach(d => {
      d.addEventListener('toggle', () => {
        if (d.open) {
          details.forEach(other => { if (other !== d) other.open = false; });
        }
      });
    });

    // Presence hold pills
    const holdPills = this.shadowRoot.querySelectorAll('.hold-pill');
    holdPills.forEach(pill => {
      pill.addEventListener('click', (e) => {
        const hold = e.currentTarget.dataset.hold;
        const zoneCard = e.currentTarget.closest('.zone-card');
        const zoneId = zoneCard?.dataset.zone;
        if (hold && zoneId) {
          // Optimistic UI — update active state immediately
          e.currentTarget.closest('.hold-pills')
            .querySelectorAll('.hold-pill')
            .forEach(p => p.classList.toggle('active', p.dataset.hold === hold));
          this._callPresenceHoldService(zoneId, hold);
        }
      });
    });
  }

  _toggleLight(zoneId) {
    if (!this._hass || !zoneId) return;

    const lightEntity = `light.${zoneId}_main`;
    const state = this._hass.states[lightEntity];
    const newState = state?.state === 'on' ? 'off' : 'on';

    this._hass.callService('light', 'toggle', {
      entity_id: lightEntity
    });
  }

  _showSceneSelector(zoneId) {
    // Dispatch event to show scene selector (can be handled by companion popup)
    this.dispatchEvent(new CustomEvent('scene-select', {
      detail: { zoneId },
      bubbles: true,
      composed: true
    }));
  }

  _adjustThermostat(zoneId) {
    if (!this._hass || !zoneId) return;

    const thermostatEntity = `climate.${zoneId}`;
    this._hass.callService('climate', 'set_temperature', {
      entity_id: thermostatEntity,
      temperature: 21
    });
  }
}

if (typeof registerStyxCard === 'function') {
  registerStyxCard('styx-zone-card', StyxZoneCard, {
    name: 'PilotSuite Zonen-Dashboard',
    description: 'Zonen-Status mit Health Score, Module States, Mood Gauges, Neuronenaktivitaet, Autonomie-Log und Schnellaktionen.',
  });
} else {
  customElements.define('styx-zone-card', StyxZoneCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: 'styx-zone-card',
    name: 'PilotSuite Zonen-Dashboard',
    description: 'Zonen-Status mit Health Score, Module States, Mood Gauges, Neuronenaktivitaet, Autonomie-Log und Schnellaktionen.',
    preview: true,
  });
}
