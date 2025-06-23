import os
import time
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.utils.logging_utils import setup_logging, log_operation
from src.utils.file_utils import (
    create_directory_if_not_exists,
    get_file_size,
    get_file_duration
)
from .config import config
from src.utils.api_keys import (
    YOUTUBE_API_KEY,
    YOUTUBE_CLIENT_SECRETS,
    TIKTOK_API_KEY,
    INSTAGRAM_API_KEY
)

# Initialize logging
logger = setup_logging("uploader")

class Uploader:
    """Core class for uploading videos to multiple platforms"""
    
    def __init__(self):
        create_directory_if_not_exists(config.log_dir)
        self.youtube_service = None
        logger.info("Uploader initialized")
        
    def _get_youtube_service(self):
        """Initialize YouTube API service with OAuth"""
        if self.youtube_service:
            return self.youtube_service
            
        try:
            # Note: In production, you would store and reuse credentials
            flow = InstalledAppFlow.from_client_secrets_file(
                YOUTUBE_CLIENT_SECRETS,
                scopes=["https://www.googleapis.com/auth/youtube.upload"]
            )
            credentials = flow.run_local_server(port=8080)
            self.youtube_service = build(
                "youtube",
                "v3",
                credentials=credentials,
                cache_discovery=False
            )
            return self.youtube_service
        except Exception as e:
            logger.error(f"YouTube OAuth failed: {str(e)}")
            return None
    
    def _generate_metadata(self, platform: str, script_json: Dict[str, Any]) -> Dict[str, Any]:
        """Generate platform-specific metadata from script"""
        template = config.metadata_templates.get(platform, {})
        content_attrs = script_json.get("metadata", {}).get("content_attributes", {})
        
        metadata = {}
        for key, value in template.items():
            if isinstance(value, str):
                metadata[key] = value.format(
                    topic=content_attrs.get("topic", "Educational Content"),
                    summary=content_attrs.get("summary", "Automatically generated educational content"),
                    keywords=", ".join(content_attrs.get("keywords", []))
                )
            else:
                metadata[key] = value
                
        return metadata
    
    def _retry_upload(self, platform: str, func, *args, **kwargs) -> Optional[Dict[str, Any]]:
        """Wrapper for retry logic with exponential backoff"""
        max_retries = config.platforms[platform]["max_retries"]
        base_delay = config.platforms[platform]["retry_delay"]
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Upload attempt {attempt + 1} failed for {platform}. "
                    f"Retrying in {delay} seconds. Error: {str(e)}"
                )
                time.sleep(delay)
    
    def upload_to_youtube(
        self,
        video_path: Path,
        script_json: Dict[str, Any],
        category_id: str = None,
        tags: list = None,
        privacy_status: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Upload video to YouTube
        
        Args:
            video_path: Path to video file
            script_json: Script data for metadata
            category_id: YouTube category ID
            tags: List of tags
            privacy_status: 'public', 'private', or 'unlisted'
            
        Returns:
            dict: YouTube API response, or None if failed
        """
        start_time = time.time()
        log_operation(logger, "upload_to_youtube", "started", {"video": str(video_path)})
        
        try:
            # Get YouTube service
            youtube = self._get_youtube_service()
            if not youtube:
                raise RuntimeError("Could not initialize YouTube service")
            
            # Generate metadata
            metadata = self._generate_metadata("youtube", script_json)
            if not category_id:
                category_id = config.platforms["youtube"]["default_category"]
            if not privacy_status:
                privacy_status = config.platforms["youtube"]["default_privacy"]
            if not tags:
                tags = metadata.get("tags", [])
            
            # Prepare request body
            body = {
                "snippet": {
                    "title": metadata["title"],
                    "description": metadata["description"],
                    "tags": tags,
                    "categoryId": category_id
                },
                "status": {
                    "privacyStatus": privacy_status
                }
            }
            
            # Create media upload
            media = MediaFileUpload(
                str(video_path),
                chunksize=config.platforms["youtube"]["chunk_size"],
                resumable=True
            )
            
            # Execute upload with retry
            def _upload():
                return youtube.videos().insert(
                    part=",".join(body.keys()),
                    body=body,
                    media_body=media
                ).execute()
            
            response = self._retry_upload("youtube", _upload)
            
            duration = time.time() - start_time
            log_operation(logger, "upload_to_youtube", "completed", {
                "video": str(video_path),
                "video_id": response.get("id"),
                "duration_sec": duration
            })
            
            return response
            
        except Exception as e:
            log_operation(logger, "upload_to_youtube", "failed", {
                "error": str(e),
                "video": str(video_path)
            }, level="ERROR")
            return None
    
    def upload_to_tiktok(
        self,
        video_path: Path,
        script_json: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Upload video to TikTok
        
        Args:
            video_path: Path to video file
            script_json: Script data for metadata
            
        Returns:
            dict: TikTok API response, or None if failed
        """
        start_time = time.time()
        log_operation(logger, "upload_to_tiktok", "started", {"video": str(video_path)})
        
        try:
            # Generate metadata
            metadata = self._generate_metadata("tiktok", script_json)
            
            # In production, you would use the actual TikTok API
            # This is a placeholder implementation
            logger.info(f"Would upload to TikTok with title: {metadata['title']}")
            
            # Simulate API call with retry
            def _upload():
                # Simulate API response
                return {
                    "status": "success",
                    "video_id": "simulated_tiktok_id",
                    "share_url": "https://tiktok.com/@autoed/video/simulated"
                }
            
            response = self._retry_upload("tiktok", _upload)
            
            duration = time.time() - start_time
            log_operation(logger, "upload_to_tiktok", "completed", {
                "video": str(video_path),
                "duration_sec": duration
            })
            
            return response
            
        except Exception as e:
            log_operation(logger, "upload_to_tiktok", "failed", {
                "error": str(e),
                "video": str(video_path)
            }, level="ERROR")
            return None
    
    def upload_to_instagram_reels(
        self,
        video_path: Path,
        script_json: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Upload video to Instagram Reels
        
        Args:
            video_path: Path to video file
            script_json: Script data for metadata
            
        Returns:
            dict: Instagram API response, or None if failed
        """
        start_time = time.time()
        log_operation(logger, "upload_to_instagram", "started", {"video": str(video_path)})
        
        try:
            # Check duration limit
            duration = get_file_duration(video_path)
            if duration and duration > config.platforms["instagram"]["max_duration"]:
                raise ValueError(f"Video exceeds Instagram max duration of {config.platforms['instagram']['max_duration']}s")
            
            # Generate metadata
            metadata = self._generate_metadata("instagram", script_json)
            
            # In production, you would use the Instagram Graph API
            # This is a placeholder implementation
            logger.info(f"Would upload to Instagram with caption: {metadata['caption']}")
            
            # Simulate API call with retry
            def _upload():
                # Simulate API response
                return {
                    "status": "success",
                    "id": "simulated_ig_id",
                    "permalink": "https://instagram.com/reel/simulated"
                }
            
            response = self._retry_upload("instagram", _upload)
            
            duration = time.time() - start_time
            log_operation(logger, "upload_to_instagram", "completed", {
                "video": str(video_path),
                "duration_sec": duration
            })
            
            return response
            
        except Exception as e:
            log_operation(logger, "upload_to_instagram", "failed", {
                "error": str(e),
                "video": str(video_path)
            }, level="ERROR")
            return None
    
    def upload_all_platforms(
        self,
        video_path: Path,
        script_json: Dict[str, Any],
        platforms: list = None
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Upload video to all configured platforms
        
        Args:
            video_path: Path to video file
            script_json: Script data for metadata
            platforms: List of platforms to upload to (default: all)
            
        Returns:
            dict: Results from each platform's upload
        """
        if not platforms:
            platforms = ["youtube", "tiktok", "instagram"]
            
        results = {}
        for platform in platforms:
            if platform == "youtube":
                results["youtube"] = self.upload_to_youtube(video_path, script_json)
            elif platform == "tiktok":
                results["tiktok"] = self.upload_to_tiktok(video_path, script_json)
            elif platform == "instagram":
                results["instagram"] = self.upload_to_instagram_reels(video_path, script_json)
            else:
                logger.warning(f"Unknown platform: {platform}")
                results[platform] = None
                
        return results
