import os
import time
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any
from src.utils.logging_utils import setup_logging, log_operation
from src.utils.file_utils import (
    create_directory_if_not_exists,
    save_text_file,
    save_json_file,
    load_json_file
)
from .config import config
from src.utils.api_keys import OPENAI_API_KEY  # Import API key

# Initialize logging
logger = setup_logging("script_generator")

class LLMClient:
    """Wrapper class for LLM API calls"""
    
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        self.timeout = config.timeout_seconds
        
    def generate_text(self, prompt: str, model: str, temperature: float) -> Optional[Dict[str, Any]]:
        """
        Make API call to LLM service
        """
        # Implementation note: In production, you would use the actual API client library
        # This is a simplified version showing the interface
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": config.max_tokens
        }
        
        try:
            # Simulating API call - replace with actual implementation
            logger.info(f"Calling LLM API with model {model}")
            
            # In real implementation:
            # response = requests.post(f"{self.base_url}/completions",
            #                       json=payload,
            #                       headers=headers,
            #                       timeout=self.timeout)
            # response.raise_for_status()
            # return response.json()
            
            # Simulated response for development
            return {
                "choices": [{
                    "text": "This is a simulated LLM response. In production, this would be the actual generated script.",
                    "finish_reason": "length",
                    "index": 0
                }],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": 150,
                    "total_tokens": len(prompt.split()) + 150
                }
            }
            
        except Exception as e:
            logger.error(f"LLM API call failed: {str(e)}")
            return None

class ScriptGenerator:
    """Core class for generating educational scripts from ingested content"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        create_directory_if_not_exists(config.output_dir)
        logger.info("Script Generator initialized")
        
    def _load_prompt_template(self) -> Optional[str]:
        """Load the prompt template from file"""
        prompt_file = config.prompt_dir / "educational_script_prompt.txt"
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load prompt template: {str(e)}")
            return None
    
    def _estimate_word_count(self, duration_seconds: int) -> int:
        """Estimate target word count based on duration"""
        words_per_minute = 150  # Average speaking rate for educational content
        return int((duration_seconds / 60) * words_per_minute)
    
    def _postprocess_script(self, raw_script: str) -> Dict[str, Any]:
        """Extract structured information from the generated script"""
        # Extract keywords
        keywords = []
        if "[KEYWORDS:" in raw_script:
            kw_match = re.search(r"\[KEYWORDS:(.*?)\]", raw_script)
            if kw_match:
                keywords = [k.strip() for k in kw_match.group(1).split(",")]
                raw_script = raw_script.replace(kw_match.group(0), "").strip()
        
        # Extract summary
        summary = ""
        if "[SECTION: Summary]" in raw_script:
            summary_part = raw_script.split("[SECTION: Summary]")[1]
            summary = summary_part.split("\n\n")[0].strip()
        
        return {
            "full_script": raw_script,
            "keywords": keywords,
            "summary": summary
        }
    
    def generate_script(
        self,
        ingested_data_json: Dict[str, Any],
        topic: Optional[str] = None,
        language: str = None,
        tone: str = None,
        summary_target_seconds: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an educational script from ingested content
        
        Args:
            ingested_data_json: Output from IngestionEngine
            topic: Override topic if different from source
            language: Output language (default: English)
            tone: Tone of voice (e.g., informative, enthusiastic)
            summary_target_seconds: Target duration in seconds
            
        Returns:
            Dictionary containing script and metadata, or None if failed
        """
        start_time = time.time()
        log_operation(logger, "generate_script", "started", {
            "source": ingested_data_json.get("metadata", {}).get("source"),
            "source_type": ingested_data_json.get("metadata", {}).get("source_type")
        })
        
        try:
            # Set defaults if not provided
            if not topic:
                topic = "Educational Content"
            if not language:
                language = config.default_language
            if not tone:
                tone = config.default_tone
            if not summary_target_seconds:
                summary_target_seconds = _main_config["defaults"]["default_script_length_seconds"]
            
            # Load and format prompt template
            prompt_template = self._load_prompt_template()
            if not prompt_template:
                raise ValueError("Could not load prompt template")
            
            word_count = self._estimate_word_count(summary_target_seconds)
            prompt = prompt_template.format(
                ingested_content=ingested_data_json["content"],
                topic=topic,
                language=language,
                style=tone,
                duration_seconds=summary_target_seconds,
                word_count=word_count
            )
            
            # Call LLM API
            llm_response = None
            for attempt in range(config.max_retries):
                llm_response = self.llm_client.generate_text(
                    prompt=prompt,
                    model=config.llm_model,
                    temperature=config.temperature
                )
                if llm_response:
                    break
                time.sleep(config.retry_delay)
            
            if not llm_response:
                raise RuntimeError("Failed to get valid response from LLM after retries")
            
            # Process the response
            raw_script = llm_response["choices"][0]["text"]
            processed_script = self._postprocess_script(raw_script)
            
            # Prepare output structure
            result = {
                "script": processed_script["full_script"],
                "metadata": {
                    "source": ingested_data_json.get("metadata", {}),
                    "generation_details": {
                        "model": config.llm_model,
                        "temperature": config.temperature,
                        "prompt_tokens": llm_response["usage"]["prompt_tokens"],
                        "completion_tokens": llm_response["usage"]["completion_tokens"],
                        "total_tokens": llm_response["usage"]["total_tokens"],
                        "generation_time_sec": time.time() - start_time
                    },
                    "content_attributes": {
                        "topic": topic,
                        "language": language,
                        "tone": tone,
                        "target_duration_seconds": summary_target_seconds,
                        "estimated_word_count": word_count,
                        "keywords": processed_script["keywords"],
                        "summary": processed_script["summary"]
                    }
                }
            }
            
            # Save outputs
            source_name = Path(ingested_data_json["metadata"]["source"]).stem
            output_prefix = config.output_dir / f"script_{source_name}"
            
            # Save human-readable text
            text_path = f"{output_prefix}.txt"
            save_text_file(result["script"], text_path)
            
            # Save structured JSON
            json_path = f"{output_prefix}.json"
            save_json_file(result, json_path)
            
            log_operation(logger, "generate_script", "completed", {
                "source": ingested_data_json["metadata"]["source"],
                "output_files": [text_path, json_path],
                "token_usage": llm_response["usage"],
                "duration_sec": time.time() - start_time
            })
            
            return result
            
        except Exception as e:
            log_operation(logger, "generate_script", "failed", {
                "error": str(e),
                "topic": topic,
                "duration_sec": time.time() - start_time
            }, level="ERROR")
            return None
