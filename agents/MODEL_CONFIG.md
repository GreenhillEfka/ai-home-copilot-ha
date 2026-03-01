# AGENT MODEL CONFIGURATION

**Fallback Model für alle Agents:**

```
ollama/qwen3.5:397b-cloud
```

## Model-Priorität (pro Agent):

1. **Agent-spezifisches Model** (wenn in Task definiert)
2. **Session-Default** (wenn gesetzt)
3. **Fallback:** `ollama/qwen3.5:397b-cloud` ✅

---

## Warum dieses Model?

- ✅ **397B Parameter** — Massive Kapazität für komplexe Tasks
- ✅ **Cloud-Hosted** — Schnell, keine lokale Ressourcen-Belastung
- ✅ **Qwen3.5** — State-of-the-Art für Coding & Reasoning
- ✅ **Ollama** — Einheitliche API, gut integriert

---

## Usage in sessions_spawn:

```python
sessions_spawn(
    task="...",
    model="ollama/qwen3.5:397b-cloud",  # Explizit setzen
    # ODER weglassen → Fallback wird automatisch genutzt
)
```

---

**Aktualisiert:** 2026-03-01 14:37 Uhr  
**Grund:** Einheitliches Fallback für alle Agents konfigurieren
