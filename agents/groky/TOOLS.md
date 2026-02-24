# TOOLS.md - Groky's Local Notes

Skills define _how_ tools work. This file ist für _deine_ specifics — das, was einzigartig in deinem Setup ist.

## Was Hier Eingeht

Zum Beispiel:

- Cameranamen und -orte
- SSH hosts und aliases
- Bevorzugte Stimmen für TTS (wenn du TTS nutzt)
- Speaker/Room names
- Device nicknames
- Alles umgebungsspezifische

## Beispiele

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Warum Trennen?

Skills sind shared. Dein Setup ist deins. Wenn du sie trennst, kannst du Skills updaten, ohne deine Notizen zu verlieren, und skills teilen, ohne deine Infrastruktur zu leaken.

---

Füge alles hinzu, was dir hilft, deine Arbeit zu machen. Das ist dein cheat sheet.

## Groky's Shortcuts

- Remote Ollama: `http://192.168.31.84:11434`
- API Key: `OLLAMA_API_KEY` (gespeichert in env)
- Repos: `pilotsuite-styx-ha`, `pilotsuite-styx-core`
- HACS Install: via custom repo (local path oder git URL)