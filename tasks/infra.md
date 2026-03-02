# 🛡️ TASKS/INFRA.md — @toolix

**Queue für:** Security, CI/CD, DevOps, Infrastructure  
**Worker:** @toolix  
**Backup:** @groky

---

## 🚨 P0 — BLOCKER (Sofort)

- [ ] **P0-301:** Release-Pipeline: Auto-Sync HA+Core vor Release @assigned @toolix @eta 20min @status pending
- [ ] **P0-302:** HA Version fixen (v11.2.3 → v12.x.x synchron mit Core) @assigned @toolix @eta 15min @status pending
- [ ] **P0-303:** GitHub Actions: HA+Core parallel testen vor Release @assigned @toolix @eta 25min @status pending

---

## 🔥 P1 — HIGH (Nach P0)

- [ ] **P1-046:** Security Headers (CSP, HSTS, X-Frame-Options) @assigned @eta 20min @status pending
- [ ] **P1-047:** CORS Configuration Review + Fix @assigned @eta 15min @status pending
- [ ] **P1-048:** API-Rate-Limiting konfigurieren @assigned @eta 20min @status pending
- [ ] **P1-049:** CI/CD Pipeline: HA+Core Sync-Check @assigned @eta 25min @status pending

---

## 📊 P2 — MEDIUM (Wenn Kapazität)

- [ ] **P2-030:** Prometheus-Metriken erweitern @assigned @eta 20min @status pending
- [ ] **P2-031:** Alerting-Regeln für Critical Errors @assigned @eta 15min @status pending
- [ ] **P2-032:** Backup-Strategy dokumentieren @assigned @eta 20min @status pending

---

## ✅ COMPLETED (Diese Session)

- [x] **P1-045:** Security Headers implementiert @completed 2026-03-02T14:30:00+01:00 @commit def456

---

## 📋 WORKER-REGELN:

1. **Immer zuerst P0** abarbeiten
2. **Nach jedem Task:** Commit + Push + WhatsApp-Update
3. **HA+Core Sync:** Vor Release IMMER beide Repos auf gleiche Version prüfen
4. **Security-First:** Bei Security-Tasks immer @groky für Review

---

**Letztes Update:** 2026-03-02 14:45 CET  
**Nächster Task:** P0-301 (Release-Pipeline Auto-Sync)
