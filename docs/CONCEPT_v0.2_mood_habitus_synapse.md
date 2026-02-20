# PilotSuite – Konzept v0.2 (Mood + Habitus + Synapsen + Vorschläge)

Stand: 2026-02-07

## Ziel
Ein zusätzlicher Denk-/Entscheidungs-Layer für Home Assistant, der:
1) **Zustände & Events** beobachtet,
2) daraus **abstrakte Situationssignale** (Moods) ableitet,
3) **Verhaltensmuster** (Habitus) lernt,
4) aus beidem **Synapsen** (Beziehungen) generiert,
5) **Automationsvorschläge** macht, die der User **bestätigt** (Governance-first).

MVP-Example: „Mir fällt auf: Wenn die Kaffeemaschine eingeschaltet wird, folgt oft die Kaffeemühle. Soll ich das als Automation vorschlagen?“

---

## Begriffe
- **Neuron**: kleinste Feature-/Heuristik-Einheit (z.B. „morgens“, „TV läuft“, „Anwesenheit“). Output: Scores + Begründung.
- **Mood**: abstrakte, nicht zwingend emotionale „Lage“ als Vektor (active/focus/relax/away/sleep …) inkl. Unsicherheit.
- **Habitus**: Mustererkennung über Events (typisch: Sequenzen A→B in Zeitfenstern) + Statistik.
- **Synapse**: Kante im Graphen, die Quellen (Mood/Habitus) mit Zielen (Option/Automation) verbindet.
- **Advisor**: Selektiert/Rankt Synapsen → erzeugt Kandidaten (Vorschläge).

---

## Architektur (Module)
### 1) Ingest
- Quelle: Home Assistant State-/Service-Events
- Vorverarbeitung: **Kanten statt Level** (off→on), **Debounce**, Ignore unknown/unavailable, Domain/Entity-Allowlist.

### 2) Mood Engine
- Input: Neuron-Scores + Kontext
- Output: `MoodSnapshot(scope, mood_vector, uncertainty, contributors)`

### 3) Habitus Engine
- Input: (debounced) Actions + `MoodSnapshot` zum Zeitpunkt der Action
- Output:
  - `PatternStats` (support/confidence/lift/lag)
  - `CandidateAutomation` (Vorschlag, erklärbar)

MVP Pattern-Familie:
- **Sequenz-Regeln**: „Nach A passiert B innerhalb Δt“
- Inkrementell über Sliding-Window-Deques + Zähler, scoring periodisch.

### 4) Synapse Engine
- Vereinheitlicht Kandidaten zu Graph-Kanten.
- Mood-Gating: Kandidat nur wenn `mood_match` passt und uncertainty niedrig.

### 5) Advisor (Governance)
- Erstellt Vorschläge **nie automatisch aktiv**.
- Stellt sie in HA als **Repair/Issue** bereit und liefert eine **Blueprint**-basierte Umsetzung.

---

## Habitus MVP: Pattern-Detection (praktisch)
### Action Tokenization
- `domain.entity_id: from→to` (z.B. `switch.grinder: off→on`)
- Optional Sensors: Schwellen-Edges (z.B. power <5W → >800W)

### Statistik
Für Paare A→B (innerhalb Δt):
- `support = count_pair(A,B)`
- `confidence = count_pair(A,B)/count_action(A)`
- `lift = confidence / (count_action(B)/total_actions)`
- `median_lag_s` aus Delay-Histogramm

Empfehlungsschwellen (Startwerte):
- `support >= 8` UND `confidence >= 0.75` UND `lift >= 1.5`

Privacy/Storage:
- Persistiere bevorzugt **aggregierte Counts**, keine Raw-Historie.

---

## Mood-Weighting
Zwei Ebenen:
1) **Beim Lernen**: Muster speichert Mood zum Zeitpunkt A → `mood_profile`.
2) **Bei Vorschlägen**: `relevance = f(confidence, lift, support) * mood_match * governance_factor`.

`mood_match` MVP: Dot-Product / Cosine Similarity zwischen `current_mood` und `pattern.mood_profile`.

---

## Home Assistant UX
### Best practice (robust): Repairs + Blueprints
- Integration erzeugt Repair-Issue für jeden neuen Vorschlag.
- „Fix“ führt in einen Flow, der:
  - Accept → erstellt Automation aus Blueprint (oder führt Nutzer zur Blueprint-Erstellung)
  - Reject → blocklist / downrank
  - Defer/Snooze

Optional: Button „Create recommended…“ (Shortcut), aber Blueprint-first bleibt Default.

---

## Offene Design-Entscheidungen (nächste Iteration)
1) Event-Transport: HA → Core Push (Webhooks) vs. Core → HA WebSocket (LLAT). Präferenz: HA push.
2) Token: X-Auth-Token überall (API + Webhook callbacks).
3) Automation-Erstellung: Blueprint-only vs. 1-Klick-Create (Storage write, fragiler).
4) Scope-Modell: global vs. area/person-spezifisch.

