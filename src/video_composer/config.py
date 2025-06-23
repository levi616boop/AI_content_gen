import os
from pathlib import Path
from typing import Dict, Any
from src.utils.file_utils import load_json_file

# Load main configuration
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "main_config.json"
_main_config = load_json_file(_CONFIG_PATH)

class VideoComposerConfig:
    """Configuration for the Video Composer module"""
    
    def __init__(self):
        # Paths from main config
        self.base_data_path = Path(_main_config["base_settings"]["base_data_path"])
        self.animation_dir = self.base_data_path / _main_config["paths"]["animation_output_dir"]
        self.voice_dir = self.base_data_path / _main_config["paths"]["voice_output_dir"]
        self.subtitle_dir = self.base_data_path / _main_config["paths"]["subtitle_dir"]
        self.output_dir = self.base_data_path / _main_config["paths"]["final_videos_dir"]
        
        # Video settings from main config
        self.resolution = _main_config["module_specific"]["animator"]["output_resolution"]
        self.fps = _main_config["module_specific"]["animator"]["fps"]
        
        # Encoding settings
        self.video_codec = "libx264"
        self.audio_codec = "aac"
        self.video_bitrate = "8000k" if self.resolution == "4k" else "5000k" if self.resolution == "1080p" else "2500k"
        self.audio_bitrate = "192k"
        self.crf = 18  # Constant Rate Factor (lower = better quality)
        
        # FFmpeg settings
        self.ffmpeg_path = "ffmpeg"  # Assumes ffmpeg is in PATH
        self.ffprobe_path = "ffprobe"  # For duration checking
        self.threads = 2  # Number of threads for encoding
        
        # Sync tolerance (seconds)
        self.sync_tolerance = 0.5
        
        # Temporary files
        self.temp_dir = self.base_data_path / "temp"
        
        # Supported formats
        self.supported_video_formats = [".mp4", ".mov"]
        self.supported_audio_formats = [".mp3", ".wav"]
        self.supported_subtitle_formats = [".srt", ".vtt"]

# Singleton config instance
config = VideoComposerConfig()
