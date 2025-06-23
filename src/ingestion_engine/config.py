import os
from pathlib import Path
from typing import Dict, Any
from src.utils.file_utils import load_json_file

# Load main configuration
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "main_config.json"
_main_config = load_json_file(_CONFIG_PATH)

class IngestionConfig:
    """Configuration for the Ingestion Engine module"""
    
    def __init__(self):
        # Paths from main config
        self.base_data_path = Path(_main_config["base_settings"]["base_data_path"])
        self.input_dir = self.base_data_path / "input"
        self.output_dir = self.base_data_path / _main_config["paths"]["ingestion_output_dir"]
        self.temp_dir = self.base_data_path / _main_config["paths"]["temp_dir"]
        
        # Module-specific settings
        self.max_file_size_mb = _main_config["module_specific"]["ingestion_engine"]["max_file_size_mb"]
        self.timeout_seconds = _main_config["module_specific"]["ingestion_engine"]["timeout_seconds"]
        
        # OCR settings
        self.ocr_language = "eng"  # Default language for pytesseract
        self.ocr_config = "--psm 6"  # Page segmentation mode
        
        # HTML scraping settings
        self.valid_content_tags = ["article", "section", "div"]
        self.min_content_length = 500  # Minimum chars to consider valid content

# Singleton config instance
config = IngestionConfig()
