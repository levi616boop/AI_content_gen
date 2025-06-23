import os
from pathlib import Path
from typing import Dict, Any
from src.utils.file_utils import load_json_file

# Load main configuration
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "main_config.json"
_main_config = load_json_file(_CONFIG_PATH)

class ContentManagerConfig:
    """Configuration for the Content Manager module"""
    
    def __init__(self):
        # Paths from main config
        self.base_data_path = Path(_main_config["base_settings"]["base_data_path"])
        
        # Content management paths
        self.performance_data_dir = self.base_data_path / "content_metrics"
        self.schedule_file = self.base_data_path / "content_schedule.json"
        self.trending_cache = self.base_data_path / "trending_topics.json"
        
        # Default files
        self.upload_log = self.base_data_path / "logs" / "uploader.log"
        self.qc_report_dir = self.base_data_path / "qc_reports"
        self.performance_csv = self.performance_data_dir / "content_performance.csv"
        
        # Analysis parameters
        self.top_n_topics = 3
        self.min_views_for_success = 1000
        self.min_watch_percentage = 0.5  # 50% watch time
        
        # Trending API settings
        self.trending_api_url = "https://api.trendingtopics.example.com/v1"
        self.trending_cache_ttl = 86400  # 24 hours in seconds
        
        # Scheduling defaults
        self.default_schedule = {
            "platforms": ["youtube"],
            "frequency": "weekly",
            "best_times": {
                "youtube": "Tuesday 15:00",
                "tiktok": "Wednesday 19:00",
                "instagram": "Friday 12:00"
            }
        }
        
        # LLM settings
        self.llm_model = "gpt-4"
        self.llm_temperature = 0.7
        
        # Ensure directories exist
        self.performance_data_dir.mkdir(parents=True, exist_ok=True)
        self.qc_report_dir.mkdir(parents=True, exist_ok=True)

# Singleton config instance
config = ContentManagerConfig()
