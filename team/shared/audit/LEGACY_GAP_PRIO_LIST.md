# Legacy Gap Prio-Liste (P0/P1/P2)

**Erstellt:** 2026-04-06
**Basierend auf:** V1_LEGACY_GAP_ANALYSIS.md
**Ziel:** Klare Priorisierung der 73 fehlenden Endpunkte für v1.0.0 Final

---

## P0 — SHOWSTOPPER (Muss für v1.0.0)
**Kriterium:** Ohne diese Features ist das System nicht produktionsbereit oder bricht kritische Workflows.

| Endpunkt | Grund | Status |
|----------|-------|--------|
| `DELETE /api/v1/notifications/:notification_id` | User kann Alerts nicht dismissen → UX-Blocker | ❌ Offen |
| `POST /api/v1/notifications/:notification_id/read` | User kann Benachrichtigungen nicht als gelesen markieren | ❌ Offen |
| `POST /api/v1/notifications/subscribe` | Keine Subscription-Management für Mobile Push | ❌ Offen |
| `POST /api/v1/notifications/unsubscribe` | Keine Opt-out Möglichkeit | ❌ Offen |
| `PUT /api/v1/notifications/subscriptions/:device_id` | Keine Device-Token Updates | ❌ Offen |
| `GET /api/v1/energy/baselines` | Keine Baseline-Referenz für Energy-Optimizer | ❌ Offen |
| `GET /api/v1/energy/explain/:suggestion_id` | Keine Erklärbarkeit für Energy-Vorschläge | ❌ Offen |
| `GET /api/v1/energy/suppress` | Keine Unterdrückung von Energy-Automatisierungen | ✅ Implementiert |
| `GET /api/v1/weather/pv-recommendations` | Keine PV-Optimierung (kritisch für Energy) | ❌ Offen |
| `GET /api/v1/weather/forecast` | Keine Wettervorhersage für Habitus-Planung | ❌ Offen |

---

## P1 — WICHTIG (Sollte für v1.0.0)
**Kriterium:** Komfort-Features, die User erwarten, aber nicht systemkritisch.

| Endpunkt | Grund | Status |
|----------|-------|--------|
| `GET /api/v1/habitus/dashboard_cards` | Keine Dashboard-Karten für Habitus-Zonen | ❌ Offen |
| `GET /api/v1/habitus/dashboard_cards/health` | Keine Health-Visualisierung pro Zone | ❌ Offen |
| `GET /api/v1/habitus/dashboard_cards/rules` | Keine Regel-Übersicht im Dashboard | ❌ Offen |
| `GET /api/v1/health/deep` | Keine tiefe System-Diagnose | ✅ Implementiert |
| `GET /api/v1/health/metrics` | Keine granularen Health-Metriken | ❌ Offen |
| `GET /api/v1/search` | Keine globale Suche (durch RAG teilweise ersetzt, aber Legacy-Bruch) | ❌ Offen |
| `DELETE /api/v1/candidates/:candidate_id` | Keine Löschung von Kandidaten | ❌ Offen |
| `GET /api/v1/candidates/graph_candidates` | Keine Graph-basierte Kandidaten-Suche | ❌ Offen |

---

## P2 — NICE-TO-HAVE (Kann nach v1.0.0)
**Kriterium:** Legacy-Kompatibilität oder durch SOTA ersetzt, aber nützlich für Power-User.

| Endpunkt | Grund | Status |
|----------|-------|--------|
| `DELETE /api/v1/vector/vectors` | Vector-DB durch RAG ersetzt | ❌ Offen |
| `DELETE /api/v1/vector/vectors/:entry_id` | Vector-DB durch RAG ersetzt | ❌ Offen |
| `GET /api/v1/vector/similar/:entry_id` | Durch Semantic Search ersetzt | ❌ Offen |
| `GET /api/v1/vector/stats` | Durch RAG Analytics ersetzt | ❌ Offen |
| `POST /api/v1/vector/embeddings` | Durch Ollama-Embedding ersetzt | ❌ Offen |
| `POST /api/v1/vector/embeddings/bulk` | Durch Ollama-Embedding ersetzt | ❌ Offen |
| `POST /api/v1/search/index` | Durch RAG-Ingest ersetzt | ❌ Offen |
| `POST /api/v1/kg/import/entities` | Durch neue Graph-Import-API ersetzt | ❌ Offen |
| `POST /api/v1/kg/import/patterns` | Durch neue Graph-Import-API ersetzt | ❌ Offen |

---

## SOFORT-MAßNAHMEN
1. **P0-Sprint:** PilotClaw implementiert die 10 P0-Endpunkte in Slices 175-180.
2. **P1-Sprint:** Parallel dazu P1-Features in Slices 181-185.
3. **P2-Backlog:** Nach v1.0.0 Final als v1.1 Roadmap.

**Keine Pausen. Wir schließen die Lücken. Go.**
