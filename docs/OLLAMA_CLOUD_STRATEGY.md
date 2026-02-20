# Ollama Cloud Model Strategy

## Policy: CLOUD ONLY 🚀

**Keine lokalen Modelle während der Intensity Boost Phase!**

Wir nutzen ausschließlich **Ollama Cloud Modelle** für alle Entwicklungsaufgaben.

---

## Verfügbare Cloud Modelle

| Modell | Stärken | Einsatzzweck |
|--------|----------|--------------|
| **glm-5:cloud** | Bester Code, 744B params, schnell | Python/HA Code, Documentation |
| **minimax-m2.5** | State-of-the-art coding | Code, Productivity |
| **qwen3-coder-next** | Agentic coding workflows | Local dev patterns |
| **deepseek-r1:latest** | Bestes Reasoning, komplexe Analyse | Code Review, Architektur |
| **deepseek-v3.1** | Hybrid + thinking mode | Reasoning, Analysis |
| **kimi-k2.5** | Native multimodal agentic | Future use |

## Aktuelle Konfiguration

| Task-Typ | Modell | Warum |
|----------|--------|-------|
| Python/HA Code | `glm-5:cloud` | ✅ Primary |
| Komplexe Analyse | `deepseek-r1:latest` | ✅ Reasoning |
| Code Review | `deepseek-r1:latest` | ✅ Quality focus |
| Documentation | `glm-5:cloud` | ✅ Fast & good |
| Web-Suche | `deepseek-r1:latest` | ✅ Research |

## Modell-Auswahl-Matrix

| Task | Cloud Modell | Lokal? |
|------|--------------|--------|
| Python/HA Code | glm-5:cloud | ❌ |
| Architecture | deepseek-r1:latest | ❌ |
| Code Review | deepseek-r1:latest | ❌ |
| Docs | glm-5:cloud | ❌ |
| Web-Suche | deepseek-r1:latest | ❌ |
| Research | deepseek-v3.1 | ❌ |

## Konfiguration

```bash
# Nur Cloud Host
export OLLAMA_HOST="http://192.168.31.84:11434"

# Model Priority
glm-5:cloud > deepseek-r1:latest > deepseek-v3.1
```

## Warum Cloud Only?

1. **Kostenlos** - 12 Stunden Anfragen verfügbar
2. **Schnell** - glm-5:cloud ist sehr performant
3. **Hohe Qualität** - Beste Modelle für Code
4. **Consistent** - Einheitliche Ergebnisse
5. **Web-Suche** - Integrierte Recherche-Fähigkeit

## Lokale Modelle (deaktiviert)

| Modell | Status | Grund |
|--------|--------|-------|
| deepseek-r1:14b | 🚫 Deaktiviert | Cloud bevorzugt |
| codellama:latest | 🚫 Deaktiviert | Cloud bevorzugt |
| local/* | 🚫 Deaktiviert | Cloud Only Policy |

**Aktivierung nur bei:**
- Cloud komplett unavailable
- Expliziter User-Request

---

*Letzte Aktualisierung: 2026-02-14*
