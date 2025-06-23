import os
from pathlib import Path
from typing import Dict, Any
from src.utils.file_utils import load_json_file

# Load main configuration
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "main_config.json"
_main_config = load_json_file(_CONFIG_PATH)

class QCConfig:
    """Configuration for the Quality Control module"""
    
    def __init__(self):
        # Paths from main config
        self.base_data_path = Path(_main_config["base_settings"]["base_data_path"])
        self.output_dir = self.base_data_path / "qc_reports"
        self.temp_dir = self.base_data_path / "temp"
        
        # LLM settings
        self.llm_models = {
            "script_review": "gpt-4",
            "visual_alignment": "gpt-4-vision-preview",  # Placeholder
            "general_qc": "gpt-4"
        }
        self.llm_temperature = 0.3  # Lower for more deterministic QC
        self.max_tokens = 2000
        
        # Thresholds
        self.grammar_error_threshold = 3  # Max allowed grammar issues
        self.pacing_tolerance = 0.2  # 20% speed variation allowed
        self.min_visual_sync_score = 0.7  # 0-1 scale
        self.warning_score_threshold = 3.5  # 1-5 scale
        
        # Review prompts
        self.prompt_dir = Path(__file__).parent / "prompts"
        self.script_review_prompt = "script_review_prompt.txt"
        self.visual_alignment_prompt = "visual_alignment_prompt.txt"  # Placeholder
        self.pacing_analysis_prompt = "pacing_analysis_prompt.txt"
        
        # ASR settings (placeholder for Whisper)
        self.asr_model = "base"  # small, medium, large
        self.asr_language = "en"
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

# Singleton config instance
config = QCConfig()
