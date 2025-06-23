import os
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from src.utils.logging_utils import setup_logging, log_operation
from src.utils.file_utils import (
    create_directory_if_not_exists,
    save_text_file,
    get_file_size
)
from .config import config
from src.utils.api_keys import ELEVENLABS_API_KEY  # Import API key

# Initialize logging
logger = setup_logging("voice_generator")

class TTSClient:
    """Wrapper class for TTS API calls"""
    
    def __init__(self):
        self.api_key = ELEVENLABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
        self.timeout = config.timeout_seconds
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
    def generate_audio(
        self,
        text: str,
        voice_id: str = None,
        model_id: str = None,
        stability: float = None,
        similarity_boost: float = None
    ) -> Optional[bytes]:
        """
        Generate audio using TTS API
        
        Args:
            text: Text to convert to speech
            voice_id: Voice to use
            model_id: Model to use
            stability: Voice stability setting
            similarity_boost: Similarity boost setting
            
        Returns:
            bytes: Audio data in MP3 format, or None if failed
        """
        if not voice_id:
            voice_id = config.default_voice_id
        if not model_id:
            model_id = config.default_model
            
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability or 0.5,
                "similarity_boost": similarity_boost or 0.75
            }
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS API request failed: {str(e)}")
            return None

class VoiceGenerator:
    """Core class for generating voiceovers and subtitles"""
    
    def __init__(self):
        self.tts_client = TTSClient()
        create_directory_if_not_exists(config.output_dir)
        create_directory_if_not_exists(config.subtitle_dir)
        logger.info("Voice Generator initialized")
        
    def generate_voiceover(
        self,
        script_text: str,
        voice_profile: str = None,
        output_mp3_path: str = None,
        **kwargs
    ) -> Optional[Path]:
        """
        Generate voiceover audio from script text
        
        Args:
            script_text: Text to convert to speech
            voice_profile: Name of voice profile to use
            output_mp3_path: Custom output path
            **kwargs: Additional TTS parameters
            
        Returns:
            Path: Path to generated MP3 file, or None if failed
        """
        start_time = time.time()
        log_operation(logger, "generate_voiceover", "started", 
                     {"voice_profile": voice_profile or "default"})
        
        try:
            # Get voice settings
            voice_settings = {}
            if voice_profile and voice_profile in config.voice_profiles:
                voice_settings = config.voice_profiles[voice_profile]
            else:
                voice_settings = {
                    "voice_id": config.default_voice_id,
                    "model": config.default_model
                }
            
            # Generate output path if not provided
            if not output_mp3_path:
                timestamp = int(time.time())
                output_mp3_path = config.output_dir / f"voiceover_{timestamp}.mp3"
            else:
                output_mp3_path = Path(output_mp3_path)
            
            # Generate audio
            audio_data = None
            for attempt in range(config.max_retries):
                audio_data = self.tts_client.generate_audio(
                    text=script_text,
                    voice_id=voice_settings.get("voice_id"),
                    model_id=voice_settings.get("model"),
                    stability=voice_settings.get("stability"),
                    similarity_boost=voice_settings.get("similarity_boost"),
                    **kwargs
                )
                if audio_data:
                    break
                time.sleep(config.retry_delay)
            
            if not audio_data:
                raise RuntimeError("Failed to generate audio after retries")
            
            # Save audio file
            with open(output_mp3_path, 'wb') as f:
                f.write(audio_data)
            
            duration = time.time() - start_time
            file_size = get_file_size(output_mp3_path)
            
            log_operation(logger, "generate_voiceover", "completed", {
                "output_path": str(output_mp3_path),
                "duration_sec": duration,
                "file_size_bytes": file_size,
                "voice_settings": voice_settings
            })
            
            return output_mp3_path
            
        except Exception as e:
            log_operation(logger, "generate_voiceover", "failed", {
                "error": str(e),
                "voice_profile": voice_profile
            }, level="ERROR")
            return None

    def generate_subtitles(
        self,
        script_text: str,
        audio_file_path: str,
        output_srt_path: str = None
    ) -> Optional[Path]:
        """
        Generate subtitles for the voiceover
        
        Args:
            script_text: Original script text
            audio_file_path: Path to audio file
            output_srt_path: Custom output path
            
        Returns:
            Path: Path to generated SRT file, or None if failed
        """
        start_time = time.time()
        log_operation(logger, "generate_subtitles", "started", 
                     {"audio_file": audio_file_path})
        
        try:
            # In production, you would:
            # 1. Use TTS API word timings if available, or
            # 2. Run ASR on the generated audio to get timings
            # This is a simplified placeholder implementation
            
            # Generate output path if not provided
            if not output_srt_path:
                output_srt_path = Path(audio_file_path).with_suffix('.srt')
            else:
                output_srt_path = Path(output_srt_path)
            
            # Split text into subtitle lines
            lines = self._split_text_for_subtitles(script_text)
            
            # Generate dummy timings (in production, use actual word timings)
            subtitles = []
            start_time_sec = 0.0
            for i, line in enumerate(lines, 1):
                duration = min(
                    len(line) * 0.1,  # Rough estimate: 0.1s per character
                    config.max_line_duration
                )
                end_time_sec = start_time_sec + duration
                
                subtitles.append(
                    self._format_srt_block(
                        index=i,
                        start_time=start_time_sec,
                        end_time=end_time_sec,
                        text=line
                    )
                )
                start_time_sec = end_time_sec + 0.1  # Small gap between lines
            
            # Save SRT file
            srt_content = "\n\n".join(subtitles)
            save_text_file(srt_content, output_srt_path)
            
            duration = time.time() - start_time
            log_operation(logger, "generate_subtitles", "completed", {
                "output_path": str(output_srt_path),
                "duration_sec": duration,
                "subtitle_count": len(subtitles)
            })
            
            return output_srt_path
            
        except Exception as e:
            log_operation(logger, "generate_subtitles", "failed", {
                "error": str(e),
                "audio_file": audio_file_path
            }, level="ERROR")
            return None

    def _split_text_for_subtitles(self, text: str) -> list[str]:
        """Split text into appropriate lines for subtitles"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            if len(' '.join(current_line + [word])) <= config.max_line_length:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines

    def _format_srt_block(
        self,
        index: int,
        start_time: float,
        end_time: float,
        text: str
    ) -> str:
        """Format a single SRT block"""
        def format_time(seconds: float) -> str:
            """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')
        
        return (
            f"{index}\n"
            f"{format_time(start_time)} --> {format_time(end_time)}\n"
            f"{text}"
        )

    def process_script(
        self,
        script_json: Dict[str, Any],
        voice_profile: str = None
    ) -> Dict[str, Optional[Path]]:
        """
        Process script to generate both voiceover and subtitles
        
        Args:
            script_json: Structured script data
            voice_profile: Voice profile to use
            
        Returns:
            dict: Paths to generated files (voiceover and subtitles)
        """
        script_text = script_json.get("script", "")
        source_name = Path(script_json.get("metadata", {}).get("source", {}).get("source", "unknown")).stem
        
        # Generate voiceover
        voiceover_path = config.output_dir / f"{source_name}_voiceover.mp3"
        voice_result = self.generate_voiceover(
            script_text=script_text,
            voice_profile=voice_profile,
            output_mp3_path=voiceover_path
        )
        
        # Generate subtitles
        subtitle_path = None
        if voice_result:
            subtitle_path = config.subtitle_dir / f"{source_name}_subtitles.srt"
            self.generate_subtitles(
                script_text=script_text,
                audio_file_path=voiceover_path,
                output_srt_path=subtitle_path
            )
        
        return {
            "voiceover": voiceover_path if voice_result else None,
            "subtitles": subtitle_path
        }
