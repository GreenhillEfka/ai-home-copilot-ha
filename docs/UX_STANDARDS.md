# PilotSuite UX Standards

> State of the Art + Beyond — Verbindliche Gestaltungsrichtlinien fuer alle PilotSuite Frontend-Komponenten.

---

## Inhaltsverzeichnis

1. [Design-Philosophie](#design-philosophie)
2. [Micro-Interactions](#micro-interactions)
3. [Animationen](#animationen)
4. [Loading-States](#loading-states)
5. [Error-States](#error-states)
6. [Accessibility (WCAG 2.1 AA)](#accessibility)
7. [Responsive Design](#responsive-design)
8. [Dark / Light Mode](#dark--light-mode)
9. [Eye-Candies](#eye-candies)
10. [Design Tokens](#design-tokens)
11. [Checkliste fuer Entwickler](#checkliste-fuer-entwickler)

---

## Design-Philosophie

| Prinzip | Beschreibung |
|---------|-------------|
| **Calm Technology** | Das Interface tritt zurueck und informiert nur, wenn noetig. Kein visuelles Rauschen. |
| **Progressive Disclosure** | Komplexitaet wird schrittweise enthuellt — Basisansicht simpel, Details on-demand. |
| **Ambient Awareness** | Systemzustand (Mood, Energy, Presence) wird subtil kommuniziert, nie aufdringlich. |
| **Trust through Transparency** | Jede KI-Empfehlung zeigt ihren Grund. Governance-first: Vorschlaege, keine stillen Aktionen. |
| **Delight without Distraction** | Eye-Candies ergaenzen die Funktion, ersetzen sie nie. Performance > Aesthetik. |

---

## Micro-Interactions

Micro-Interactions geben sofortiges Feedback auf Nutzerhandlungen. Jedes interaktive Element MUSS die folgenden Zustaende visuell unterscheiden.

### Hover

```css
.ps-interactive {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.ps-interactive:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

/* Cards: subtiler Glow im Brand-Farbton */
.ps-card:hover {
  box-shadow: 0 0 0 1px var(--ps-accent), 0 8px 24px rgba(var(--ps-accent-rgb), 0.12);
}

/* Icon-Buttons: sanfter Hintergrund-Kreis */
.ps-icon-btn:hover {
  background: rgba(var(--ps-accent-rgb), 0.08);
  border-radius: 50%;
}
```

**Regeln:**
- Hover-Effekte innerhalb von **200ms** (max 250ms)
- Keine Layout-Shifts — nur `transform`, `box-shadow`, `opacity`, `background`
- Hover auf Touch-Geraeten deaktivieren (`@media (hover: hover)`)

### Focus

```css
/* Globaler Focus-Ring — NIEMALS entfernen */
.ps-interactive:focus-visible {
  outline: 2px solid var(--ps-focus-ring);
  outline-offset: 2px;
  border-radius: var(--ps-radius-sm);
}

/* Focus innerhalb von Gruppen */
.ps-card:focus-within {
  box-shadow: 0 0 0 2px var(--ps-focus-ring);
}
```

**Regeln:**
- `:focus-visible` verwenden, nicht `:focus` (Maus-Klick braucht keinen Ring)
- Focus-Ring Farbe: `--ps-focus-ring` — High-Contrast gegen beide Themes
- Minimum Kontrast: **3:1** gegen den Hintergrund (WCAG 2.1 AA)
- Tab-Reihenfolge muss logisch sein (DOM-Reihenfolge = visuelle Reihenfolge)

### Active / Pressed

```css
.ps-btn:active {
  transform: scale(0.97);
  transition-duration: 0.1s;
}

/* Toggle-Buttons: Zustandswechsel mit Farbe + Icon */
.ps-toggle[aria-pressed="true"] {
  background: var(--ps-accent);
  color: var(--ps-on-accent);
}

.ps-toggle[aria-pressed="true"] .icon {
  transform: rotate(180deg);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

**Regeln:**
- Active-Feedback innerhalb von **100ms** — fuehlt sich physisch an
- Scale-Down statt Opacity-Reduktion (natuerlicheres Gefuehl)
- Toggle-States muessen durch **Farbe + Icon + ARIA** kommuniziert werden (nie nur Farbe allein)

### Swipe & Drag (Touch)

```css
.ps-swipeable {
  touch-action: pan-x;
  will-change: transform;
}

.ps-dragging {
  opacity: 0.85;
  transform: scale(1.02);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
  cursor: grabbing;
}
```

**Regeln:**
- Drag-Threshold: **8px** bevor Drag startet (verhindert versehentliches Dragging)
- Haptic Feedback auf unterstuetzten Geraeten (`navigator.vibrate(10)`)
- Drop-Zone visuell hervorheben waehrend Drag

---

## Animationen

### Timing-Funktionen

| Name | Easing | Dauer | Verwendung |
|------|--------|-------|------------|
| **Micro** | `cubic-bezier(0.4, 0, 0.2, 1)` | 150–200ms | Hover, Focus, Toggles |
| **Standard** | `cubic-bezier(0.4, 0, 0.2, 1)` | 250–350ms | Panels, Dropdowns, Modals |
| **Emphasis** | `cubic-bezier(0.34, 1.56, 0.64, 1)` | 350–500ms | Notifications, Erfolge |
| **Dramatic** | `cubic-bezier(0.16, 1, 0.3, 1)` | 500–800ms | Page-Transitions, Hero-Elemente |

### Fade-In

```css
@keyframes ps-fade-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ps-fade-in {
  animation: ps-fade-in 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

/* Staggered Fade-In fuer Listen */
.ps-stagger > * {
  animation: ps-fade-in 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
  opacity: 0;
}

.ps-stagger > *:nth-child(1) { animation-delay: 0ms; }
.ps-stagger > *:nth-child(2) { animation-delay: 50ms; }
.ps-stagger > *:nth-child(3) { animation-delay: 100ms; }
.ps-stagger > *:nth-child(4) { animation-delay: 150ms; }
.ps-stagger > *:nth-child(5) { animation-delay: 200ms; }
/* Max 5 Stufen — danach alle gleichzeitig */
.ps-stagger > *:nth-child(n+6) { animation-delay: 200ms; }
```

### Pulse (Aufmerksamkeit)

```css
@keyframes ps-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.85; }
}

/* Notification Badge */
.ps-badge-pulse {
  animation: ps-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Breathing Glow fuer aktive Sensoren */
@keyframes ps-glow-breathe {
  0%, 100% { box-shadow: 0 0 8px rgba(var(--ps-accent-rgb), 0.2); }
  50% { box-shadow: 0 0 20px rgba(var(--ps-accent-rgb), 0.4); }
}

.ps-sensor-active {
  animation: ps-glow-breathe 3s ease-in-out infinite;
}
```

### Transitions (View-Uebergaenge)

```css
/* Panel Slide-In */
@keyframes ps-slide-in-right {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* Modal Entrance */
@keyframes ps-modal-enter {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.ps-modal-enter {
  animation: ps-modal-enter 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

/* Backdrop */
.ps-backdrop {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  transition: opacity 0.3s ease;
}
```

### Regeln fuer Animationen

- **`prefers-reduced-motion: reduce`** — MUSS respektiert werden. Alle Animationen auf sofort (0ms) oder Fade-only reduzieren:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

- Keine Animationen ueber **1s** Dauer (ausser Ambient-Loops wie Breathing)
- GPU-beschleunigte Properties bevorzugen: `transform`, `opacity`, `filter`
- Keine Animation auf `width`, `height`, `top`, `left` (Layout-Thrashing)
- Staggering max **5 Stufen** bei Listen (danach gleichzeitig)

---

## Loading-States

### Skeleton Screens

Skeleton Screens ersetzen Platzhalter-Spinner. Sie zeigen die Form des erwarteten Inhalts.

```css
@keyframes ps-skeleton-shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.ps-skeleton {
  background: linear-gradient(
    90deg,
    var(--ps-skeleton-base) 25%,
    var(--ps-skeleton-highlight) 50%,
    var(--ps-skeleton-base) 75%
  );
  background-size: 200% 100%;
  animation: ps-skeleton-shimmer 1.5s ease-in-out infinite;
  border-radius: var(--ps-radius-sm);
}

/* Varianten */
.ps-skeleton-text { height: 16px; margin-bottom: 8px; }
.ps-skeleton-title { height: 24px; width: 60%; margin-bottom: 12px; }
.ps-skeleton-avatar { width: 40px; height: 40px; border-radius: 50%; }
.ps-skeleton-card { height: 120px; border-radius: var(--ps-radius-md); }
.ps-skeleton-chart { height: 200px; border-radius: var(--ps-radius-md); }
```

**Regeln:**
- Skeleton zeigen, wenn Ladezeit voraussichtlich **> 300ms**
- Unter 300ms: Inhalt direkt anzeigen (kein Flackern)
- Skeleton-Form muss dem tatsaechlichen Content entsprechen
- Mindestens **500ms** Skeleton anzeigen (verhindert Flicker bei schnellen Loads)

### Progress-Indikatoren

```
Ladezeit        | Feedback
< 300ms         | Kein sichtbares Feedback
300ms – 1s      | Inline-Spinner oder Skeleton
1s – 5s         | Skeleton + optionaler Progress-Text
5s – 15s        | Determinate Progress-Bar mit Prozent
> 15s           | Progress-Bar + Abbrechen-Button + geschaetzte Restzeit
```

```css
/* Indeterminate Progress-Bar */
.ps-progress-bar {
  height: 3px;
  background: var(--ps-surface-variant);
  border-radius: 2px;
  overflow: hidden;
}

.ps-progress-bar::after {
  content: '';
  display: block;
  height: 100%;
  width: 40%;
  background: var(--ps-accent);
  border-radius: 2px;
  animation: ps-progress-indeterminate 1.5s ease-in-out infinite;
}

@keyframes ps-progress-indeterminate {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}

/* Determinate Progress-Bar */
.ps-progress-bar[data-progress]::after {
  animation: none;
  width: var(--progress, 0%);
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Optimistic UI

Fuer schnelle Aktionen (Toggles, Favorites, Kandidaten-Voting):

1. **Sofort** den neuen Zustand anzeigen
2. **Im Hintergrund** den API-Call machen
3. **Bei Fehler** den alten Zustand wiederherstellen + Error-Toast anzeigen

```
User klickt Toggle → UI zeigt sofort "An" → API-Call → Erfolg: fertig
                                                      → Fehler: UI zurueck auf "Aus" + Toast
```

---

## Error-States

### Fehler-Hierarchie

| Schweregrad | Darstellung | Dauer | Beispiel |
|------------|-------------|-------|---------|
| **Info** | Toast (blau) | 4s auto-dismiss | "Einstellungen gespeichert" |
| **Warnung** | Toast (gelb) | 6s auto-dismiss | "Verbindung instabil" |
| **Fehler** | Toast (rot) + Retry | Manuell schliessen | "Speichern fehlgeschlagen" |
| **Kritisch** | Banner (rot) | Persistent | "Keine Verbindung zum Server" |
| **Offline** | Overlay mit Status | Persistent | "Offline — letzte Sync vor 5 Min" |

### User-Friendly Messages

**NIEMALS** technische Fehlermeldungen direkt anzeigen. Jeder Fehler braucht:

1. **Was** ist passiert (klare, menschliche Sprache)
2. **Warum** es passiert ist (kurze Ursache, wenn bekannt)
3. **Was der User tun kann** (konkrete Handlungsanweisung)

```
SCHLECHT:  "Error 500: Internal Server Error"
SCHLECHT:  "TypeError: Cannot read property 'name' of undefined"
SCHLECHT:  "Request failed with status code 408"

GUT:       "Verbindung fehlgeschlagen"
           "Der Server antwortet nicht. Pruefe deine Netzwerkverbindung."
           [Erneut versuchen]

GUT:       "Daten konnten nicht geladen werden"
           "Es gab ein Problem beim Abrufen der Sensordaten."
           [Erneut versuchen] [Details anzeigen]
```

### Error-Mapping

```javascript
const ERROR_MESSAGES = {
  // Netzwerk
  'NETWORK_ERROR':      { title: 'Keine Verbindung', body: 'Pruefe deine Netzwerkverbindung.', action: 'retry' },
  'TIMEOUT':            { title: 'Zeitueberschreitung', body: 'Der Server braucht zu lange. Versuche es erneut.', action: 'retry' },
  'OFFLINE':            { title: 'Offline', body: 'Du bist nicht mit dem Netzwerk verbunden.', action: 'none' },

  // Auth
  'TOKEN_EXPIRED':      { title: 'Sitzung abgelaufen', body: 'Bitte melde dich erneut an.', action: 'reauth' },
  'UNAUTHORIZED':       { title: 'Zugriff verweigert', body: 'Du hast keine Berechtigung fuer diese Aktion.', action: 'none' },

  // Daten
  'NOT_FOUND':          { title: 'Nicht gefunden', body: 'Die angeforderten Daten existieren nicht mehr.', action: 'back' },
  'VALIDATION_ERROR':   { title: 'Ungueltige Eingabe', body: null, action: 'fix' },  // body aus Serverantwort
  'CONFLICT':           { title: 'Konflikt', body: 'Die Daten wurden zwischenzeitlich geaendert.', action: 'reload' },

  // Server
  'SERVER_ERROR':       { title: 'Serverfehler', body: 'Es ist ein interner Fehler aufgetreten. Versuche es spaeter erneut.', action: 'retry' },
  'SERVICE_UNAVAILABLE':{ title: 'Service nicht verfuegbar', body: 'Wartungsarbeiten. Bitte warte einen Moment.', action: 'retry' },

  // Fallback
  'UNKNOWN':            { title: 'Unbekannter Fehler', body: 'Etwas ist schiefgelaufen. Versuche es erneut.', action: 'retry' },
};
```

### Toast-Komponente

```css
.ps-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 12px 20px;
  border-radius: var(--ps-radius-md);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  gap: 12px;
  animation: ps-slide-in-up 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 9000;
  max-width: 420px;
}

@keyframes ps-slide-in-up {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Stacking: maximal 3 Toasts sichtbar */
.ps-toast-stack > .ps-toast:nth-child(2) { transform: translateY(-8px) scale(0.98); opacity: 0.9; }
.ps-toast-stack > .ps-toast:nth-child(3) { transform: translateY(-16px) scale(0.96); opacity: 0.8; }
.ps-toast-stack > .ps-toast:nth-child(n+4) { display: none; }
```

### Empty States

Leere Zustaende (keine Daten, erste Nutzung) MUESSEN visuell gestaltet sein:

```
+----------------------------------------------+
|                                              |
|          [Illustration / Icon]               |
|                                              |
|      Noch keine Vorschlaege vorhanden        |
|                                              |
|   PilotSuite lernt deine Gewohnheiten        |
|   und wird bald erste Vorschlaege machen.    |
|                                              |
|          [So funktioniert's]                 |
|                                              |
+----------------------------------------------+
```

**Regeln:**
- Illustration oder thematisches Icon (nie ein leeres weisses Feld)
- Erklaerung, **warum** es leer ist
- Optionaler Call-to-Action oder Erklaerungslink
- Positiver Ton (nicht: "Keine Daten", sondern: "Noch keine Daten — kommt bald!")

---

## Accessibility

### WCAG 2.1 AA Anforderungen (verbindlich)

#### Farbkontrast

| Element | Minimum Kontrast |
|---------|-----------------|
| Normaler Text (< 18px) | **4.5:1** |
| Grosser Text (>= 18px / >= 14px bold) | **3:1** |
| UI-Komponenten & Grafiken | **3:1** |
| Focus-Indikatoren | **3:1** gegen angrenzende Farben |
| Dekorative Elemente | Kein Minimum |

**Werkzeuge:** Kontrast vor jedem Release pruefen mit Chrome DevTools, axe, oder Colour Contrast Analyser.

#### Keyboard-Navigation

```
Tab / Shift+Tab     Naechstes / vorheriges Element
Enter / Space        Aktivieren
Escape               Modal / Dropdown schliessen
Arrow Keys           Navigation in Listen, Tabs, Menues
Home / End           Erstes / letztes Element
```

**Regeln:**
- Jedes interaktive Element MUSS per Tastatur erreichbar sein
- Focus-Reihenfolge folgt der visuellen Lesereihenfolge
- Keine Keyboard-Traps (ausser Modals — Focus bleibt im Modal)
- Skip-Links am Seitenanfang: "Zum Hauptinhalt springen"

#### ARIA

```html
<!-- Korrekte Verwendung -->
<button aria-label="Benachrichtigungen" aria-expanded="false">
  <svg aria-hidden="true">...</svg>
  <span class="ps-badge" aria-label="3 ungelesene">3</span>
</button>

<!-- Live-Regionen fuer dynamische Updates -->
<div aria-live="polite" aria-atomic="true" class="ps-sr-only">
  <!-- Hier werden Status-Updates fuer Screenreader injiziert -->
</div>

<!-- Toasts fuer Screenreader -->
<div role="status" aria-live="assertive" aria-atomic="true">
  Einstellungen erfolgreich gespeichert.
</div>
```

**Regeln:**
- `aria-label` fuer Icon-only Buttons
- `aria-expanded` fuer aufklappbare Elemente
- `aria-live="polite"` fuer nicht-kritische Updates
- `aria-live="assertive"` fuer Fehler und wichtige Status-Aenderungen
- `role="alert"` fuer Fehler-Meldungen
- `aria-hidden="true"` fuer dekorative Icons

#### Screen Reader

```css
/* Visuell versteckter, aber fuer Screenreader lesbarer Text */
.ps-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

#### Weitere Anforderungen

- **Bilder:** Alle informativen Bilder brauchen `alt`-Text
- **Formulare:** Labels fuer alle Inputs, Fehlermeldungen mit `aria-describedby`
- **Zeitlimits:** User muss Session verlaengern koennen
- **Bewegung:** `prefers-reduced-motion` respektieren (siehe Animationen)
- **Zoom:** Bis 200% Zoom darf kein Inhalt abgeschnitten werden oder Funktion verlieren
- **Touch Target:** Mindestens **44x44px** (WCAG 2.5.5)

---

## Responsive Design

### Breakpoints

```css
:root {
  /* Mobile-first Breakpoints */
  --ps-bp-sm: 640px;    /* Smartphone Landscape */
  --ps-bp-md: 768px;    /* Tablet Portrait */
  --ps-bp-lg: 1024px;   /* Tablet Landscape / kleiner Desktop */
  --ps-bp-xl: 1280px;   /* Desktop */
  --ps-bp-2xl: 1536px;  /* Grosser Desktop / TV Dashboard */
}

/* Verwendung */
@media (min-width: 640px)  { /* sm */ }
@media (min-width: 768px)  { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
@media (min-width: 1536px) { /* 2xl - Wand-Dashboard */ }
```

### Layout-Strategie

| Breakpoint | Layout | Navigation | Cards |
|-----------|--------|-----------|-------|
| < 640px | Single Column | Bottom Nav | Full Width |
| 640–767px | Single Column | Bottom Nav | Full Width |
| 768–1023px | 2 Columns | Side Nav (collapsed) | 2 pro Reihe |
| 1024–1279px | 2–3 Columns | Side Nav (expanded) | 3 pro Reihe |
| >= 1280px | 3–4 Columns | Side Nav (expanded) | 4 pro Reihe |
| >= 1536px | Dashboard Grid | Side Nav + Top Bar | Auto-fit |

### Container

```css
.ps-container {
  width: 100%;
  max-width: var(--ps-container-max, 1280px);
  margin-inline: auto;
  padding-inline: var(--ps-spacing-4);
}

@media (min-width: 768px) {
  .ps-container { padding-inline: var(--ps-spacing-6); }
}

@media (min-width: 1280px) {
  .ps-container { padding-inline: var(--ps-spacing-8); }
}
```

### Touch vs. Pointer

```css
/* Groessere Targets auf Touch-Geraeten */
@media (pointer: coarse) {
  .ps-btn { min-height: 48px; min-width: 48px; }
  .ps-list-item { padding-block: 12px; }
  .ps-input { min-height: 48px; font-size: 16px; /* verhindert iOS Zoom */ }
}

/* Feinere Interaktionen fuer Maus */
@media (pointer: fine) {
  .ps-btn { min-height: 36px; }
  .ps-list-item { padding-block: 8px; }
}
```

### Home Assistant Panel

PilotSuite laeuft als Panel in Home Assistant. Spezialbehandlung:

```css
/* HA Panel eingebettet — kein eigener Scrollbar am Body */
:host {
  display: block;
  height: 100%;
  overflow: auto;
}

/* HA Toolbar Hoehe beruecksichtigen */
.ps-main-content {
  padding-top: var(--header-height, 56px);
}
```

---

## Dark / Light Mode

### Strategie

1. **System-Praeferenz** als Default (`prefers-color-scheme`)
2. **User Override** persistent in LocalStorage
3. **Home Assistant Theme** Integration (wenn in HA Panel eingebettet)

```css
/* System-Default */
:root {
  color-scheme: light dark;
}

/* Expliziter Override */
[data-theme="light"] { color-scheme: light; }
[data-theme="dark"]  { color-scheme: dark;  }
```

### Farb-Tokens

```css
/* Light Theme */
:root, [data-theme="light"] {
  --ps-bg:                 #FAFAFA;
  --ps-bg-elevated:        #FFFFFF;
  --ps-surface:            #FFFFFF;
  --ps-surface-variant:    #F1F3F5;
  --ps-border:             #E0E3E8;
  --ps-border-subtle:      #ECEEF1;

  --ps-text-primary:       #1A1D23;
  --ps-text-secondary:     #5F6672;
  --ps-text-tertiary:      #8B919D;
  --ps-text-disabled:      #B0B5BF;

  --ps-accent:             #3B82F6;
  --ps-accent-hover:       #2563EB;
  --ps-accent-rgb:         59, 130, 246;
  --ps-on-accent:          #FFFFFF;

  --ps-success:            #22C55E;
  --ps-warning:            #F59E0B;
  --ps-error:              #EF4444;
  --ps-info:               #3B82F6;

  --ps-skeleton-base:      #E0E3E8;
  --ps-skeleton-highlight: #F1F3F5;

  --ps-focus-ring:         #3B82F6;
  --ps-shadow-sm:          0 1px 2px rgba(0, 0, 0, 0.05);
  --ps-shadow-md:          0 4px 12px rgba(0, 0, 0, 0.08);
  --ps-shadow-lg:          0 12px 32px rgba(0, 0, 0, 0.1);
}

/* Dark Theme */
[data-theme="dark"],
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ps-bg:                 #0F1117;
    --ps-bg-elevated:        #1A1D26;
    --ps-surface:            #1E2028;
    --ps-surface-variant:    #262930;
    --ps-border:             #2E3138;
    --ps-border-subtle:      #242730;

    --ps-text-primary:       #E8EAF0;
    --ps-text-secondary:     #A0A5B2;
    --ps-text-tertiary:      #6B7180;
    --ps-text-disabled:      #4A4F5C;

    --ps-accent:             #60A5FA;
    --ps-accent-hover:       #93C5FD;
    --ps-accent-rgb:         96, 165, 250;
    --ps-on-accent:          #0F1117;

    --ps-success:            #4ADE80;
    --ps-warning:            #FBBF24;
    --ps-error:              #F87171;
    --ps-info:               #60A5FA;

    --ps-skeleton-base:      #262930;
    --ps-skeleton-highlight: #2E3138;

    --ps-focus-ring:         #60A5FA;
    --ps-shadow-sm:          0 1px 2px rgba(0, 0, 0, 0.2);
    --ps-shadow-md:          0 4px 12px rgba(0, 0, 0, 0.3);
    --ps-shadow-lg:          0 12px 32px rgba(0, 0, 0, 0.4);
  }
}
```

### Regeln fuer Themes

- **Keine hart-codierten Farben** — immer `var(--ps-...)` verwenden
- Bilder und Icons: `filter: brightness(0.9)` im Dark Mode oder SVG mit `currentColor`
- Schatten im Dark Mode subtiler (hoehere Opacity, weniger Spread)
- Kontrast-Checks fuer **beide** Themes durchfuehren
- Uebergang zwischen Themes: `transition: background-color 0.3s, color 0.3s` auf `body`

---

## Eye-Candies

Eye-Candies machen PilotSuite zu einem visuellen Erlebnis. Sie sind **optional** und duerfen die Performance nie beeintraechtigen.

### Gradients

```css
/* Ambient Gradient — spiegelt Mood Engine wider */
.ps-mood-gradient {
  background: linear-gradient(
    135deg,
    rgba(var(--ps-mood-comfort-rgb), 0.15),
    rgba(var(--ps-mood-joy-rgb), 0.10),
    rgba(var(--ps-mood-frugality-rgb), 0.08)
  );
}

/* Glassmorphism Cards */
.ps-glass {
  background: rgba(var(--ps-surface-rgb), 0.6);
  backdrop-filter: blur(16px) saturate(1.2);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--ps-radius-lg);
}

/* Mesh Gradient (Hero / Dashboard Header) */
.ps-mesh-gradient {
  background:
    radial-gradient(ellipse at 20% 50%, rgba(var(--ps-accent-rgb), 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(var(--ps-success-rgb), 0.10) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, rgba(var(--ps-warning-rgb), 0.08) 0%, transparent 50%);
}
```

### Particle-Effects

Subtile Partikel fuer besondere Momente (Onboarding, Achievements, Meilensteine):

```javascript
/**
 * Leichtgewichtiger Partikel-Emitter fuer Canvas
 * Nur bei sichtbarer Viewport-Area und keiner Motion-Praeferenz aktivieren
 */
class PilotParticles {
  static MAX_PARTICLES = 30;        // Performance-Limit
  static PARTICLE_LIFETIME = 3000;  // ms

  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.particles = [];
    this.active = false;
  }

  shouldAnimate() {
    return !window.matchMedia('(prefers-reduced-motion: reduce)').matches
        && document.visibilityState === 'visible';
  }

  emit(x, y, count = 10) {
    if (!this.shouldAnimate()) return;
    // ... Partikel erzeugen (max MAX_PARTICLES)
  }
}
```

**Verwendung:**
- Erfolgreiche Kandidaten-Akzeptanz → Konfetti (kurz, 1.5s)
- Onboarding abgeschlossen → sanfter Sternstaub
- Energie-Sparziel erreicht → gruene Partikel aufsteigend

**Regeln:**
- Max **30 Partikel** gleichzeitig
- Nur auf Canvas (kein DOM-Partikel-Spam)
- `prefers-reduced-motion` respektieren — Partikel komplett deaktivieren
- `document.visibilityState` pruefen — unsichtbare Tabs keine Partikel
- Auf Mobile deaktivieren wenn Battery < 20% (`navigator.getBattery()`)

### 3D-Effekte

```css
/* Subtle Tilt auf Cards (nur Maus) */
@media (pointer: fine) and (hover: hover) {
  .ps-card-3d {
    transform-style: preserve-3d;
    perspective: 1000px;
    transition: transform 0.2s ease;
  }

  .ps-card-3d:hover {
    /* JavaScript setzt --rx und --ry basierend auf Mausposition */
    transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  }
}

/* Tiefeneffekt fuer Mood-Visualisierung */
.ps-mood-orb {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: radial-gradient(
    circle at 35% 35%,
    rgba(var(--ps-mood-joy-rgb), 0.6),
    rgba(var(--ps-mood-comfort-rgb), 0.4) 50%,
    rgba(var(--ps-mood-frugality-rgb), 0.2)
  );
  box-shadow:
    inset -8px -8px 24px rgba(0, 0, 0, 0.15),
    0 0 40px rgba(var(--ps-accent-rgb), 0.2);
  animation: ps-orb-float 6s ease-in-out infinite;
}

@keyframes ps-orb-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
```

### Ambient Data Visualization

```css
/* Energy Flow — animierte Linien auf dem Dashboard */
.ps-energy-flow {
  stroke: var(--ps-success);
  stroke-width: 2;
  stroke-dasharray: 8 4;
  animation: ps-flow 1s linear infinite;
}

@keyframes ps-flow {
  to { stroke-dashoffset: -12; }
}

/* Neuron Activity Ring */
.ps-neuron-ring {
  fill: none;
  stroke: var(--ps-accent);
  stroke-width: 3;
  stroke-dasharray: calc(var(--score, 0) * 283) 283; /* 283 = 2*PI*45 */
  stroke-linecap: round;
  transform: rotate(-90deg);
  transform-origin: center;
  transition: stroke-dasharray 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Regeln fuer Eye-Candies

| Regel | Beschreibung |
|-------|-------------|
| **Performance-Budget** | Eye-Candies duerfen max **5ms/Frame** JS + max **2 Compositor-Layers** kosten |
| **Progressive Enhancement** | Ohne Eye-Candies muss alles funktionieren — sie sind optional |
| **Battery-Aware** | Auf Low-Battery oder `prefers-reduced-motion` deaktivieren |
| **Nicht auf Critical Path** | Lazy-load alle Eye-Candy-Assets |
| **Max 1 Hero-Animation** | Pro Seite nur ein aufwendiges visuelles Element |

---

## Design Tokens

### Spacing

```css
:root {
  --ps-spacing-1: 4px;
  --ps-spacing-2: 8px;
  --ps-spacing-3: 12px;
  --ps-spacing-4: 16px;
  --ps-spacing-5: 20px;
  --ps-spacing-6: 24px;
  --ps-spacing-8: 32px;
  --ps-spacing-10: 40px;
  --ps-spacing-12: 48px;
  --ps-spacing-16: 64px;
}
```

### Border Radius

```css
:root {
  --ps-radius-sm: 6px;
  --ps-radius-md: 10px;
  --ps-radius-lg: 16px;
  --ps-radius-xl: 24px;
  --ps-radius-full: 9999px;
}
```

### Typography

```css
:root {
  --ps-font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --ps-font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;

  --ps-text-xs:   0.75rem;   /* 12px */
  --ps-text-sm:   0.875rem;  /* 14px */
  --ps-text-base: 1rem;      /* 16px */
  --ps-text-lg:   1.125rem;  /* 18px */
  --ps-text-xl:   1.25rem;   /* 20px */
  --ps-text-2xl:  1.5rem;    /* 24px */
  --ps-text-3xl:  1.875rem;  /* 30px */

  --ps-leading-tight: 1.25;
  --ps-leading-normal: 1.5;
  --ps-leading-relaxed: 1.75;
}
```

### Z-Index Scale

```css
:root {
  --ps-z-base:      0;
  --ps-z-raised:    100;
  --ps-z-dropdown:  1000;
  --ps-z-sticky:    2000;
  --ps-z-overlay:   3000;
  --ps-z-modal:     4000;
  --ps-z-popover:   5000;
  --ps-z-toast:     9000;
  --ps-z-tooltip:   9500;
  --ps-z-max:       10000;
}
```

---

## Checkliste fuer Entwickler

Vor jedem Merge pruefen:

### Micro-Interactions
- [ ] Hover-, Focus-, Active-States fuer alle interaktiven Elemente
- [ ] Focus-Ring sichtbar und kontrastreich
- [ ] Keine Layout-Shifts bei Interaktionen

### Animationen
- [ ] `prefers-reduced-motion` respektiert
- [ ] Keine Animationen > 1s (ausser Ambient)
- [ ] Nur GPU-Properties animiert (`transform`, `opacity`, `filter`)

### Loading
- [ ] Skeleton oder Spinner fuer Ladezeiten > 300ms
- [ ] Mindestens 500ms Skeleton-Anzeige (kein Flicker)
- [ ] Progress-Feedback bei Ladezeiten > 5s

### Errors
- [ ] Alle API-Fehler mit menschlicher Nachricht + Handlungsanweisung
- [ ] Retry-Button bei transienten Fehlern
- [ ] Empty States visuell gestaltet

### Accessibility
- [ ] Kontrast >= 4.5:1 (Text) / 3:1 (UI) in beiden Themes
- [ ] Keyboard-navigierbar (Tab, Enter, Escape, Arrows)
- [ ] ARIA-Labels fuer Icon-Buttons und dynamische Inhalte
- [ ] Touch Targets >= 44x44px

### Responsive
- [ ] Getestet auf 375px, 768px, 1280px, 1536px
- [ ] Kein horizontales Scrollen
- [ ] Touch-Targets gross genug auf Mobile

### Dark / Light
- [ ] Beide Themes visuell geprueft
- [ ] Keine hart-codierten Farben
- [ ] Schatten und Transparenzen in beiden Themes korrekt

### Eye-Candies
- [ ] Performance-Budget eingehalten (< 5ms/Frame)
- [ ] Auf Low-Battery / reduced-motion deaktiviert
- [ ] Funktionalitaet ohne Eye-Candies gewaehrleistet

---

> _"The best interface is the one that disappears — until the moment you need it."_
> — PilotSuite Design Philosophy
