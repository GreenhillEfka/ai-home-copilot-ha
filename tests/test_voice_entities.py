"""Tests for PilotSuite STT and TTS voice entities.

Tests that don't require homeassistant imports: manifest, platform list,
and PCM-to-WAV conversion logic.
"""

import io
import json
import wave
import pytest
from pathlib import Path
from unittest.mock import Mock


class TestManifest:
    """Tests for manifest.json updates."""

    def test_manifest_has_stt_dependency(self):
        manifest_path = Path(__file__).parent.parent / "custom_components" / "copilot_ha" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        assert "stt" in manifest["dependencies"]
        assert "tts" in manifest["dependencies"]

    def test_manifest_has_conversation_dependency(self):
        manifest_path = Path(__file__).parent.parent / "custom_components" / "copilot_ha" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        assert "conversation" in manifest["dependencies"]

    def test_manifest_has_assist_after_dep(self):
        manifest_path = Path(__file__).parent.parent / "custom_components" / "copilot_ha" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        assert "assist_pipeline" in manifest["after_dependencies"]


class TestPCMToWAV:
    """Test PCM to WAV conversion (no HA imports needed)."""

    def test_pcm_to_wav_valid_output(self):
        """PCM to WAV conversion produces valid WAV header."""
        pcm = b"\x00\x01" * 8000  # 1 second of 16kHz mono 16-bit
        sample_rate = 16000
        channels = 1
        sample_width = 2  # 16-bit

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm)
        wav_data = buf.getvalue()

        # Verify it's valid WAV
        verify_buf = io.BytesIO(wav_data)
        with wave.open(verify_buf, "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 16000
            assert wf.getnframes() == 8000

    def test_pcm_to_wav_starts_with_riff(self):
        """WAV output starts with RIFF header."""
        pcm = b"\x00" * 100
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(pcm)
        assert buf.getvalue()[:4] == b"RIFF"


class TestSTTFileStructure:
    """Test stt.py file exists and has expected structure."""

    def test_stt_file_exists(self):
        stt_path = Path(__file__).parent.parent / "custom_components" / "copilot_ha" / "stt.py"
        assert stt_path.exists()

    def test_stt_has_setup_entry(self):
        stt_path = Path(__file__).parent.parent / "custom_components" / "copilot_ha" / "stt.py"
        content = stt_path.read_text()
        assert "async_setup_entry" in content
        assert "PilotSuiteSTTEntity" in content
        assert "SpeechToTextEntity" in content
        assert "async_process_audio_stream" in content

    def test_stt_supports_wav(self):
        stt_path = Path(__file__).parent.parent / "custom_components" / "copilot_ha" / "stt.py"
        content = stt_path.read_text()
        assert "AudioFormats.WAV" in content
        assert "AudioCodecs.PCM" in content


class TestTTSFileStructure:
    """Test tts.py file exists and has expected structure."""

    def test_tts_file_exists(self):
        tts_path = Path(__file__).parent.parent / "custom_components" / "copilot_ha" / "tts.py"
        assert tts_path.exists()

    def test_tts_has_setup_entry(self):
        tts_path = Path(__file__).parent.parent / "custom_components" / "copilot_ha" / "tts.py"
        content = tts_path.read_text()
        assert "async_setup_entry" in content
        assert "PilotSuiteTTSEntity" in content
        assert "TextToSpeechEntity" in content
        assert "async_get_tts_audio" in content

    def test_tts_has_voices(self):
        tts_path = Path(__file__).parent.parent / "custom_components" / "copilot_ha" / "tts.py"
        content = tts_path.read_text()
        assert "de-DE-ConradNeural" in content
        assert "en-US-GuyNeural" in content
        assert "async_get_supported_voices" in content

    def test_tts_returns_mp3(self):
        tts_path = Path(__file__).parent.parent / "custom_components" / "copilot_ha" / "tts.py"
        content = tts_path.read_text()
        assert '"mp3"' in content


class TestLegacyPlatforms:
    """Test legacy module platform list includes STT/TTS."""

    def test_platforms_in_legacy_file(self):
        legacy_path = (
            Path(__file__).parent.parent
            / "custom_components"
            / "copilot_ha"
            / "core"
            / "modules"
            / "legacy.py"
        )
        content = legacy_path.read_text()
        assert '"stt"' in content
        assert '"tts"' in content


class TestCoordinatorVoiceMethods:
    """Test coordinator has voice methods (file-level check)."""

    def test_coordinator_has_voice_methods(self):
        coord_path = (
            Path(__file__).parent.parent
            / "custom_components"
            / "copilot_ha"
            / "coordinator.py"
        )
        content = coord_path.read_text()
        assert "async_stt" in content
        assert "async_tts" in content
        assert "async_voice_status" in content

    def test_coordinator_stt_sends_audio(self):
        coord_path = (
            Path(__file__).parent.parent
            / "custom_components"
            / "copilot_ha"
            / "coordinator.py"
        )
        content = coord_path.read_text()
        assert "audio/wav" in content
        assert "/api/v1/styx/stt" in content

    def test_coordinator_tts_sends_json(self):
        coord_path = (
            Path(__file__).parent.parent
            / "custom_components"
            / "copilot_ha"
            / "coordinator.py"
        )
        content = coord_path.read_text()
        assert "/api/v1/styx/tts" in content
