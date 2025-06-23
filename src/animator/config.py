import os
from pathlib import Path
from typing import Dict, Any
from src.utils.file_utils import load_json_file

# Load main configuration
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "main_config.json"
_main_config = load_json_file(_CONFIG_PATH)

class AnimatorConfig:
    """Configuration for the Animator module"""
    
    def __init__(self):
        # Paths from main config
        self.base_data_path = Path(_main_config["base_settings"]["base_data_path"])
        self.input_dir = self.base_data_path / _main_config["paths"]["script_output_dir"]
        self.output_dir = self.base_data_path / _main_config["paths"]["animation_output_dir"]
        self.template_dir = Path(__file__).parent / "templates"
        
        # Animation settings from main config
        anim_config = _main_config["module_specific"]["animator"]
        self.resolution = anim_config["output_resolution"]  # e.g., "1080p"
        self.fps = anim_config["fps"]
        self.default_transition = anim_config["default_transition"]
        
        # Resolution mapping
        self.resolution_map = {
            "480p": (854, 480),
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "4k": (3840, 2160)
        }
        
        # Default durations (in seconds)
        self.scene_duration = 5
        self.transition_duration = 1
        
        # External tools paths
        self.ffmpeg_path = "ffmpeg"
        self.manim_path = "manim"

# Singleton config instance
config = AnimatorConfig()
