import os
from pathlib import Path
from typing import Dict, List, Any
from src.utils.file_utils import load_json_file

# Load main configuration
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "main_config.json"
_main_config = load_json_file(_CONFIG_PATH)

class TechnicianConfig:
    """Configuration for the Technician Agent module"""
    
    def __init__(self):
        # Paths from main config
        self.base_data_path = Path(_main_config["base_settings"]["base_data_path"])
        self.log_dir = self.base_data_path / "logs"
        self.qc_report_dir = self.base_data_path / "qc_reports"
        self.diagnostic_dir = self.base_data_path / "diagnostics"
        
        # Thresholds
        self.error_threshold = 3  # Min errors to flag
        self.warning_threshold = 10
        self.performance_threshold = 5.0  # Seconds
        
        # Module alternatives
        self.tool_alternatives = {
            "pytesseract": ["google-cloud-vision", "easyocr", "paddleocr"],
            "ffmpeg": ["opencv", "moviepy"],
            "manim": ["blender", "after-effects-api"],
            "whisper": ["google-speech-to-text", "azure-speech"]
        }
        
        # Performance benchmarks
        self.expected_timings = {
            "ingestion": 30.0,
            "script_generation": 60.0,
            "animation": 120.0,
            "voice_generation": 30.0,
            "video_composition": 60.0
        }
        
        # Hardware recommendations
        self.hardware_requirements = {
            "min_ram": 8,  # GB
            "min_cpu_cores": 4,
            "gpu_recommended": True
        }
        
        # Ensure directories exist
        self.diagnostic_dir.mkdir(parents=True, exist_ok=True)

# Singleton config instance
config = TechnicianConfig()
