"""Voice Feedback Lovelace Cards — Slice 164.

NUR Darstellung (KEINE Logik):
- VoiceWaveformCard: Visuelle Anzeige von Push-to-Talk
- VoiceCommandHistoryCard: Letzte Sprachbefehle
- VoiceStatusCard: STT/TTS/Pipeline Status
- VoicePipelineCard: Vollständiger Voice-Feedback Loop

Architecture:
- Card holt Daten von HA Core API (keine Logik im Card)
- Audio-Verarbeitung läuft in voice_pipeline.py
- Push-to-Talk via Media Recorder API
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

_LOGGER = logging.getLogger(__name__)

# ─── Voice Waveform Card ────────────────────────────────────────────────────


def voice_waveform_card() -> Dict[str, Any]:
    """Voice Waveform + Push-to-Talk Card.

    States:
    - idle: Grauer Ring, "Halte zum Sprechen"
    - recording: Pulsierender grüner Ring, Waveform animiert
    - processing: Drehender Ring, "Verarbeite..."
    - done: Grüner Haken, Antworttext
    - error: Roter Ring, Fehlermeldung

    User-Action: mousedown → Recording start → mouseup → STT
    """
    return {
        "type": "custom:mod-card",
        "card_mod": {
            "style": """
                ha-card {
                    padding: 16px;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    border-radius: 16px;
                }
                .voice-ring {
                    width: 120px;
                    height: 120px;
                    border-radius: 50%;
                    border: 4px solid #4a5568;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 16px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    position: relative;
                }
                .voice-ring.recording {
                    border-color: #48bb78;
                    animation: pulse-ring 1.5s infinite;
                }
                .voice-ring.processing {
                    border-color: #4299e1;
                    animation: spin-ring 1s linear infinite;
                }
                .voice-ring.error {
                    border-color: #f56565;
                }
                @keyframes pulse-ring {
                    0%, 100% { box-shadow: 0 0 0 0 rgba(72, 187, 120, 0.4); }
                    50% { box-shadow: 0 0 0 16px rgba(72, 187, 120, 0); }
                }
                @keyframes spin-ring {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                .voice-icon {
                    font-size: 32px;
                    color: #a0aec0;
                }
                .voice-ring.recording .voice-icon { color: #48bb78; }
                .voice-ring.processing .voice-icon { color: #4299e1; }
                .voice-ring.error .voice-icon { color: #f56565; }
                .voice-status {
                    text-align: center;
                    color: #e2e8f0;
                    font-size: 14px;
                    margin-bottom: 12px;
                }
                .voice-transcript {
                    background: rgba(255,255,255,0.05);
                    border-radius: 8px;
                    padding: 12px;
                    color: #e2e8f0;
                    font-size: 13px;
                    min-height: 40px;
                }
                .voice-response {
                    margin-top: 8px;
                    padding-top: 8px;
                    border-top: 1px solid rgba(255,255,255,0.1);
                    color: #48bb78;
                    font-size: 13px;
                }
            """
        },
        "card": {
            "type": "entities",
            "entities": [
                {
                    "type": "custom:html-template-row",
                    "title": "",
                    "template": """
                        <div class="voice-widget">
                            <div class="voice-ring" id="voice_ring">
                                <span class="voice-icon">🎤</span>
                            </div>
                            <div class="voice-status" id="voice_status">Halte zum Sprechen</div>
                            <div class="voice-transcript" id="voice_transcript">
                                <span style="color:#718096">Dein Befehl erscheint hier...</span>
                            </div>
                            <div class="voice-response" id="voice_response" style="display:none"></div>
                        </div>
                        <script>
                            // Voice Pipeline Integration
                            window.VoiceWidget = (function() {
                                var state = 'idle'; // idle, recording, processing, done, error
                                var mediaRecorder = null;
                                var audioChunks = [];

                                function setState(newState) {
                                    state = newState;
                                    var ring = document.getElementById('voice_ring');
                                    var status = document.getElementById('voice_status');
                                    ring.className = 'voice-ring ' + state;
                                    var labels = {
                                        idle: 'Halte zum Sprechen',
                                        recording: 'Sprich jetzt...',
                                        processing: 'Verarbeite...',
                                        done: 'Fertig!',
                                        error: 'Fehler'
                                    };
                                    status.textContent = labels[state] || state;
                                }

                                function startRecording() {
                                    if (state !== 'idle') return;
                                    audioChunks = [];
                                    navigator.mediaDevices.getUserMedia({audio: true})
                                        .then(function(stream) {
                                            mediaRecorder = new MediaRecorder(stream);
                                            mediaRecorder.ondataavailable = function(e) {
                                                audioChunks.push(e.data);
                                            };
                                            mediaRecorder.onstop = sendToPipeline;
                                            mediaRecorder.start();
                                            setState('recording');
                                        })
                                        .catch(function(err) {
                                            console.error('Mic access denied:', err);
                                            setState('error');
                                        });
                                }

                                function stopRecording() {
                                    if (state !== 'recording' || !mediaRecorder) return;
                                    mediaRecorder.stop();
                                    mediaRecorder.stream.getTracks().forEach(function(t) {t.stop();});
                                    setState('processing');
                                }

                                function sendToPipeline() {
                                    var blob = new Blob(audioChunks, {type: 'audio/webm'});
                                    var reader = new FileReader();
                                    reader.onloadend = function() {
                                        var base64 = reader.result.split(',')[1];
                                        // Call HA API → Core voice pipeline
                                        fetch('/api/copilot/voice/process', {
                                            method: 'POST',
                                            headers: {'Content-Type': 'application/json'},
                                            body: JSON.stringify({audio: base64, language: 'de'})
                                        })
                                        .then(function(r) { return r.json(); })
                                        .then(function(data) {
                                            document.getElementById('voice_transcript').textContent = data.transcript || '';
                                            var respEl = document.getElementById('voice_response');
                                            if (data.response) {
                                                respEl.textContent = data.response;
                                                respEl.style.display = 'block';
                                            }
                                            setState('done');
                                            setTimeout(setState, 3000, 'idle');
                                        })
                                        .catch(function() {
                                            setState('error');
                                            setTimeout(setState, 3000, 'idle');
                                        });
                                    };
                                    reader.readAsDataURL(blob);
                                }

                                // Wire up events
                                document.addEventListener('DOMContentLoaded', function() {
                                    var ring = document.getElementById('voice_ring');
                                    if (ring) {
                                        ring.addEventListener('mousedown', startRecording);
                                        ring.addEventListener('mouseup', stopRecording);
                                        ring.addEventListener('touchstart', startRecording);
                                        ring.addEventListener('touchend', stopRecording);
                                    }
                                });

                                return { startRecording, stopRecording, setState };
                            })();
                        </script>
                    """
                }
            ]
        }
    }


# ─── Voice Command History Card ──────────────────────────────────────────────


def voice_command_history_card(max_items: int = 10) -> Dict[str, Any]:
    """Card showing last N voice commands and responses."""
    return {
        "type": "entities",
        "title": "🗣️ Sprachbefehle",
        "entities": [
            {
                "entity": "sensor.pilotsuite_voice_command_history",
                "type": "custom:tooltip",
                "content": """
                    {% if states('sensor.pilotsuite_voice_command_history') != 'unknown' %}
                    {% set history = state_attr('sensor.pilotsuite_voice_command_history', 'commands') or [] %}
                    <div style="max-height:300px;overflow-y:auto;">
                    {% for cmd in history[:10] %}
                        <div style="margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.1);">
                            <div style="color:#e2e8f0;font-size:13px;">🎤 {{ cmd.transcript }}</div>
                            <div style="color:#48bb78;font-size:12px;margin-top:4px;">
                                {% if cmd.response %}{{ cmd.response }}{% else %}{{ cmd.intent }}{% endif %}
                            </div>
                            <div style="color:#718096;font-size:11px;margin-top:2px;">
                                {{ cmd.timestamp.strftime('%H:%M') if cmd.timestamp else '' }}
                            </div>
                        </div>
                    {% endfor %}
                    </div>
                    {% else %}
                    <div style="color:#718096">Noch keine Sprachbefehle</div>
                    {% endif %}
                """
            }
        ]
    }


# ─── Voice Status Card ───────────────────────────────────────────────────────


def voice_status_card() -> Dict[str, Any]:
    """Card showing STT/TTS/Pipeline status."""
    return {
        "type": "vertical-stack",
        "cards": [
            {
                "type": "entity",
                "entity": "sensor.pilotsuite_voice_stt_status",
                "name": "STT Engine",
                "icon": "mdi:mic",
            },
            {
                "type": "entity",
                "entity": "sensor.pilotsuite_voice_tts_status",
                "name": "TTS Engine",
                "icon": "mdi:volume-high",
            },
            {
                "type": "entity",
                "entity": "sensor.pilotsuite_voice_pipeline_status",
                "name": "Pipeline",
                "icon": "mdi:audio-video",
            },
            {
                "type": "entity",
                "entity": "sensor.pilotsuite_voice_commands_today",
                "name": "Befehle heute",
                "icon": "mdi:counter",
            },
        ]
    }


# ─── Voice Pipeline Dashboard Card ───────────────────────────────────────────


def voice_pipeline_dashboard_card() -> Dict[str, Any]:
    """Full voice pipeline dashboard card.

    Shows: waveform, last transcript, last response, stats.
    """
    return {
        "type": "custom:mod-card",
        "card_mod": {
            "style": """
                ha-card {
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    border-radius: 16px;
                    padding: 16px;
                }
            """
        },
        "card": {
            "type": "vertical-stack",
            "cards": [
                {
                    "type": "custom:html-template-row",
                    "title": "",
                    "template": """
                        <div style="text-align:center;margin-bottom:16px;">
                            <div id="vp_waveform" style="height:60px;display:flex;align-items:center;justify-content:center;gap:3px;">
                                {% for i in range(20) %}
                                <div class="vp_bar" style="width:4px;background:#4a5568;border-radius:2px;transition:height 0.1s;"></div>
                                {% endfor %}
                            </div>
                            <script>
                                // Animated waveform bars
                                (function() {
                                    var bars = document.querySelectorAll('.vp_bar');
                                    let idx = 0;
                                    setInterval(function() {
                                        bars.forEach(function(bar, i) {
                                            var h = Math.random() * 40 + 10;
                                            bar.style.height = h + 'px';
                                            bar.style.background = bar.style.background || '#48bb78';
                                        });
                                    }, 150);
                                })();
                            </script>
                        </div>
                        <style>
                            .vp_bar.recording { background: #48bb78 !important; }
                            .vp_bar.processing { background: #4299e1 !important; }
                        </style>
                    """
                },
                voice_waveform_card()["card"],
                {
                    "type": "entity",
                    "entity": "sensor.pilotsuite_voice_last_command",
                    "name": "Letzter Befehl",
                },
                {
                    "type": "entity",
                    "entity": "sensor.pilotsuite_voice_last_response",
                    "name": "Antwort",
                },
                {
                    "type": "statistics-graph",
                    "entities": ["sensor.pilotsuite_voice_commands_today"],
                    "days_to_show": 7,
                    "title": "Befehle / Tag",
                },
            ]
        }
    }


# ─── Registration ────────────────────────────────────────────────────────────


def register_voice_cards() -> Dict[str, Dict[str, Any]]:
    """Register all voice cards. Called by register_cards()."""
    return {
        "voice-waveform": voice_waveform_card,
        "voice-command-history": voice_command_history_card,
        "voice-status": voice_status_card,
        "voice-pipeline-dashboard": voice_pipeline_dashboard_card,
    }
