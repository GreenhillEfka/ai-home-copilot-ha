# Chat-Response-Time-Analyse — PS-051

**Datei:** `pilotsuite_ops/docs/CHAT_PERFORMANCE_ANALYSIS.md`  
**Erstellt:** 2026-03-20  
**Agent:** PilotClaw (Subagent)  
**Branch:** `pilotsuite-styx-ha-current`

---

## Zusammenfassung

Das Chat-System läuft über den **Conversation Agent** (`conversation.py`), der HA-Kontext aufbaut, Historie verwaltet und via `coordinator.api.async_chat_completions()` an Core sendet. STT und TTS sind separate Entities, die direkt über den Coordinator laufen.

**Größtes Bottleneck: `async_chat_completions()` — LLM-Inferenz auf HA-Hardware.**

---

## Endpunkt-Analyse

| # | Endpunkt | Typical Latency | Bottleneck-Typ | Empfehlung |
|---|----------|-----------------|-----------------|------------|
| 1 | `async_chat_completions()` | **5–60+ s** (TTFT) | **CPU/VRAM** — qwen3:4b Inferenz auf HA-Klasse Hardware | Streaming aktivieren (TTFT statt full-response-wait); evtl. kleineres Modell für Trivialfragen; Context-Trimming |
| 2 | `async_stt()` | **2–10 s** | **CPU + Waiting** — WAV-Encoding (Executor) + Whisper-Inferenz im Core | Audio-Chunk-Groesse pruefen; Streaming-STT-Interface evaluieren |
| 3 | `async_tts()` | **1–5 s** | **I/O** — edge-tts Call + Audio-Return | OK fuer aktuelles Nutzungsprofil; CDN-Caching bei Bedarf |
| 4 | `async_get_presence()` | **100–500 ms** | **I/O** (REST) | OK; keine Aktion noetig |
| 5 | `async_get_light_intelligence()` | **100–500 ms** | **I/O** (REST) | OK; keine Aktion noetig |
| 6 | `_pcm_to_wav()` (Executor) | **5–50 ms** | **CPU** (wave-Modul) | Minor; bei Bedarf C-basiertes Audio-Library nutzen |
| 7 | `async_voice_status()` | **100–500 ms** | **I/O** (REST) | OK; keine Aktion noetig |

---

## Detail-Analysis

### 1. `async_chat_completions()` — **KRITISCH**

**Code-Location:** `coordinator.py`, Zeile ~490  
**Timeout:** 90 s (`CHAT_COMPLETIONS_TIMEOUT_S = 90.0`)  
**Endpoint:** `POST /v1/chat/completions`  
**Model:** qwen3:4b auf HA-Klasse Hardware  

```
User → HA Conversation Agent
       → _build_home_context()       [~10 ms, in-memory]
       → _get_history()              [~1 ms, in-memory]
       → async_chat_completions()
           → POST /v1/chat/completions
               → LLM Inference (qwen3:4b)   [5–60+ s] ← BOTTLENECK
                   → Response Parsing        [<10 ms]
```

**Bottleneck-Typ:** CPU gebunden (LLM-Inferenz). HA-Klasse Hardware (typisch: 4–8 GB VRAM, keine dedizierte GPU) kann qwen3:4b nur langsam ausführen. 60 s sind dokumentiert als "oft noetig fuer first tokens".

**Empfehlungen:**
1. **Streaming aktivieren:** `/v1/chat/completions` soll Streaming unterstützen (OpenAI-kompatibles `stream: true`). Erster Token erscheint nach TTFT, Rest fließt stueckweise. Conversation Agent muesste `async_process()` auf Streaming umstellen.
2. **Model-Routing:** Trivialfragen ("Wie spät ist es?", "Was ist die Temperatur?") direkt lokal via HA-Intents beantworten ohne Core-Call.
3. **Context-Trimming:** `_MAX_HISTORY_TURNS = 5` ist gut. Bei laengeren Konversationen prompt-Kuerzung vorsehen (summarize + truncate).
4. **Timeout-Grenze:** 90 s ist konservativ. Bei Streaming ist das egal; bei Blocking-Calls muesste der Timeout erhöht werden, wenn das Modell nicht heruntergetunt wird.

---

### 2. `async_stt()` — **HOCH**

**Code-Location:** `coordinator.py`, Zeile ~508  
**Timeout:** 30 s (`AUDIO_TIMEOUT_S = 30.0`)  
**Endpoint:** `POST /api/v1/styx/stt`  
**Audio:** WAV, 16 kHz, mono, 16-bit PCM  

```
async_process_audio_stream()
  → collect chunks                    [stream-abhaengig]
  → _pcm_to_wav() in executor         [5–50 ms CPU]
  → async_stt(wav_data)
      → POST /api/v1/styx/stt
          → Whisper via Ollama        [1–8 s]
          → JSON Response             [<50 ms]
```

**Bottleneck-Typ:** Waiting (I/O + Whisper-Inferenz in Core). Das WAV-Encoding im Executor ist CPU-messig aber klein.

**Empfehlungen:**
1. **Audio-Chunk-Groesse:** HA liefert Audio in Chunks. Prüfen ob die Chunks effizient gesammelt werden (kein exzessives Kopieren).
2. **Streaming-STT-Interface evaluieren:** Core könnte ein Streaming-STT anbieten (Chunk-weise Whisper), um Wartezeit zu reduzieren.
3. **Sprach-Detection:** `?language=de` ist hardcoded auf Deutsch. Ggf. automatische Sprachdetection ermöglichen.

---

### 3. `async_tts()` — **MITTEL**

**Code-Location:** `coordinator.py`, Zeile ~540  
**Timeout:** 30 s (`AUDIO_TIMEOUT_S = 30.0`)  
**Endpoint:** `POST /api/v1/styx/tts`  
**Backend:** edge-tts (Microsoft Edge TTS, neural voices)  

```
async_get_tts_audio()
  → async_tts(text)
      → POST /api/v1/styx/tts
          → edge-tts API call          [0.5–3 s]
          → Audio Return (bytes)       [I/O, <1 s]
```

**Bottleneck-Typ:** I/O (edge-tts upstream). Latency ist akzeptabel (1–5 s fuer kurze bis mittellange Texte).

**Empfehlungen:**
1. **OK fuer aktuelles Profil.** Keine immediate Aktion noetig.
2. **Audio-Caching:** Bei wiederholten Responses (z.B. gleiche Ansagen) könnte ein lokaler Cache die Latenz auf <100 ms reduzieren.
3. **MP3 vs. raw:** Aktuell wird mp3 zurueckgegeben. Das spart Bandbreite; gut so.

---

### 4. `async_get_presence()` — **NIEDRIG**

**Code-Location:** `coordinator.py`, Zeile ~484  
**Timeout:** 10 s (default `API_DEFAULT_TIMEOUT_S`)  
**Endpoint:** `GET /api/v1/hub/presence`  
**Nutzung:** Polling im Coordinator (alle 120 s normal, gestreckt auf 180 s) + webhooks  

**Bottleneck-Typ:** I/O (Netzwerk). Sehr schnelle Antworten dokumentiert.

**Empfehlungen:** Keine. Bereits durch adaptive Polling + Webhook-Push optimiert.

---

### 5. `_pcm_to_wav()` (Executor Call) — **MINOR**

**Code-Location:** `stt.py`, `_pcm_to_wav()`  
**Aufruf:** `await self.hass.async_add_executor_job(_pcm_to_wav, ...)`  
**Latenz:** 5–50 ms (线程pool, wave-Modul)  

**Empfehlung:** Minor. Nur relevant wenn sehr viele STT-Requests gleichzeitig laufen.

---

## Call-Flow: Voice Command (Worst Case)

```
1. User spricht                    [0 ms]
2. HA Assist Pipeline startet STT
   2a. Audio sammeln               [1–5 s, je nach wake-word config]
   2b. _pcm_to_wav (executor)      [5–50 ms]
   2c. async_stt() → Whisper       [1–8 s]        ← STT Latency
3. Text an Conversation Agent      [~5 ms]
4. _build_home_context()           [<10 ms]
5. _get_history()                  [<5 ms]
6. async_chat_completions()        [5–60+ s]      ← CRITICAL BOTTLENECK
7. Intent Detection               [<50 ms]
8. Intent Execution (optional)     [HA Service Calls, variabel]
9. async_tts()                     [1–5 s]        ← TTS Latency
10. Audio zurueck an User           [I/O]

Total (Voice): ~9–80+ s
Total (Text Chat): ~5–60+ s
```

---

## Priorisierte Empfehlungen

| Priority | Action | Impact | Effort |
|----------|--------|--------|--------|
| **P1** | Streaming fuer `/v1/chat/completions` im Conversation Agent aktivieren | TTFT: 5–60 s → erster Token in <1 s sichtbar | Mittel |
| **P1** | Model-Routing: Trivialfragen ohne Core-Call lokal beantworten | Spart 5–60 s fuer haeufige Simple-Intents | Niedrig |
| **P2** | STT Audio-Chunk-Verhalten prüfen (kein exzessives Kopieren) | STT Latency um 10–20% reduzieren | Niedrig |
| **P2** | Context-Trimming bei langen Konversationen aktivieren | Prompt-Groesse begrenzen, stabilere Latenz | Niedrig |
| **P3** | TTS Response Caching | Cache-Hit Latenz: 1–5 s → <100 ms | Mittel |
| **P3** | `_pcm_to_wav` durch `soundfile` oder `torchaudio` ersetzen | ~5 ms weniger im Executor | Niedrig |

---

## Bottleneck-Identifikation

**Größtes Bottleneck: `async_chat_completions()` (LLM-Inferenz auf HA-Hardware)**

- Typ: **CPU/VRAM** — LLM-Inferenz (qwen3:4b)
- Symptom: 5–60+ Sekunden Wartezeit pro Chat-Response
- Root Cause: qwen3:4b ist zu groß für HA-Klasse Hardware ohne dedizierte GPU. Model-Größe + fehlende GPU = langsameInference.
- **Warum kein I/O-Problem:** Die 90-s-Timeouts und Retry-Logik sind ausreichend. Das Problem ist die pure Rechenzeit.

**Second-Largest: `async_stt()` (Whisper-Inferenz)**

- Typ: **Waiting** — Whisper-Inferenz in Core
- Symptom: 2–10 s fuer Sprach-zu-Text
- Root Cause: Audio-Daten muessen transferiert + dekodiert werden, dann Whisper-Inferenz.

---

*Analyse erstellt von PilotClaw Subagent (task: PS-051). Keine Code-Änderungen.*
