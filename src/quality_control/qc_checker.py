import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from src.utils.logging_utils import setup_logging, log_operation
from src.utils.file_utils import (
    create_directory_if_not_exists,
    save_json_file,
    load_json_file
)
from .config import config
from src.utils.api_keys import OPENAI_API_KEY  # Import API key

# Initialize logging
logger = setup_logging("quality_control")

class LLMQCClient:
    """Wrapper class for LLM-based quality checks"""
    
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        self.timeout = 30
        
    def _load_prompt(self, prompt_name: str) -> Optional[str]:
        """Load a prompt template from file"""
        try:
            with open(config.prompt_dir / prompt_name, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load prompt {prompt_name}: {str(e)}")
            return None
    
    def analyze_text(
        self,
        text: str,
        prompt_template: str,
        model: str = None,
        **format_args
    ) -> Optional[Dict[str, Any]]:
        """
        Perform LLM analysis on text
        
        Args:
            text: Text to analyze
            prompt_template: Name of prompt template file
            model: Override default model
            format_args: Additional formatting for prompt
            
        Returns:
            dict: Analysis results or None if failed
        """
        prompt = self._load_prompt(prompt_template)
        if not prompt:
            return None
            
        # Format prompt with content
        full_prompt = prompt.format(text=text, **format_args)
        
        # Simulate LLM call (in production, use actual API)
        logger.debug(f"LLM analysis prompt:\n{full_prompt}")
        
        # Placeholder response - in production would call:
        # response = requests.post(f"{self.base_url}/chat/completions", ...)
        return {
            "issues": [
                {"type": "grammar", "description": "Incorrect verb tense", "suggestion": "Change 'go' to 'went'"},
                {"type": "clarity", "description": "Complex sentence structure", "suggestion": "Break into two shorter sentences"}
            ],
            "score": 4.2,
            "summary": "Generally good with minor improvements needed"
        }
    
    def compare_texts(
        self,
        reference: str,
        actual: str,
        prompt_template: str,
        model: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Compare two texts using LLM
        
        Args:
            reference: Reference text
            actual: Actual text to compare
            prompt_template: Name of prompt template file
            model: Override default model
            
        Returns:
            dict: Comparison results or None if failed
        """
        prompt = self._load_prompt(prompt_template)
        if not prompt:
            return None
            
        # Format prompt with content
        full_prompt = prompt.format(reference=reference, actual=actual)
        
        # Simulate LLM call
        logger.debug(f"LLM comparison prompt:\n{full_prompt}")
        
        # Placeholder response
        return {
            "pacing_issues": [
                {"position": "0:45-1:10", "issue": "Speech too fast", "suggestion": "Slow down by 20%"},
                {"position": "2:30-3:00", "issue": "Long pause", "suggestion": "Trim pause by 1 second"}
            ],
            "content_mismatches": [
                {"position": "1:45", "reference": "quantum physics", "actual": "quantum mechanics"}
            ],
            "sync_score": 0.85
        }

class QualityControl:
    """Core quality control checks for educational content"""
    
    def __init__(self):
        self.llm_client = LLMQCClient()
        create_directory_if_not_exists(config.output_dir)
        logger.info("Quality Control initialized")
        
    def _transcribe_audio(self, video_path: Path) -> Optional[str]:
        """
        Transcribe audio from video (placeholder for Whisper implementation)
        
        Args:
            video_path: Path to video file
            
        Returns:
            str: Transcribed text or None if failed
        """
        try:
            # In production, would use:
            # import whisper
            # model = whisper.load_model(config.asr_model)
            # result = model.transcribe(str(video_path), language=config.asr_language)
            # return result["text"]
            
            logger.info(f"Would transcribe audio from {video_path} using {config.asr_model} model")
            return "This is a simulated transcription of the video audio content."
        except Exception as e:
            logger.error(f"Audio transcription failed: {str(e)}")
            return None
    
    def run_script_review(self, script_text: str) -> Optional[Dict[str, Any]]:
        """
        Perform comprehensive script review
        
        Args:
            script_text: Script text to review
            
        Returns:
            dict: Review results or None if failed
        """
        start_time = time.time()
        log_operation(logger, "run_script_review", "started", 
                     {"text_length": len(script_text)})
        
        try:
            # Run LLM analysis
            result = self.llm_client.analyze_text(
                text=script_text,
                prompt_template=config.script_review_prompt,
                model=config.llm_models["script_review"]
            )
            
            if not result:
                raise RuntimeError("LLM analysis returned no results")
            
            # Process results
            grammar_issues = [issue for issue in result.get("issues", []) 
                            if issue["type"] == "grammar"]
            clarity_issues = [issue for issue in result.get("issues", []) 
                            if issue["type"] == "clarity"]
            
            review_result = {
                "grammar_issues": grammar_issues,
                "clarity_issues": clarity_issues,
                "score": result.get("score", 0),
                "summary": result.get("summary", ""),
                "timestamp": time.time()
            }
            
            duration = time.time() - start_time
            log_operation(logger, "run_script_review", "completed", {
                "issues_found": len(grammar_issues) + len(clarity_issues),
                "score": review_result["score"],
                "duration_sec": duration
            })
            
            return review_result
            
        except Exception as e:
            log_operation(logger, "run_script_review", "failed", {
                "error": str(e)
            }, level="ERROR")
            return None
    
    def run_video_review(
        self,
        video_path: Path,
        script_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Review video against script for pacing and sync issues
        
        Args:
            video_path: Path to video file
            script_text: Original script text
            
        Returns:
            dict: Review results or None if failed
        """
        start_time = time.time()
        log_operation(logger, "run_video_review", "started", 
                     {"video": str(video_path)})
        
        try:
            # Step 1: Transcribe audio
            transcribed_text = self._transcribe_audio(video_path)
            if not transcribed_text:
                raise RuntimeError("Audio transcription failed")
            
            # Step 2: Compare with script
            comparison = self.llm_client.compare_texts(
                reference=script_text,
                actual=transcribed_text,
                prompt_template=config.pacing_analysis_prompt,
                model=config.llm_models["general_qc"]
            )
            
            if not comparison:
                raise RuntimeError("Text comparison failed")
            
            # Step 3: (Placeholder) Visual alignment check
            visual_alignment = {
                "issues": [],
                "score": 0.9,
                "summary": "Simulated visual alignment results"
            }
            
            review_result = {
                "pacing_issues": comparison.get("pacing_issues", []),
                "content_mismatches": comparison.get("content_mismatches", []),
                "visual_alignment": visual_alignment,
                "transcription": transcribed_text,
                "timestamp": time.time()
            }
            
            duration = time.time() - start_time
            log_operation(logger, "run_video_review", "completed", {
                "pacing_issues": len(review_result["pacing_issues"]),
                "mismatches": len(review_result["content_mismatches"]),
                "duration_sec": duration
            })
            
            return review_result
            
        except Exception as e:
            log_operation(logger, "run_video_review", "failed", {
                "error": str(e),
                "video": str(video_path)
            }, level="ERROR")
            return None
    
    def generate_qc_report(
        self,
        script_text: str,
        video_path: Path = None
    ) -> Optional[Path]:
        """
        Generate comprehensive QC report
        
        Args:
            script_text: Script text to review
            video_path: Optional path to video file
            
        Returns:
            Path: Path to generated report, or None if failed
        """
        start_time = time.time()
        source_name = "script_only"
        if video_path:
            source_name = video_path.stem
        log_operation(logger, "generate_qc_report", "started", 
                     {"source": source_name})
        
        try:
            report = {
                "script_review": self.run_script_review(script_text),
                "video_review": None,
                "summary": {},
                "timestamp": time.time()
            }
            
            # Add video review if video provided
            if video_path:
                report["video_review"] = self.run_video_review(video_path, script_text)
            
            # Generate overall summary
            report["summary"] = self._generate_summary(report)
            
            # Save report
            report_path = config.output_dir / f"{source_name}_qc_report.json"
            save_json_file(report, report_path)
            
            duration = time.time() - start_time
            log_operation(logger, "generate_qc_report", "completed", {
                "report_path": str(report_path),
                "duration_sec": duration,
                "overall_score": report["summary"].get("overall_score", 0)
            })
            
            return report_path
            
        except Exception as e:
            log_operation(logger, "generate_qc_report", "failed", {
                "error": str(e),
                "source": source_name
            }, level="ERROR")
            return None
    
    def _generate_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall summary from review results"""
        summary = {
            "critical_issues": 0,
            "warnings": 0,
            "passed_checks": 0,
            "overall_score": 0,
            "recommendations": []
        }
        
        # Process script review
        if report.get("script_review"):
            script_score = report["script_review"].get("score", 0)
            grammar_issues = len(report["script_review"].get("grammar_issues", []))
            clarity_issues = len(report["script_review"].get("clarity_issues", []))
            
            if grammar_issues > config.grammar_error_threshold:
                summary["critical_issues"] += 1
                summary["recommendations"].append("Fix grammar issues in script")
            elif grammar_issues > 0:
                summary["warnings"] += 1
            
            if clarity_issues > 0:
                summary["warnings"] += 1
                summary["recommendations"].append("Improve script clarity")
            
            summary["overall_score"] += script_score * 0.6  # 60% weight
        
        # Process video review
        if report.get("video_review"):
            pacing_issues = len(report["video_review"].get("pacing_issues", []))
            mismatches = len(report["video_review"].get("content_mismatches", []))
            visual_score = report["video_review"].get("visual_alignment", {}).get("score", 1)
            
            if pacing_issues > 0:
                summary["warnings"] += 1
                summary["recommendations"].append("Adjust video pacing")
            
            if mismatches > 0:
                summary["critical_issues"] += 1
                summary["recommendations"].append("Fix content mismatches")
            
            if visual_score < config.min_visual_sync_score:
                summary["warnings"] += 1
                summary["recommendations"].append("Improve visual-narration sync")
            
            summary["overall_score"] += visual_score * 0.4  # 40% weight
        
        # Calculate overall score (1-5 scale)
        if report.get("script_review") and report.get("video_review"):
            summary["overall_score"] = round(summary["overall_score"], 1)
        elif report.get("script_review"):
            summary["overall_score"] = round(report["script_review"].get("score", 0), 1)
        
        # Final assessment
        if summary["critical_issues"] > 0:
            summary["status"] = "needs_revision"
        elif summary["warnings"] > 0 or summary["overall_score"] < config.warning_score_threshold:
            summary["status"] = "needs_review"
        else:
            summary["status"] = "approved"
        
        return summary
