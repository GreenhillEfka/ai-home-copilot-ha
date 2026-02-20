# Fragen / Klärungen (autopilot Run 14:49)

> ⚠️ **Entscheidungspriorität**: P0 (Testing Suite) → P1 (TAG_SYSTEM v0.2) → P2 (Energy Module)
>
> **Update 2026-02-14 14:59**: Testing Suite v0.1 Stub angelegt (Tests für Candidate Poller, Repairs, Decision Sync). P0 teilweise adressiert — vollständige Implementierung folgt nach P1 Entscheidungen.

---

## P0 — Testing Suite (vorrangig)

### 1. Testing Suite für Production-Deployment
**Status**: ✅ Stub implementiert (2026-02-14 14:59)
**Empfehlung (Decision Matrix Run #7):** ✅ **JA — Testing Suite v0.1 implementieren**

| Option | Aufwand | Wert |
|--------|---------|------|
| SystemHealth Modul | Niedrig (~1 Woche) | Mittel |
| Energy Module | Mittel-Hoch | Hoch |
| **Testing Suite** | Niedrig-Mittel | **Hoch** ⭐ |

**Begründung:**
- Testing reduziert Risiko vor Production-Rollout
- Bestehende Module (Core v0.4.x, HA Integration v0.6.x) sind reif für Verifikation
- Keine Blockierung durch offene Spezifikationsfragen

**Empfehlung:** Testing Suite v0.1 zuerst implementieren (Repairs workflow, Candidate Poller, Decision Sync)

---

## P1 — TAG_SYSTEM v0.2 (basierend auf Decision Matrix)

### 2. HA-Labels materialisieren
**Empfehlung:** Nur ausgewählte Facetten (`role.*`, `state.*`) → NICHT automatisch alles

**Begründung:** Privacy-first, Learned Tags sind instabil

---

### 3. Subjects v0.1
**Empfehlung (Decision Matrix):** ✅ **Alle unterstützten HA-Label-Typen** (`entity`, `device`, `area`, `automation`, `scene`, `script`, `helper`)

**Begründung:** Maximale Flexibilität, zukunftssicher

---

### 4. Subject IDs
**Empfehlung (Decision Matrix):** ✅ **Mix aus Registry-ID + Fallback**

```yaml
# canonical_subject_id Schema
- entity      → entity_id
- device      → device_id  
- area        → area_id
- automation  → automation_id
- script      → script_id
- scene       → scene_id
- helper      → helper_id
```

---

### 5. Namespace-Policy
**Empfehlung:** `user.*` NICHT als interner Namespace — **nur HA-Labels importieren**

**Begründung:** Klarere Trennung, HA als Single Source of Truth

---

### 6. Lokalisierung
**Empfehlung:** ✅ **Nur `display.de` + `en`** (v0.1); i18n später bei Bedarf

---

### 7. Learned Tags → HA-Labels
**Empfehlung (Decision Matrix):** ✅ **NIE automatisch** — nur nach expliziter Bestätigung

**Begründung:** Privacy-first, Labels sind HA-nativ/sichtbar

---

### 8. Farben/Icons
**Empfehlung:** HA als UI-Quelle akzeptieren, nur IDs synchron halten

---

### 9. Konflikte/Duplikate
**Empfehlung:** Existierende HA-Labels ohne `aicp.*` Namespace **ignorieren** (nicht überschreiben)

---

### 10. Habitus-Zonen
**Empfehlung:** Als eigene interne Objekte mit Policies (wie im Doc spezifiziert)

---

## P2 — Energy Module (geblockt durch P0-P1)

### 11. Sensor Inventory (noch offen)
> ⚠️ **Warte auf P0-P1** — Energy Module Konfiguration erfordert klare Tag-System-Entscheidungen

---

## Migration

### 12. Legacy-Configs
**Empfehlung:** Start bei v0.1 — keine Legacy-Migration nötig

---

*Autopilot Run: 2026-02-14 14:49*
*Decision Matrix Basis: Run #7 (2026-02-14 14:20)*

---

## P3 — Aktueller Stand (2026-02-15)

**Status:** Keine neuen Fragen nach Deep-Audit.

**Offene P0-Items (Decision Matrix #10):**
1. Fix `BrainGraphStore` → `GraphStore` (provider.py)
2. Convert `tags/api.py` von aiohttp zu Flask

**Sicherheit:** CRITICAL-issues in `log_fixer_tx.py` (Auth + path validation) erfordern schnelle Korrektur.
