import os
import subprocess
import time
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from src.utils.logging_utils import setup_logging, log_operation
from src.utils.file_utils import (
    create_directory_if_not_exists,
    get_file_size
)
from .config import config

# Initialize logging
logger = setup_logging("video_composer")

class VideoComposer:
    """Core class for composing final videos from assets"""
    
    def __init__(self):
        create_directory_if_not_exists(config.output_dir)
        create_directory_if_not_exists(config.temp_dir)
        logger.info("Video Composer initialized")
        logger.info(f"Output directory: {config.output_dir}")
        logger.info(f"Target resolution: {config.resolution}")
        
    def _get_media_duration(self, file_path: Path) -> Optional[float]:
        """
        Get duration of a media file using ffprobe
        
        Args:
            file_path: Path to media file
            
        Returns:
            float: Duration in seconds, or None if failed
        """
        try:
            cmd = [
                config.ffprobe_path,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(file_path)
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return float(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get duration for {file_path}: {str(e)}")
            return None
        except ValueError:
            logger.error(f"Invalid duration output for {file_path}")
            return None
    
    def ensure_sync(self, video_path: Path, audio_path: Path) -> bool:
        """
        Check if video and audio durations are within tolerance
        
        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            
        Returns:
            bool: True if durations match within tolerance, False otherwise
        """
        video_duration = self._get_media_duration(video_path)
        audio_duration = self._get_media_duration(audio_path)
        
        if not video_duration or not audio_duration:
            return False
            
        duration_diff = abs(video_duration - audio_duration)
        if duration_diff > config.sync_tolerance:
            logger.warning(
                f"Audio/video duration mismatch: "
                f"video={video_duration:.2f}s, "
                f"audio={audio_duration:.2f}s, "
                f"diff={duration_diff:.2f}s"
            )
            return False
            
        logger.debug(
            f"Audio/video durations match: "
            f"video={video_duration:.2f}s, "
            f"audio={audio_duration:.2f}s"
        )
        return True
    
    def merge_assets(
        self,
        animation_mp4_path: Path,
        voice_mp3_path: Path,
        subtitles_srt_path: Optional[Path] = None,
        final_output_mp4_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Combine video, audio, and subtitles into final video
        
        Args:
            animation_mp4_path: Path to animation video
            voice_mp3_path: Path to voiceover audio
            subtitles_srt_path: Optional path to subtitles
            final_output_mp4_path: Optional custom output path
            
        Returns:
            Path: Path to generated video, or None if failed
        """
        start_time = time.time()
        log_operation(logger, "merge_assets", "started", {
            "animation": str(animation_mp4_path),
            "voiceover": str(voice_mp3_path),
            "subtitles": str(subtitles_srt_path) if subtitles_srt_path else None
        })
        
        try:
            # Validate inputs
            if not animation_mp4_path.exists():
                raise FileNotFoundError(f"Animation file not found: {animation_mp4_path}")
            if not voice_mp3_path.exists():
                raise FileNotFoundError(f"Voiceover file not found: {voice_mp3_path}")
            if subtitles_srt_path and not subtitles_srt_path.exists():
                raise FileNotFoundError(f"Subtitles file not found: {subtitles_srt_path}")
            
            # Check sync between audio and video
            self.ensure_sync(animation_mp4_path, voice_mp3_path)
            
            # Create output path if not provided
            if not final_output_mp4_path:
                source_name = animation_mp4_path.stem.replace("_animation", "")
                final_output_mp4_path = config.output_dir / f"{source_name}_final.mp4"
            else:
                final_output_mp4_path = Path(final_output_mp4_path)
            
            # Build ffmpeg command
            cmd = [
                config.ffmpeg_path,
                "-y",  # Overwrite output
                "-i", str(animation_mp4_path),
                "-i", str(voice_mp3_path),
            ]
            
            # Add subtitles if provided
            if subtitles_srt_path:
                cmd.extend([
                    "-vf", f"subtitles={str(subtitles_srt_path)}:force_style='Fontsize=24,PrimaryColour=&HFFFFFF&'"
                ])
            
            # Add encoding parameters
            cmd.extend([
                "-c:v", config.video_codec,
                "-b:v", config.video_bitrate,
                "-crf", str(config.crf),
                "-c:a", config.audio_codec,
                "-b:a", config.audio_bitrate,
                "-threads", str(config.threads),
                "-shortest",  # End at shortest input duration
                "-movflags", "+faststart",  # For streaming
                str(final_output_mp4_path)
            ])
            
            # Log the full command
            logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            
            # Run ffmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg failed with error: {result.stderr}")
                return None
            
            # Verify output
            if not final_output_mp4_path.exists():
                raise RuntimeError("Output file was not created")
            
            duration = time.time() - start_time
            file_size = get_file_size(final_output_mp4_path)
            output_duration = self._get_media_duration(final_output_mp4_path)
            
            log_operation(logger, "merge_assets", "completed", {
                "output_path": str(final_output_mp4_path),
                "duration_sec": duration,
                "file_size_bytes": file_size,
                "video_duration": output_duration
            })
            
            return final_output_mp4_path
            
        except Exception as e:
            log_operation(logger, "merge_assets", "failed", {
                "error": str(e),
                "animation": str(animation_mp4_path),
                "voiceover": str(voice_mp3_path)
            }, level="ERROR")
            return None
    
    def compose_video(
        self,
        script_json_path: Path,
        animation_path: Optional[Path] = None,
        voiceover_path: Optional[Path] = None,
        subtitles_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Complete video composition workflow
        
        Args:
            script_json_path: Path to script JSON file
            animation_path: Optional override for animation file
            voiceover_path: Optional override for voiceover file
            subtitles_path: Optional override for subtitles file
            
        Returns:
            Path: Path to final video, or None if failed
        """
        try:
            # Load script metadata
            with open(script_json_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            
            source_name = Path(script_data["metadata"]["source"]["source"]).stem
            
            # Determine input paths if not provided
            if not animation_path:
                animation_path = config.animation_dir / f"{source_name}_animation.mp4"
            if not voiceover_path:
                voiceover_path = config.voice_dir / f"{source_name}_voiceover.mp3"
            if not subtitles_path:
                subtitles_path = config.subtitle_dir / f"{source_name}_subtitles.srt"
            
            # Compose final video
            final_video_path = self.merge_assets(
                animation_mp4_path=animation_path,
                voice_mp3_path=voiceover_path,
                subtitles_srt_path=subtitles_path if subtitles_path.exists() else None
            )
            
            return final_video_path
            
        except Exception as e:
            logger.error(f"Video composition failed: {str(e)}")
            return None
