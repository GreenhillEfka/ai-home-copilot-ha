# Drag & Drop für Widgets 💋✨

## Übersicht

Widgets im Dashboard sind jetzt frei positionierbar! Mit Interact.js für touch-freundliches Drag & Drop.

## Features

✅ **Drag & Drop mit Mouse + Touch** - Funktioniert auf allen Geräten  
✅ **Snap-to-Grid** - Widgets rasten automatisch am 20px Grid ein  
✅ **Drop-Zones visualisieren** - Highlight beim Drüberziehen  
✅ **Positionen speichern** - localStorage + Backend API  
✅ **Undo/Redo** - Strg+Z / Strg+Y für Positionsänderungen  
✅ **Responsive** - Mobile: Swipe-Gesten statt Drag  
✅ **Resize Handles** - Widgets in der Größe anpassen  

## Dateien

### Frontend
- `static/js/drag_drop.js` — Drag & Drop Logic mit Interact.js
- `static/css/drag_drop.css` — Drop-Zones, Visual-Feedback, Grid-Styles

### Backend
- `api/v1/widget_positions.py` — REST API für Positionen

## API Endpoints

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| `GET` | `/api/v1/widgets/positions` | Alle Widget-Positionen |
| `POST` | `/api/v1/widgets/positions` | Neue Position speichern |
| `GET` | `/api/v1/widgets/positions/<id>` | Position eines Widgets |
| `DELETE` | `/api/v1/widgets/positions/<id>` | Position löschen |
| `POST` | `/api/v1/widgets/positions/bulk` | Mehrere Positionen speichern |
| `POST` | `/api/v1/widgets/positions/<id>/history` | History für Undo hinzufügen |
| `POST` | `/api/v1/widgets/positions/<id>/undo` | Letzte Änderung rückgängig |
| `POST` | `/api/v1/widgets/positions/<id>/redo` | Rückgängig wiederherstellen |
| `POST` | `/api/v1/widgets/positions/reset` | Alle Positionen zurücksetzen |

## Payload Beispiel

### Position speichern
```json
POST /api/v1/widgets/positions
{
  "widget_id": "temp-wohn",
  "x": 100,
  "y": 200,
  "width": 300,
  "height": 200,
  "zone_id": "wohn",
  "snap_to_grid": true
}
```

### Bulk Save
```json
POST /api/v1/widgets/positions/bulk
{
  "positions": [
    { "widget_id": "temp-wohn", "x": 100, "y": 200 },
    { "widget_id": "humidity-wohn", "x": 420, "y": 200 }
  ]
}
```

## Verwendung im Dashboard

### Widgets mit Drag-Handle
```html
<div class="zone-card widget-container" 
     data-widget-id="temp-wohn" 
     data-x="0" 
     data-y="0">
    <div class="drag-handle">
        <i class="mdi mdi-drag"></i>
    </div>
    <!-- Widget Content -->
</div>
```

### JavaScript API
```javascript
// Drag & Drop Manager
dragDropManager.enableDrag('.widget-container');
dragDropManager.disableDrag('.widget-container');
dragDropManager.undo();
dragDropManager.redo();
dragDropManager.resetPositions();

// Positionen abrufen
const positions = dragDropManager.getWidgetPositions();
```

## Keyboard Shortcuts

| Tasten | Aktion |
|--------|--------|
| `Strg + Z` | Undo |
| `Strg + Shift + Z` oder `Strg + Y` | Redo |
| `Escape` | Drag abbrechen |

## Mobile / Touch

Auf Mobile-Geräten werden Swipe-Gesten erkannt:
- **Swipe Left/Right** — Widget horizontal bewegen
- **Swipe Up/Down** — Widget vertikal bewegen

Touch-Optimierung: `touch-action: pan-x pan-y` erlaubt Scrollen, wenn nicht am Drag-Handle gezogen wird.

## Snap-to-Grid

Das Grid ist standardmäßig **20px** groß und kann in den Optionen angepasst werden:

```javascript
new DragDropManager({
    gridSnap: 20,      // Grid-Größe in Pixeln
    snapToGrid: true,  // Snap aktivieren
    showGrid: false,   // Grid sichtbar machen (Debug)
    allowResize: true  // Resize Handles aktivieren
});
```

## Persistenz

Positionen werden automatisch gespeichert:
1. **localStorage** — Client-seitig für schnelle Wiederherstellung
2. **Backend API** — Server-seitig für geräteübergreifende Synchronisation
3. **JSON-Datei** — `dashboard/data/widget_positions.json` (Fallback)

## WebSocket Events

Bei Änderungen werden folgende Events gesendet:
- `widget_position_update` — Neue Position
- `widget_position_deleted` — Position gelöscht
- `widget_positions_reset` — Alle Positionen zurückgesetzt

## Theme Support

Drag & Drop Styles unterstützen automatisch:
- Light Theme (Default)
- Dark Theme (`[data-theme="dark"]`)

## Accessibility

- Keyboard-Navigation für Drag & Drop
- Fokus-Indikatoren für Widgets
- `prefers-reduced-motion` wird respektiert
- Screen Reader-freundliche Labels

## Debugging

Grid sichtbar machen für Debugging:
```javascript
dragDropManager.options.showGrid = true;
dragDropManager.showGridIfEnabled();
```

Positionen im Console-Log:
```javascript
console.log(dragDropManager.getWidgetPositions());
```

---

**Erstellt:** 2026-03-02  
**Agent:** @Viewona  
**Version:** 1.0.0
