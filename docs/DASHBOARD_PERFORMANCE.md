# PS-059 · Dashboard Performance Report

**Task:** HA: PS-059 Dashboard-Performance-Monitoring
**Scope:** Dashboard-Statics-Analyse
**Date:** 2026-03-20
**Agent:** pilotclaw-subagent (fbefe1e3)

---

## 1. Bundle-Größen

### JavaScript (static/js/)

| File | Size | Lines | Status |
|---|---|---|---|
| `dashboard.js` | **35 KB** | 907 | 🔴 Largest |
| `drag_drop.js` | 25 KB | 736 | 🟡 Lazy-loaded |
| `zone_cards.js` | 23 KB | 603 | 🟡 Lazy-loaded |
| `accessibility.js` | 20 KB | 620 | 🟡 Utility |
| `ui_state_components.js` | 17 KB | 593 | 🟡 Shared |
| `websocket.js` | 7.6 KB | 240 | 🟢 Optimized |
| **Total JS** | **~128 KB** | 3699 | |

### CSS (static/css/)

| File | Size | Lines |
|---|---|---|
| `accessibility.css` | 18 KB | 726 |
| `style.css` | 15 KB | 817 |
| `dashboard.css` | 14 KB | 723 |
| `drag_drop.css` | 11 KB | 458 |
| `ui_state_components.css` | 4.9 KB | 230 |
| **Total CSS** | **~63 KB** | 2954 |

**Gesamt static/: ~300 KB (roh, unkompiliert)**

---

## 2. Ladezeiten-Schätzung (3G / 4G)

| Ressource | Roh | GZIP | 3G (~1.6 Mbps) | 4G (~10 Mbps) |
|---|---|---|---|---|
| dashboard.js | 35 KB | ~12 KB | ~60 ms | ~10 ms |
| drag_drop.js | 25 KB | ~8 KB | ~40 ms | ~6 ms |
| zone_cards.js | 23 KB | ~8 KB | ~40 ms | ~6 ms |
| accessibility.js | 20 KB | ~7 KB | ~35 ms | ~5 ms |
| ui_state_components.js | 17 KB | ~6 KB | ~30 ms | ~5 ms |
| websocket.js | 7.6 KB | ~3 KB | ~15 ms | ~2 ms |
| CSS total | 63 KB | ~18 KB | ~90 ms | ~15 ms |
| socket.io (CDN) | ~15 KB | — | ~75 ms | ~12 ms |
| MDI Font (CDN) | ~30 KB | — | ~150 ms | ~25 ms |
| **Summe (ohne CDN)** | ~191 KB | ~62 KB | **~310 ms** | **~51 ms** |

> Hinweis: Flask `flask-compress` aktiv → serverseitige GZIP-Kompression. HTML-Rendering + WebSocket-Init fügen ~200–400 ms hinzu.
> **TTFB +50–150 ms (lokale Flask-App)**
> **Geschätzte FCP: ~400–600 ms auf 4G**

---

## 3. Performance-Engpässe

### 🔴 Problem 1: Kein Minifying / Bundling in Produktion
**Impact:** Hoch — 40–60% der JS/CSS- Größe sind unnötig

- `dashboard.js` (35 KB roh) → ~10–12 KB mit minify
- CSS dasselbe Problem
- `build.mjs` ist vorhanden, wird aber NICHT im Produktions-Workflow verwendet
- Kein Tree-Shaking, kein Dead-Code-Elimination

**Empfehlung:** `build.mjs --prod` mit esbuild minify + tree-shaking

---

### 🔴 Problem 2: Render-Blocking CSS + Synchrone Script-Ladung
**Impact:** Hoch — FCP verzögert um ~200–300 ms

```html
<!-- Render-blocking im <head> -->
<link href="...mdi.min.css" rel="stylesheet">
<link rel="stylesheet" href="...style.css">

<!-- Sequentiell, ohne defer/async -->
<script src="...ui_state_components.js"></script>
<script src="...dashboard.js"></script>
```

**Empfehlung:**
```html
<link rel="stylesheet" href="...mdi.min.css" media="print" onload="this.media='all'">
<link rel="stylesheet" href="...style.css" media="print" onload="this.media='all'">
<script ... defer></script>
```

---

### 🟡 Problem 3: Code-Splitting Potential bei zone_cards + drag_drop
**Impact:** Mittel — -40 KB für Basis-Load

- `zone_cards.js` → nur wenn Zone-Grid-Tab aktiv
- `drag_drop.js` → nur wenn Drag-Drop-Editor aktiv

**Empfehlung:** Lazy-load bei erstem Zugriff

---

### 🟢 Problem 4: Externe CDN-Abhängigkeiten
**Impact:** Niedrig-Mittel

- `socket.io 4.5.4` über CDN → zusätzlicher DNS + Connection-Overhead
- MDI Font könnte als Subset oder defer

---

## 4. Top-3 Optimierungsvorschläge

### 1. ✅ Production Build Pipeline (HÖCHSTE PRIORITÄT)
**Impact:** -40-60% JS/CSS Größe, ~150 ms schnellerer Load

```bash
node build.mjs --prod
```

- Ziel: alle JS in 1–2 dist-Files bündeln
- CSS minified via cssnano oder esbuild
- Flask `url_for` auf dist-Dateien umstellen

**Aufwand:** ~1–2 h | **Einsparung:** ~100 KB roh → ~35 KB GZIP

---

### 2. ✅ Render-Blocking eliminieren
**Impact:** ~200–300 ms schnellerer FCP

- Font-Preload + print-onload Trick für CSS
- `defer` für alle Scripts
- Media-Attribute auf CSS

**Aufwand:** ~1 h | **Einsparung:** FCP -200 ms

---

### 3. ✅ Code Splitting für zone_cards + drag_drop
**Impact:** -40 KB für Basis-Load (Nicht-Editor-Nutzer)

```javascript
if (currentPage === 'zone-cards' && !window.zoneCardsLoaded) {
  const script = document.createElement('script');
  script.src = '...zone_cards.js';
  script.defer = true;
  document.head.appendChild(script);
}
```

**Aufwand:** ~2–3 h | **Einsparung:** -40 KB initiale Last

---

## 5. Bereits Implementiert (OPTIMIZATIONS.md Stand)

| Optimierung | Status | Impact |
|---|---|---|
| WebSocket Batch Updates (500ms) | ✅ Aktiv | Latenz -60% |
| GZIP Compression (flask-compress) | ✅ Aktiv | Message-Size -70% |
| Client-Side Debouncing (300ms) | ✅ Aktiv | Re-renders -60% |
| Performance API (/api/v1/performance) | ✅ Aktiv | Monitoring |
| Per-Widget Metrics | ✅ Aktiv | Monitoring |

---

## 6. Tasklog-Report

```
Task: PS-059 Dashboard-Performance-Monitoring
Status: ✅ COMPLETE

Files analysed:
  - dashboard/static/js/*.js (6 files, 3699 lines, ~128 KB)
  - dashboard/static/css/*.css (5 files, 2954 lines, ~63 KB)
  - dashboard/templates/dashboard.html
  - dashboard/OPTIMIZATIONS.md

Key findings:
  1. Kein Minifying/Bundling in Produktion → 40-60% oversized
  2. Render-blocking CSS + synchrone Scripts → FCP verzögert
  3. Code-Splitting Potential bei zone_cards + drag_drop
  4. WebSocket-Layer bereits gut optimiert

Top-3 Quick Wins:
  1. Production Build Pipeline (build.mjs --prod erweitern)
  2. Render-Blocking eliminieren (defer + print-onload CSS)
  3. Lazy-Load zone_cards + drag_drop

Deliverable: docs/DASHBOARD_PERFORMANCE.md ✓
```
