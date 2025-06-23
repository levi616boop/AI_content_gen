import os
from pathlib import Path
from typing import Dict, Any
from src.utils.file_utils import load_json_file

# Load main configuration
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "main_config.json"
_main_config = load_json_file(_CONFIG_PATH)

class VoiceGeneratorConfig:
    """Configuration for the Voice Generator module"""
    
    def __init__(self):
        # Paths from main config
        self.base_data_path = Path(_main_config["base_settings"]["base_data_path"])
        self.input_dir = self.base_data_path / _main_config["paths"]["script_output_dir"]
        self.output_dir = self.base_data_path / _main_config["paths"]["voice_output_dir"]
        self.subtitle_dir = self.base_data_path / _main_config["paths"]["subtitle_dir"]
        
        # Voice settings
        self.default_voice_id = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs default voice
        self.default_model = "eleven_monolingual_v2"
        self.sample_rate = 44100
        self.bitrate = "192k"
        
        # Subtitle settings
        self.subtitle_format = "srt"
        self.max_line_length = 42  # Characters per subtitle line
        self.max_line_duration = 3.0  # Seconds per subtitle
        
        # API settings
        self.timeout_seconds = 30
        self.max_retries = 3
        self.retry_delay = 2
        
        # Voice profiles (voice_id: description)
        self.voice_profiles = {
            "professional_male": {
                "voice_id": "21m00Tcm4TlvDq8ikWAM",
                "model": "eleven_monolingual_v2",
                "stability": 0.5,
                "similarity_boost": 0.75
            },
            "friendly_female": {
                "voice_id": "EXAVITQu4vr4xnSDxMaL",
                "model": "eleven_monolingual_v2",
                "stability": 0.4,
                "similarity_boost": 0.85
            },
            "narrator": {
                "voice_id": "AZnzlk1XvdvUeBnXmlld",
                "model": "eleven_monolingual_v2",
                "stability": 0.6,
                "similarity_boost": 0.7
            }
        }

# Singleton config instance
config = VoiceGeneratorConfig()
