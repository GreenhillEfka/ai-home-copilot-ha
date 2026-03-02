# PilotSuite - Quick Start Guide

## Was ist PilotSuite?

PilotSuite ist ein **intelligentes Heimautomatisierungs-System**, das dein Home Assistant Setup **kontinuierlich analysiert** und **automatisch Verbesserungen vorschlägt**. Statt starrer Automationen bekommst du einen **digitalen Hausmeister**, der aus deinen Gewohnheiten lernt.

## System-Architektur

```
[Home Assistant] ←→ [PilotSuite Integration] ←→ [Core Add-on (Brain)]
      ↑                                                       ↓
   Deine Geräte                                        AI Analyse & Empfehlungen
```

### Komponenten

1. **HA Integration** (`copilot_ha`) - Sammelt Daten, zeigt Empfehlungen
2. **Core Add-on** (`ha-copilot-core`) - KI-Engine für Analyse und Kandidaten-Generierung
3. **Brain Graph** - Visualisiert Gerät-Verbindungen und Aktivitätsmuster

## Installation (Schnellstart - 5 Minuten)

### Schritt 1: Core Add-on installieren

1. **Add-on Repository hinzufügen:**
   - Home Assistant → Add-ons → Add-on Store → ⋮ → Repositories
   - URL: `https://github.com/GreenhillEfka/pilotsuite-styx-core`
   - "ADD REPOSITORY"

2. **PilotSuite Core installieren:**
   - Neues Add-on "PilotSuite Core" → "INSTALL"
   - Configuration: Standard-Einstellungen OK
   - "START" + "Auto-Start" aktivieren

3. **Funktionstest:**
   - Add-on Log prüfen → sollte `Starting CoPilot Core...` zeigen
   - Web UI öffnen → `http://<ha-ip>:8686` → Dashboard sollte laden

### Schritt 2: HA Integration installieren

1. **HACS Repository hinzufügen:**
   - HACS → Integrations → ⋮ → Custom repositories
   - URL: `https://github.com/GreenhillEfka/pilotsuite-styx-ha`
   - Category: Integration → "ADD"

2. **Integration installieren:**
   - HACS → "PilotSuite" suchen → Download
   - Home Assistant neu starten

3. **Integration konfigurieren:**
   - Einstellungen → Geräte & Dienste → "Integration hinzufügen"
   - "PilotSuite" suchen
   - Core Add-on URL: `http://127.0.0.1:8686` (Standard)
   - Auth Token: (Optional - für erweiterte Features)

### Schritt 3: Erste Schritte

1. **Entity Allowlist konfigurieren:**
   - PilotSuite Integration → "Configure"
   - Wähle Bereiche (Wohnzimmer, Küche, etc.)
   - Aktiviere wichtige Geräte-Typen
   - "Submit"

2. **Brain Dashboard öffnen:**
   - Neues Entity: `button.copilot_brain_dashboard_summary`
   - Button drücken → zeigt Gesundheits-Score + Empfehlungen

3. **24h warten:** System braucht Daten für erste Analysen

## Was passiert nach der Installation?

### Datensammlung (Tag 1-3)
- Integration sammelt **Entity-Änderungen** (Licht an/aus, Sensordaten, etc.)
- **Privacy-first**: Nur Aktivitätsmuster, keine persönlichen Daten
- Core Add-on baut **Brain Graph** auf (Gerät-Verbindungen)

### Analyse & Empfehlungen (Tag 4+)
- System erkennt **wiederkehrende Muster**
- Generiert **Automatisierungs-Kandidaten**
- Zeigt **verbesserungswürdige Bereiche** auf

### Beispiel-Empfehlungen
- *"Du schaltest oft Küchenlicht + Kaffeemaschine zusammen → Automation vorschlagen?"*
- *"Heizung wird häufig manuell angepasst → Intelligente Zeitsteuerung?"*
- *"Ungenutzte Geräte erkannt → Energieeinsparung möglich"*

## Brain Dashboard verstehen

### Health Score (0-100)
- **90-100**: Optimal konfiguriert, starke Aktivität
- **70-89**: Gut, kleinere Verbesserungen möglich  
- **50-69**: Durchschnitt, mehr Automatisierung empfohlen
- **0-49**: Niedrig, Konfiguration überprüfen

### Empfehlungen-Typen
- **🔧 Reparaturen**: Fehlerhafte/inaktive Geräte
- **⚡ Optimierungen**: Automatisierungs-Chancen
- **📊 Insights**: Nutzungsmuster-Analyse

## Privacy & Sicherheit

### Was wird gesammelt?
- **Entity-Zustandsänderungen** (Licht an/aus, Temperatur-Werte)
- **Zeitstempel** für Muster-Erkennung
- **Geräte-Typen** und Bereiche

### Was wird NICHT gesammelt?
- **Kamera-Bilder** oder Audio
- **Namen** oder persönliche Bezeichnungen
- **IP-Adressen** oder Netzwerk-Details
- **Externe Cloud-Uploads**

### Lokale Verarbeitung
- **Alles läuft lokal** in deinem Home Assistant
- **Keine externen APIs** erforderlich
- **Du behältst die Kontrolle** über alle Daten

## Fehlerbehebung

### Integration kann Core nicht erreichen
```
Problem: "Unable to connect to CoPilot Core"
Lösung:
1. Core Add-on Status prüfen (läuft?)
2. Port 8686 frei? → Add-on Config prüfen
3. URL korrekt? → http://127.0.0.1:8686
```

### Brain Graph leer
```
Problem: Dashboard zeigt "No data"
Lösung:
1. Entity Allowlist konfiguriert?
2. Mind. 24h Datensammlung abwarten
3. Events Forwarder aktiv? → Logs prüfen
```

### Performance-Probleme
```
Problem: Home Assistant langsam
Lösung:
1. Entity Allowlist reduzieren
2. Nur wichtige Bereiche aktivieren
3. Core Add-on CPU/RAM prüfen
```

## Support

### Logs sammeln
1. **HA Integration**: Einstellungen → System → Logs → `custom_components.copilot_ha`
2. **Core Add-on**: Add-ons → PilotSuite Core → Log-Tab

### GitHub Issues
- **HA Integration**: https://github.com/GreenhillEfka/pilotsuite-styx-ha/issues
- **Core Add-on**: https://github.com/GreenhillEfka/pilotsuite-styx-core/issues

### Community
- **Home Assistant Forum**: [AI CoPilot Thread]
- **Discord**: [Invite-Link]

## Erweiterte Features (Optional)

### Auth Token Setup
```yaml
# Für erweiterte Core-Features
Integration Config:
  auth_token: "your-secret-token"
  
Core Add-on Config:
  auth:
    tokens:
      - "your-secret-token"
```

### API Access
- **REST API**: `http://127.0.0.1:8686/api/v1/`
- **Capabilities**: `/api/v1/capabilities`
- **Dashboard**: `/api/v1/dashboard`
- **Brain Graph**: `/api/v1/brain/graph`

## Updates

### Automatische Updates (empfohlen)
- **HACS**: Auto-Update für HA Integration
- **Add-on Store**: Auto-Update für Core Add-on

### Manuelle Updates
```bash
# Core Add-on
Add-ons → PilotSuite Core → Update

# HA Integration  
HACS → Integrations → PilotSuite → Update
```

## Changelog

Aktuelle Versionen:
- **HA Integration**: v0.4.6 (Enhanced UX, Error Handling)
- **Core Add-on**: v0.4.9 (Brain Dashboard, Privacy Envelopes)

Vollständiger Changelog: [CHANGELOG.md]

---

**Ready for Smart Living? 🏠✨**

Nach 24-48h solltest du die ersten Empfehlungen sehen. Das System lernt kontinuierlich und wird mit der Zeit immer präziser!