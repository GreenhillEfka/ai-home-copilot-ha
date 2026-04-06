# PilotSuite v1.x SOTA-Innovationsplan
## Scope: Slices 301–305
**Status:** Ready (Plan/Spezifikation)
**Pflicht-Schnittstelle:** `SOTA_V1_X_INNOVATION_PLAN.md`
**Zielbild:** Alle 5 Slices werden auf nachvollziehbarer, formal definierter Logik implementiert; keine Implementation in diesem Artefakt.

---

## Gemeinsame Ausgangslage

- Zeitscheibe: v1.x Echtzeitbetrieb, bestehende Module `copilot_core/presence` und `copilot_core/collective_intelligence`.
- Einheitliche Zeitbasis: `now = datetime.now(timezone.utc)`.
- Alle Entscheidungen sind **probabilistisch**, aber deterministisch rekonstruierbar durch persistierte Metriken.
- Bei widersprüchlichen Daten gilt: **zuerst robuste Statistik, dann Sensorfusion**.

---

## Slice 301 — Thompson Sampling (Preference Learning Balance)

### 1) Ziel
Aus der reinen Heuristik eine balancierte Präferenzwahl (Exploit/Explore) mit adaptiver Lernkurve machen.

### 2) Datenmodell (pro User, Zone, Preference-Key, Arm)
- `alpha` (Erfolgsgewicht) 
- `beta` (Misserfolgsgewicht)
- `n` = `alpha + beta`
- `last_update_ts`
- `decay_half_life_sec` (konfigurierbar, Default 14 Tage)

Initialwerte (Prior):
- `alpha = 1.0`, `beta = 1.0`

### 3) Ereignisverarbeitung (Update-Logik)
Für jeden Arm wird aus Feedback ein gewichteter Erfolg `r∈[0,1]` erzeugt.

- **Explicit Accept** → `r = 1.0`
- **Explicit Reject** → `r = 0.0`
- **Implicit Keep/Undo** (optional, wenn konfiguriert):
  - Aktion wird ohne Undo weitergeführt nach `τ_keep=120min` → `r = 0.4`
  - Manuelle Deaktivierung/Undo innerhalb von `τ_keep` → `r = 0.0`
- **Update:**
  - `alpha ← alpha + r * w_feedback`
  - `beta  ← beta + (1-r) * w_feedback`

### 4) Zeitliche Entwertung (Stabilisierung gegen stale Präferenzen)
Vor jedem Update:
- `decay = exp(-Δt / T_half)` mit `T_half = decay_half_life_sec`
- `alpha = 1 + (alpha - 1) * decay`
- `beta  = 1 + (beta - 1) * decay`

Damit gilt: neue Nutzerverhalten dominieren, ohne Kaltstart-Effekte zu verlieren.

### 5) Auswahlregel (entscheidend)
Für `k` verfügbare Actions/Arme:
1. `sample_k ~ Beta(alpha_k, beta_k)`
2. `score_k = sample_k`
3. Kandidat mit maximalem `score_k` wird vorgeschlagen.

**Sicherheits-Override (Cold-Start/Freeze):**
- Wenn `n < 4` (zu wenig Evidenz):
  - kein Random aus `sample`; deterministisch wählen nach `mean = alpha/(alpha+beta)` und priorisierter Prior-Order.

### 4) Exporte
- Logging/Telemetry je Entscheidung:
  - `arm`, `sample`, `mean`, `n`, `alpha`, `beta`, `reason`.
- API-/Service-Antwort soll neben gewähltem Arm den `confidence_proxy = mean` ausgeben.

### 6) Acceptance-Checks
- Bei identischem Feedbacksatz erzeugt derselbe Seed dieselben Entscheidungen.
- Bei `alpha=beta=1` liefern alle Arme gleiches Exploration-Verhalten.
- Kein Arm darf in endloser Kaltstartphase dominant werden.

---

## Slice 302 — Wilson Score Interval (Presence Confidence)

### 1) Ziel
Präsenzkonfidenz formal robust gegen kleine Stichproben stabilisieren.

### 2) Evidenzmodell (pro Zone)
Pro Sensorbeobachtung wird eine gewichtete Bernoulli-Evidenz gespeist:
- `success += w * x`, `x ∈ {0,1}` (`1` = Präsenzsignal, `0` = Abwesenheit)
- `total += w`

Gewicht `w` (0…1):
- Sensor-Konfidenz × Sensor-Priorität × Recency-Wert.

### 3) Rekursive Zeitgewichtung
Vor jeder Aktualisierung:
- `decay = exp(-Δt / 900)` (Halbwertszeit 15 min)
- `success ← success * decay`
- `total   ← total * decay`
- dann `success += w*x`, `total += w`

### 4) Wilson-Lower-Bound Formeln (95%-Intervall)
Für `n > 0`, `p̂ = success / total`, `z = 1.96`:

- `den = 1 + z^2/n`
- `lb = (p̂ + z^2/(2n) - z * sqrt((p̂*(1-p̂) + z^2/(4n)) / n)) / den`
- `ub = (p̂ + z^2/(2n) + z * sqrt((p̂*(1-p̂) + z^2/(4n)) / n)) / den`

Clamp: `lb,ub ∈ [0,1]`, `n==0 → lb=0.5, ub=0.5`

### 5) Entscheidungsregel für Zone
- `P_occ = lb`
- `P_vac = 1 - ub`

Zone-State:
- `P_occ >= 0.68` → `PRESENT`
- `P_vac >= 0.68` → `ABSENT`
- sonst `UNCERTAIN`

### 6) Übergangs-Hysterese
- `P_occ`/`P_vac` nur nach `hysteresis_hold = 2` aufeinanderfolgenden Samples übernehmen.
- `UNCERTAIN` darf den Zustand höchstens für `t_uncertain_max=60s` trennen, danach als neuer state bestätigen.

### 7) Acceptance-Checks
- Bei 1 Treffer / 1 Versuch liefert Wilson ein konservatives `lb<1`, keine 100%-Sicherheitsillusion.
- Für `n=100` nähert sich die Kennung `lb` stark der Rohauswertung an.

---

## Slice 303 — mmWave Radar Fusion (Occupancy)

### 1) Ziel
Statisches Verbleiben im Raum (Schlaf/Stillstand) erkennen, ohne Bewegungs-Timeouts zu „überfalschen Leerräumen“ werden zu lassen.

### 2) Eingaben pro mmWave-Sensor
Erwartete Signale aus der Entität/Attribute:
- `is_present` (on/off/state)
- `target_count` (Integer)
- `movement_state` (optional, moving/static)
- `micro_movement` (numerisch)
- `radar_confidence`/`confidence`

### 3) Grundscores

a) Basisscore aus Zielzahl:
- `target_score = min(1.0, target_count / 4)`

b) Bewegungsscore:
- `move_score = 1.0` wenn `movement_state == moving` sonst `0.0`

c) Mikro-Bewegungsscore (normiert):
- `micro_norm = clip((micro_movement - noise_floor)/(micro_ceiling-noise_floor), 0, 1)`
- default `noise_floor=0.10`, `micro_ceiling=0.70`

d) Kombinierte mmWave-Occupancy-Wahrscheinlichkeit:
- `p_mm = clip(0.45*target_score + 0.35*move_score + 0.20*micro_norm, 0, 1)`
- zusätzlich `p_mm = p_mm * radar_confidence`

e) Occupancy-Mode:
- `static` wenn `is_present` und `move_score==0` und `micro_norm >= 0.2`
- `moving` wenn `is_present` und `move_score==1`
- `none` sonst

### 4) Occupancy-Hold nach mmWave-Rückgang
- Wird `p_mm >= 0.6` erreicht, setze `last_mmwave_present_at = now`.
- Bei anschließendem `none`:
  - if vorher `mode == static`: off-hold `T_hold = 240s`
  - if vorher `mode == moving`: `T_hold = 120s`
  - sonst standard `T_hold = 60s`
- Bis `now <= last_mmwave_present_at + T_hold`: mmWave liefert mindestens `p_mm_hold = 0.5` in Fusion/Pipeline.

### 5) Fusion mit Zone-Pipeline
- mmWave wird als eigener evidentieller Kanal in die Zone-Fusion eingespeist (Prior vor Standard-PIR).
- Bedingung für harte Bestätigung in bewegungslosen Räumen:
  - `is_present=False`, vorherige mmWave-Mode war `static`, und `time_since_last_mmwave_present <= 240s` → Zone bleibt `PRESENT` (oder `UNCERTAIN` nur bei extremer Gegensignalstärke).

### 6) Ausgabe-Felder (minimale Pflicht)
- `mmwave.p`: 0..1
- `mmwave.mode`: static|moving|none
- `mmwave.last_present_ts`
- `mmwave.hold_until`

### 7) Acceptance-Checks
- Bei `target_count>0`, keine Bewegung, aber `micro_norm>=0.2` → Zone wird nicht sofort frei.
- Bei echtem Verlassen + `none` werden mindestens `T_hold` Sekunden keine abrupten Leermeldungen erzeugt.

---

## Slice 304 — Federated Learning Library

### 1) Ziel
Mathematisch belastbares Aggregations-Framework statt einfacher Mittelwerte; harte Ausreißer/fehlerhafte Updates abfangen.

### 2) Eingangsmodell pro Round
- `updates`: Liste gewichteter Model-Update-Objekte.
- pro Update: `node_id, model_version, timestamp, weights, metrics, n_samples, trust_score, privacy_budget_left, staleness_sec`

Rundenvorbedingungen:
- `len(valid_updates) >= min_participants`
- `model_version` konsistent
- `staleness_sec <= staleness_max`

### 3) Vorberechnung pro Update
Für jedes Gewichtstensor:
1. Flatten und Typprüfung (`float`-fähig)
2. Norm-Clipping:
   - `g = w * min(1, C/||w||2)` mit Clip `C`
3. Optional Signiertracking: kein Code, aber explizit als Auditfeld speichern.

### 4) Krum (Byzantine-Resistenz)
Für `m` gültige Updates und geschätzte `f` adversarial nodes:
- `f = floor( min( (m-2)/2, byzantine_cap) )`
- Für jedes Update `i`:
  - berechne alle Distanzen `d_ij = ||Δ_i - Δ_j||2`
  - sortiere aufsteigend
  - `score_i = sum(first m-f-2 distances)`
- Krum-Ausgabe: Update mit minimalem `score`.
- `multi_krum` (optional): `m-f` beste Kandidaten mittelwerten.

### 5) Alternative Aggregationen (zusätzlich vorhanden)
- `fed_avg`: gewichtetes Mittel auf Node-Trust
- `fed_median`: pro Parameter Median
- `trimmed_mean`: Trimmen per Anteil `trim_ratio=0.1`

### 6) Trust- & Zeitgewichtung

a) Basisgewicht je Node:
- `w_node = trust_score * exp(-age/τ_node) * log(1 + n_samples)`

b) Gesamtgewicht pro Param `w = w_node`.

### 7) Differential Privacy Layer
Nach Aggregation:
- Norm-Dimension pro Parameter `S` (Sensitivität, abgeleitet aus clipped updates)
- Mechanismus:
  - **Laplace**: `scale = S / ε`
  - Noise pro Parameter ~ `Laplace(0, scale)` (Standard)

### 8) Ausgabe der Round-Metrik
Notwendig für spätere Auswertung:
- `selected_indices`, `excluded_indices`, `aggregation_method`, `epsilon_spent`, `byzantine_score`, `participant_count`, `timestamp`.

### 9) Acceptance-Checks
- Bei gleichen Updates mit `f=0` muss Krum ~ Durchschnitt treffen.
- bei 1 bösartiger Divergenz (`norm deutlich ausreißend`) darf Krum nicht automatisch den Ausreißer wählen.

---

## Slice 305 — Bayesian Sensor Fusion

### 1) Ziel
Konfliktsituation (z. B. BLE sagt Home, mmWave sagt Empty) formal und nachvollziehbar auflösen.

### 2) Bayes-Modell pro Zone
Zustandsvariable: `H ∈ {occupied, empty}`.

Für jede Evidenz `e`:
- `x_e ∈ {0,1}` (1=präsenz), `w_e` (Gewicht 0..1),
- Sensor-spezifische Fehler:
  - `TPR_e` (true positive rate), `FPR_e` (false positive rate)

Prior:
- `P0(H=occupied)` = Wilson-basierter Zone-Prior aus Slice 302 (oder Persistierter Zustand bei Start = 0.5).

### 3) Log-Odds Update

```text
odds = P/(1-P),  P = P0(H=occupied)

für jede Evidenz e:
  if x_e = 1:
      llr_e = ln(TPR_e / FPR_e)
  else:
      llr_e = ln((1-TPR_e) / (1-FPR_e))

  odds *= exp(w_e * llr_e)
  P = odds / (1+odds)
```

Clamp am Ende: `P ∈ [0.01, 0.99]`.

### 4) Gewichtung der Evidenz
`w_e = conf_e * rel_e * decay(Δt)`
- `conf_e` = Sensorkonfidenz (z. B. mmWave-p_mm)
- `rel_e` = aktuelle Zuverlässigkeit aus Sensor-Historie (EWMA)
- `decay(Δt)=exp(-Δt / 300)`

### 5) Konfliktmodus
- Definiere Margin `m = |P - 0.5|`.
- Wenn `m < 0.12` → `state=UNCERTAIN`.
- Im Konfliktmodus gilt: keine harte Entscheidung, sondern `confidence = 2*m` und Konflikt-Metriken im Eventlog (`top2 evidences`, `margin gap`).

### 6) Übergangs-Hysterese mit Zone-State
- Wenn neuer Zustand `present`/`empty` und vorheriger Zustand bereits gleich: sofort übernehmen.
- Wenn neuer Zustand anders, aber `m < 0.2` oder letzter Zustand stabil älter als `grace_window=8s`, dann nur `uncertain` und hold.
- Erst bei `m >= 0.20` und 2 aufeinanderfolgenden Zyklen harte Umschaltung.

### 7) Ausgabe
Für jede Zone liefern:
- `posterior_occupied` (0..1)
- `fusion_mode` (present/absent/uncertain)
- `conflict_detected` (bool)
- `evidence_top` (3 stärkste Evidenzen mit Gewichten)

### 8) Acceptance-Checks
- Bei stark widersprüchlichen Quellen wird nicht vorschnell auf 0/1 gefahren.
- Bei stabilen Signalen (`m` steigt über 0.2 und hält 2 Zyklen) erfolgt deterministisch die harte Umschaltung.

---

## Cross-Slice-Arbeitslogik (301–305)

1. **Slice 302** erzeugt den robusten Präsenz-`prior`.
2. **Slice 303** liefert mmWave-Basiswahrscheinlichkeit + Occupancy-Mode + Hold.
3. **Slice 305** kombiniert diese und weitere Sensoren per Bayes-Law zur finalen Zone-Entscheidung.
4. **Slice 304** liefert die Infrastruktur für verteilte Modellaktualisierung (inkl. Robustheit), die später von Präferenzlern-Layern gespeist werden kann.

---

## Definition of Done (für diese Artefakt-Folge)
- Plan liegt vollständig in dieser Datei ohne Implementation-Code vor.
- Alle 5 Slices haben:
  - klar definiertes Datenmodell
  - exakte Formel-/Entscheidungslogik
  - deterministische Übergangsregeln
  - messbare Acceptance-Checks

