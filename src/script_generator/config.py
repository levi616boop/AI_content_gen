import os
from pathlib import Path
from typing import Dict, Any
from src.utils.file_utils import load_json_file

# Load main configuration
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "main_config.json"
_main_config = load_json_file(_CONFIG_PATH)

class ScriptGeneratorConfig:
    """Configuration for the Script Generator module"""
    
    def __init__(self):
        # Paths from main config
        self.base_data_path = Path(_main_config["base_settings"]["base_data_path"])
        self.input_dir = self.base_data_path / _main_config["paths"]["ingestion_output_dir"]
        self.output_dir = self.base_data_path / _main_config["paths"]["script_output_dir"]
        self.prompt_dir = Path(__file__).parent / "prompts"
        
        # LLM settings from main config
        llm_config = _main_config["module_specific"]["script_generator"]
        self.llm_model = llm_config["llm_model"]
        self.temperature = llm_config["temperature"]
        self.max_tokens = 2000
        self.timeout_seconds = 30
        
        # Script generation settings
        self.default_language = "English"
        self.default_tone = "informative"
        self.min_script_words = 200
        self.max_retries = 3
        self.retry_delay = 5

# Singleton config instance
config = ScriptGeneratorConfig()
