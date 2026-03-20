# Dashboard Performance Monitoring — PS-059

## Stand: 2026-03-20

## Bundle-Analyse

| Metrik | Wert |
|--------|------|
| Total JS | ~128 KB (6 Files, 3699 Lines) |
| Total CSS | ~63 KB (5 Files, 2954 Lines) |
|mallest Bundle (unkomprimiert) | ~300 KB |
| Geschätzte Load 4G | ~51 ms (nach GZIP, ohne CDN) |

## Top-3 Optimierungsvorschläge

### 1. Build Pipeline — Production Minification (HÖCHSTER IMPACT)
**Problem:** `build.mjs` läuft ohne `--prod` / Minification.

**Impact:** -40-60% JS/CSS Größe → ~150ms schneller Ladezeit.

**Empfehlung:**
```bash
node build.mjs --prod
```
- esbuild minify in build.mjs aktivieren
- CSS minification hinzufügen

### 2. Render-Blocking eliminieren
**Problem:** CSS und JS blockieren First Contentful Paint.

**Impact:** FCP -200ms.

**Empfehlung:**
- CSS via `media="print" onload`
- Scripts mit `defer` statt synchron
- Kritische CSS inline

### 3. Code Splitting — Lazy Loading
**Problem:** `zone_cards.js` und `drag_drop.js` laden sofort, obwohl selten genutzt.

**Impact:** -40 KB initiale Last.

**Empfehlung:**
```javascript
// Lazy load zone cards
import('./zone_cards.js').then(module => { ... });
```

## WebSocket-Layer Status

Laut `OPTIMIZATIONS.md` bereits solide:
- Batch + GZIP + Debounce aktiv
- Latency <100ms

## Hauptproblem

Fehlender Production-Build-Schritt (`build.mjs --prod`).

## Nächste Schritte

1. `build.mjs` mit Minification-Flag erweitern
2. CSS `media="print" onload` Pattern
3. Zone-Cards Lazy-Loading
