/**
 * PS-198/200: Habitus Brain-View Card
 *
 * Card for Brain-View visualization in PilotSuite with:
 * - Zone-Aggregation: Globaler Systemzustand über alle Zonen
 * - Module-Status: Aktive Module je Zone (Licht, Musik, Klima, Cover, Energie, Szene, Sicherheit)
 * - Mood-Panels: Emotionales Zustandsmonitoring (Valenz, Aktivierung, Stabilität)
 * - Real-Time-Aggregation: Echtzeit-Datenströme mit Confidence-Indikatoren
 *
 * Design-Referenz: ux_design_system.md (Section 2: Brain-View, Section 4: Mood-Panels)
 * Schema-Referenz: card-form-helper.ts (PS-198) + editor-schema-validation.ts (PS-200)
 */

import {
  buildHaFormSchema,
  HaFormSchema,
  HaFormFieldDescriptor,
} from '../utils/card-form-helper.js';
import { buildConfigValidator } from '../utils/editor-schema-validation.js';
import { registerCustomCard } from '../utils/card-registration.js';

/**
 * Mood-Dimensions for 3D-Mood-Raster
 * @see ux_design_system.md Section 4
 */
export type MoodValence = 'positive' | 'neutral' | 'negative';
export type MoodActivation = 'calm' | 'moderate' | 'charged';
export type MoodStability = 'stable' | 'shifting' | 'volatile';

/**
 * Aggregation-Interval for real-time updates
 * @see ux_design_system.md Section 5
 */
export type AggregationWindow = '5s' | '30s' | '5m';

/**
 * Brain-View Display Mode
 * @see ux_design_system.md Section 2
 */
export type BrainViewMode = 'live' | 'trend' | 'drift';

export interface HabitusBrainCardConfig extends Record<string, unknown> {
  // === Header / Identity ===
  title: string;
  subtitle?: string;

  // === Zone Aggregation ===
  /** Show aggregated zone states */
  show_zone_aggregation: boolean;
  /** Zones to include (empty = all) */
  zones?: string[];
  /** Aggregation interval */
  aggregation_window: AggregationWindow;
  /** Show stale indicator when data is old */
  show_stale_indicator: boolean;
  /** Max age in seconds before showing stale state */
  stale_threshold_seconds: number;

  // === Module Status ===
  /** Show module status chips */
  show_module_status: boolean;
  /** Module types to monitor */
  monitored_modules: MonitoredModule[];
  /** Show module health/consistency score */
  show_module_health: boolean;
  /** Show confidence score per module */
  show_module_confidence: boolean;

  // === Mood Panels ===
  /** Enable mood panel */
  enable_mood_panel: boolean;
  /** Mood panel position: top | bottom | sidebar */
  mood_panel_position: 'top' | 'bottom' | 'sidebar';
  /** Show global mood valence */
  show_mood_valence: boolean;
  /** Show mood activation level */
  show_mood_activation: boolean;
  /** Show mood stability indicator */
  show_mood_stability: boolean;
  /** Show mood historical trend */
  show_mood_history: boolean;
  /** Show mood factors (top contributors) */
  show_mood_factors: boolean;
  /** Mood history duration in hours */
  mood_history_hours: number;

  // === Brain-View Display ===
  /** Brain-View rendering mode */
  view_mode: BrainViewMode;
  /** Show prediction overlays */
  show_predictions: boolean;
  /** Show causal breadcrumbs (explainability) */
  show_causal_breadcrumbs: boolean;
  /** Enable incident lens mode */
  incident_lens_mode: boolean;

  // === Real-Time Aggregation ===
  /** Show data freshness indicator */
  show_data_freshness: boolean;
  /** Show uncertainty fog for low confidence */
  show_uncertainty_fog: boolean;
  /** Batch render updates */
  batch_updates: boolean;
  /** Show zone-match heat layer */
  show_zone_match: boolean;

  // === Layout ===
  /** Compact card layout */
  compact_mode: boolean;
  /** Show action shortcuts */
  show_actions: boolean;
}

export type MonitoredModule =
  | 'light'
  | 'music'
  | 'climate'
  | 'cover'
  | 'energy'
  | 'scene'
  | 'security';

const BRAIN_CARD_FIELDS: HaFormFieldDescriptor[] = [
  // --- Header ---
  {
    name: 'title',
    type: 'text',
    title: 'Titel',
    description: 'Titel der Brain-View Karte',
    required: true,
    defaultValue: 'Brain View',
  },
  {
    name: 'subtitle',
    type: 'text',
    title: 'Untertitel',
    description: 'Optionaler Untertitel',
    required: false,
  },

  // --- Zone Aggregation ---
  {
    name: 'show_zone_aggregation',
    type: 'boolean',
    title: 'Zone-Aggregation anzeigen',
    description: 'Aggregierte Zone-Zustände im Header zeigen',
    required: false,
    defaultValue: true,
  },
  {
    name: 'zones',
    type: 'text',
    title: 'Zonen-Filter',
    description: 'Zu überwachende Zonen (Mehrfachfeld, leer = alle)',
    required: false,
    multiple: true,
  },
  {
    name: 'aggregation_window',
    type: 'text',
    title: 'Aggregations-Intervall',
    description: 'Update-Fenster: 5s | 30s | 5m',
    required: false,
    defaultValue: '30s',
  },
  {
    name: 'show_stale_indicator',
    type: 'boolean',
    title: 'Stale-Indikator',
    description: 'Zeige Warnung bei veralteten Daten',
    required: false,
    defaultValue: true,
  },
  {
    name: 'stale_threshold_seconds',
    type: 'number',
    title: 'Stale-Schwelle (Sekunden)',
    description: 'Ab wann gelten Daten als veraltet',
    required: false,
    defaultValue: 60,
    min: 0,
    step: 1,
  },

  // --- Module Status ---
  {
    name: 'show_module_status',
    type: 'boolean',
    title: 'Modul-Status anzeigen',
    description: 'Aktive Module als Status-Chips zeigen',
    required: false,
    defaultValue: true,
  },
  {
    name: 'monitored_modules',
    type: 'attribute',
    title: 'Monitorierte Module',
    description: 'Light, Musik, Klima, Cover, Energie, Szene, Sicherheit',
    required: false,
    defaultValue: ['light', 'climate', 'music', 'security'],
    multiple: true,
  },
  {
    name: 'show_module_health',
    type: 'boolean',
    title: 'Modul-Gesundheit',
    description: 'Konsistenz-Score pro Modul anzeigen',
    required: false,
    defaultValue: true,
  },
  {
    name: 'show_module_confidence',
    type: 'boolean',
    title: 'Modul-Konfidenz',
    description: 'Konfidenz-Score pro Modul anzeigen',
    required: false,
    defaultValue: true,
  },

  // --- Mood Panels ---
  {
    name: 'enable_mood_panel',
    type: 'boolean',
    title: 'Mood-Panel aktivieren',
    description: 'Emotionales Zustandsmonitoring aktivieren',
    required: false,
    defaultValue: true,
  },
  {
    name: 'mood_panel_position',
    type: 'text',
    title: 'Mood-Panel Position',
    description: 'top | bottom | sidebar',
    required: false,
    defaultValue: 'top',
  },
  {
    name: 'show_mood_valence',
    type: 'boolean',
    title: 'Mood-Valenz',
    description: 'Positiv / Neutral / Negativ anzeigen',
    required: false,
    defaultValue: true,
  },
  {
    name: 'show_mood_activation',
    type: 'boolean',
    title: 'Mood-Aktivierung',
    description: 'Ruhig / Moderat / Geladen anzeigen',
    required: false,
    defaultValue: true,
  },
  {
    name: 'show_mood_stability',
    type: 'boolean',
    title: 'Mood-Stabilität',
    description: 'Stabil / Wechselnd / Instabil anzeigen',
    required: false,
    defaultValue: true,
  },
  {
    name: 'show_mood_history',
    type: 'boolean',
    title: 'Mood-Historie',
    description: 'Verlauf der letzten N Stunden zeigen',
    required: false,
    defaultValue: true,
  },
  {
    name: 'show_mood_factors',
    type: 'boolean',
    title: 'Mood-Faktoren',
    description: 'Top-Contributor zum aktuellen Mood anzeigen',
    required: false,
    defaultValue: true,
  },
  {
    name: 'mood_history_hours',
    type: 'number',
    title: 'Mood-Historie (Stunden)',
    description: 'Wie viele Stunden zurückschauen',
    required: false,
    defaultValue: 24,
    min: 1,
    step: 1,
  },

  // --- Brain-View Display ---
  {
    name: 'view_mode',
    type: 'text',
    title: 'Ansichtsmodus',
    description: 'live | trend | drift',
    required: false,
    defaultValue: 'live',
  },
  {
    name: 'show_predictions',
    type: 'boolean',
    title: 'Vorhersagen',
    description: 'Prädiktions-Overlays auf Knoten anzeigen',
    required: false,
    defaultValue: false,
  },
  {
    name: 'show_causal_breadcrumbs',
    type: 'boolean',
    title: 'Kausale Breadcrumbs',
    description: 'Explainability-Pfad anzeigen (Auslöser → Wirkung → Ergebnis)',
    required: false,
    defaultValue: true,
  },
  {
    name: 'incident_lens_mode',
    type: 'boolean',
    title: 'Incident-Lens Modus',
    description: 'Fokusmodus bei Alarmzuständen (reduzierte visuelle Last)',
    required: false,
    defaultValue: false,
  },

  // --- Real-Time Aggregation ---
  {
    name: 'show_data_freshness',
    type: 'boolean',
    title: 'Daten-Frische',
    description: 'Zeitstempel und Freshness-Indikator anzeigen',
    required: false,
    defaultValue: true,
  },
  {
    name: 'show_uncertainty_fog',
    type: 'boolean',
    title: 'Unsicherheits-Nebel',
    description: 'Visuell unscharf bei niedriger Konfidenz',
    required: false,
    defaultValue: true,
  },
  {
    name: 'batch_updates',
    type: 'boolean',
    title: 'Batch-Updates',
    description: 'Updates bündeln statt einzeln rendern',
    required: false,
    defaultValue: true,
  },
  {
    name: 'show_zone_match',
    type: 'boolean',
    title: 'Zone-Match',
    description: 'Heat-Layer: passt aktueller Zustand zu gewohnten Mustern?',
    required: false,
    defaultValue: false,
  },

  // --- Layout ---
  {
    name: 'compact_mode',
    type: 'boolean',
    title: 'Kompakt-Modus',
    description: 'Reduzierte Darstellung',
    required: false,
    defaultValue: false,
  },
  {
    name: 'show_actions',
    type: 'boolean',
    title: 'Aktionen anzeigen',
    description: 'Quick-Action Buttons anzeigen',
    required: false,
    defaultValue: true,
  },
];

const BRAIN_CARD_SCHEMA: HaFormSchema[] = buildHaFormSchema(BRAIN_CARD_FIELDS, {
  gridName: 'brain',
  gridTitle: 'Brain View',
  gridDescription:
    'Interaktiver Wissensraum mit Zone-Aggregation, Module-Status und Mood-Panels',
  flatten: true,
});

const validateHabitusBrainCardConfig: (config: unknown) => asserts config is HabitusBrainCardConfig =
  buildConfigValidator<HabitusBrainCardConfig>(BRAIN_CARD_SCHEMA);

export class HabitusBrainCard extends HTMLElement {
  static get type(): string {
    return 'habitus-brain';
  }

  static get documentationURL(): string {
    return 'https://pilotsuite.io/docs/cards/brain-view';
  }

  static async getConfigForm(): Promise<HaFormSchema[]> {
    return BRAIN_CARD_SCHEMA;
  }

  static getStubConfig(): Partial<HabitusBrainCardConfig> {
    return {
      title: 'Brain View',
      subtitle: 'System-Übersicht',
      show_zone_aggregation: true,
      aggregation_window: '30s',
      show_stale_indicator: true,
      stale_threshold_seconds: 60,
      show_module_status: true,
      monitored_modules: ['light', 'climate', 'music', 'security'],
      show_module_health: true,
      show_module_confidence: true,
      enable_mood_panel: true,
      mood_panel_position: 'top',
      show_mood_valence: true,
      show_mood_activation: true,
      show_mood_stability: true,
      show_mood_history: true,
      show_mood_factors: true,
      mood_history_hours: 24,
      view_mode: 'live',
      show_predictions: false,
      show_causal_breadcrumbs: true,
      incident_lens_mode: false,
      show_data_freshness: true,
      show_uncertainty_fog: true,
      batch_updates: true,
      show_zone_match: false,
      compact_mode: false,
      show_actions: true,
    };
  }

  static validateConfig(config: unknown): void {
    validateHabitusBrainCardConfig(config as Record<string, unknown>);
  }
}

// Register card with Home Assistant
registerCustomCard({
  type: HabitusBrainCard.type,
  name: 'Habitus Brain View',
  description:
    'Interaktiver Wissensraum mit Zone-Aggregation, Module-Status und Mood-Panels',
  documentationURL: HabitusBrainCard.documentationURL,
  preview: true,
  default: HabitusBrainCard.getStubConfig(),
});
