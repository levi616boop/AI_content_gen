import os
import csv
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import pandas as pd
from src.utils.logging_utils import setup_logging, log_operation
from src.utils.file_utils import (
    create_directory_if_not_exists,
    save_json_file,
    load_json_file,
    file_exists_within_seconds
)
from .config import config
from src.utils.api_keys import TRENDING_API_KEY  # Import API key

# Initialize logging
logger = setup_logging("content_manager")

class ContentManager:
    """Strategic content planning and performance analysis module"""
    
    def __init__(self):
        create_directory_if_not_exists(config.performance_data_dir)
        self.performance_data = self._load_performance_data()
        self.schedule = self._load_schedule()
        logger.info("Content Manager initialized")
        
    def _load_performance_data(self) -> pd.DataFrame:
        """Load historical performance data"""
        try:
            if config.performance_csv.exists():
                return pd.read_csv(config.performance_csv)
            return pd.DataFrame(columns=[
                "topic", "platform", "upload_date", "views", 
                "likes", "watch_time_percentage", "qc_issues"
            ])
        except Exception as e:
            logger.error(f"Failed to load performance data: {str(e)}")
            return pd.DataFrame()
    
    def _load_schedule(self) -> Dict[str, Any]:
        """Load content schedule"""
        try:
            if config.schedule_file.exists():
                return load_json_file(config.schedule_file)
            return {"scheduled": [], "completed": []}
        except Exception as e:
            logger.error(f"Failed to load schedule: {str(e)}")
            return {"scheduled": [], "completed": []}
    
    def _get_trending_topics(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get trending topics either from cache or API
        
        Args:
            force_refresh: Whether to ignore cache and fetch fresh data
            
        Returns:
            dict: Trending topics data or None if failed
        """
        # Check cache first
        if not force_refresh and file_exists_within_seconds(config.trending_cache, config.trending_cache_ttl):
            try:
                return load_json_file(config.trending_cache)
            except Exception as e:
                logger.warning(f"Failed to load trending cache: {str(e)}")
        
        # Fetch from API
        try:
            headers = {"Authorization": f"Bearer {TRENDING_API_KEY}"}
            response = requests.get(
                f"{config.trending_api_url}/topics",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Save to cache
            save_json_file(data, config.trending_cache)
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch trending topics: {str(e)}")
            return None
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance data to identify successful patterns"""
        if self.performance_data.empty:
            return {}
            
        analysis = {
            "top_topics": [],
            "best_platforms": [],
            "success_patterns": {}
        }
        
        try:
            # Calculate success metric (simplified)
            self.performance_data["success_score"] = (
                self.performance_data["views"] / self.performance_data["views"].max() +
                self.performance_data["likes"] / self.performance_data["likes"].max() +
                self.performance_data["watch_time_percentage"]
            ) / 3
            
            # Get top performing topics
            top_topics = self.performance_data.sort_values(
                "success_score", ascending=False
            ).head(config.top_n_topics)["topic"].tolist()
            
            analysis["top_topics"] = top_topics
            
            # Get best platforms
            platform_scores = self.performance_data.groupby("platform")["success_score"].mean()
            analysis["best_platforms"] = platform_scores.sort_values(ascending=False).index.tolist()
            
            # Identify patterns (simplified example)
            analysis["success_patterns"] = {
                "optimal_duration": self.performance_data[
                    self.performance_data["success_score"] > 0.7
                ]["duration_seconds"].mean(),
                "best_upload_days": self.performance_data[
                    self.performance_data["success_score"] > 0.7
                ]["upload_day"].mode().tolist()
            }
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {str(e)}")
            
        return analysis
    
    def _generate_topic_suggestions(
        self,
        analysis: Dict[str, Any],
        trending_data: Optional[Dict[str, Any]] = None,
        num_suggestions: int = 3
    ) -> List[str]:
        """
        Generate topic suggestions using LLM (placeholder implementation)
        
        Args:
            analysis: Performance analysis results
            trending_data: Optional trending topics data
            num_suggestions: Number of suggestions to generate
            
        Returns:
            list: Suggested topics
        """
        # In production, this would call an LLM API with a well-crafted prompt
        # This is a simplified placeholder implementation
        
        prompt = f"""
Based on our successful educational content about {', '.join(analysis.get('top_topics', []))},
and trending topics in education ({trending_data.get('trending', []) if trending_data else 'none'}),
suggest {num_suggestions} new video topics that would perform well.

Consider our audience prefers content with:
- Optimal duration around {analysis.get('success_patterns', {}).get('optimal_duration', 300)} seconds
- Best posted on {', '.join(analysis.get('success_patterns', {}).get('best_upload_days', ['weekdays']))}
"""
        
        logger.debug(f"LLM prompt for topic generation:\n{prompt}")
        
        # Simulated LLM response
        suggestions = [
            "The Science Behind Climate Change - Simplified",
            "Mathematics in Everyday Life: Practical Applications",
            "History of Technology: From Wheel to AI"
        ]
        
        return suggestions[:num_suggestions]
    
    def load_past_upload_data(
        self,
        log_filepath: Path = None,
        qc_report_dir: Path = None
    ) -> bool:
        """
        Load and process historical upload and QC data
        
        Args:
            log_filepath: Path to uploader log
            qc_report_dir: Directory containing QC reports
            
        Returns:
            bool: True if successful, False otherwise
        """
        log_filepath = log_filepath or config.upload_log
        qc_report_dir = qc_report_dir or config.qc_report_dir
        
        try:
            # Parse upload logs (simplified example)
            upload_data = []
            with open(log_filepath, 'r') as f:
                for line in f:
                    if '"operation": "upload_to_' in line and '"status": "completed"' in line:
                        try:
                            log_entry = json.loads(line.split('|')[-1])
                            upload_data.append({
                                "platform": log_entry.get("platform"),
                                "video_id": log_entry.get("video_id"),
                                "timestamp": log_entry.get("timestamp"),
                                "duration_sec": log_entry.get("duration_sec")
                            })
                        except json.JSONDecodeError:
                            continue
            
            # Parse QC reports (simplified example)
            qc_data = {}
            for qc_file in qc_report_dir.glob("*.json"):
                try:
                    report = load_json_file(qc_file)
                    video_id = qc_file.stem.replace("_qc_report", "")
                    qc_data[video_id] = {
                        "issues": report.get("issues", []),
                        "score": report.get("score", 0)
                    }
                except Exception as e:
                    logger.warning(f"Failed to parse QC report {qc_file}: {str(e)}")
            
            # TODO: In production, would merge with existing performance data
            logger.info(f"Loaded {len(upload_data)} upload records and {len(qc_data)} QC reports")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load past upload data: {str(e)}")
            return False
    
    def suggest_next_topics(
        self,
        num_suggestions: int = None,
        trending_topics: List[str] = None,
        use_cached_trending: bool = True
    ) -> Dict[str, Any]:
        """
        Generate topic suggestions based on performance and trends
        
        Args:
            num_suggestions: Number of suggestions to generate
            trending_topics: Optional list of trending topics
            use_cached_trending: Whether to use cached trending data
            
        Returns:
            dict: Analysis results and suggestions
        """
        start_time = time.time()
        log_operation(logger, "suggest_next_topics", "started")
        
        try:
            num_suggestions = num_suggestions or config.top_n_topics
            
            # Get trending topics if not provided
            if trending_topics is None:
                trending_data = self._get_trending_topics(not use_cached_trending)
                trending_topics = trending_data.get("topics", []) if trending_data else []
            
            # Analyze performance
            analysis = self._analyze_performance()
            
            # Generate suggestions
            suggestions = self._generate_topic_suggestions(
                analysis,
                {"trending": trending_topics},
                num_suggestions
            )
            
            result = {
                "analysis": analysis,
                "trending_topics": trending_topics,
                "suggestions": suggestions,
                "generated_at": datetime.now().isoformat()
            }
            
            duration = time.time() - start_time
            log_operation(logger, "suggest_next_topics", "completed", {
                "num_suggestions": len(suggestions),
                "duration_sec": duration
            })
            
            return result
            
        except Exception as e:
            log_operation(logger, "suggest_next_topics", "failed", {
                "error": str(e)
            }, level="ERROR")
            return {
                "error": str(e),
                "suggestions": []
            }
    
    def schedule_new_upload(
        self,
        topic_suggestion: str,
        target_platforms: List[str] = None,
        preferred_time: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Add a new content piece to the schedule
        
        Args:
            topic_suggestion: Topic to schedule
            target_platforms: Platforms to target
            preferred_time: Preferred upload time
            
        Returns:
            dict: Scheduled entry or None if failed
        """
        start_time = time.time()
        log_operation(logger, "schedule_new_upload", "started", {
            "topic": topic_suggestion
        })
        
        try:
            if not target_platforms:
                target_platforms = config.default_schedule["platforms"]
                
            if not preferred_time:
                # Use best time for first platform
                platform = target_platforms[0]
                preferred_time = config.default_schedule["best_times"].get(platform, "Friday 15:00")
            
            # Create schedule entry
            entry = {
                "topic": topic_suggestion,
                "platforms": target_platforms,
                "scheduled_time": preferred_time,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "content_type": "educational_video",
                "priority": "normal"
            }
            
            # Add to schedule
            self.schedule["scheduled"].append(entry)
            
            # Save schedule
            save_json_file(self.schedule, config.schedule_file)
            
            duration = time.time() - start_time
            log_operation(logger, "schedule_new_upload", "completed", {
                "topic": topic_suggestion,
                "platforms": target_platforms,
                "duration_sec": duration
            })
            
            return entry
            
        except Exception as e:
            log_operation(logger, "schedule_new_upload", "failed", {
                "error": str(e),
                "topic": topic_suggestion
            }, level="ERROR")
            return None
    
    def update_performance_metrics(self) -> bool:
        """
        Update performance metrics from platform APIs
        
        Returns:
            bool: True if successful, False otherwise
        """
        start_time = time.time()
        log_operation(logger, "update_performance_metrics", "started")
        
        try:
            # Placeholder for actual API integration
            # In production, would:
            # 1. Fetch analytics from YouTube/TikTok/Instagram APIs
            # 2. Merge with existing performance data
            # 3. Save updated metrics
            
            logger.info("Performance metrics update simulated - would fetch from APIs")
            
            # Simulate some new data
            new_data = {
                "topic": "Introduction to Quantum Computing",
                "platform": "youtube",
                "upload_date": datetime.now().strftime("%Y-%m-%d"),
                "views": 1250,
                "likes": 87,
                "watch_time_percentage": 0.62,
                "qc_issues": []
            }
            
            # Append to performance data
            self.performance_data = pd.concat([
                self.performance_data,
                pd.DataFrame([new_data])
            ], ignore_index=True)
            
            # Save to CSV
            self.performance_data.to_csv(config.performance_csv, index=False)
            
            duration = time.time() - start_time
            log_operation(logger, "update_performance_metrics", "completed", {
                "new_records": 1,
                "duration_sec": duration
            })
            
            return True
            
        except Exception as e:
            log_operation(logger, "update_performance_metrics", "failed", {
                "error": str(e)
            }, level="ERROR")
            return False
