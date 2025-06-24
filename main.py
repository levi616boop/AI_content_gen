#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Initialize environment variables first
from src.utils.env_initializer import initialize_env
if not initialize_env():
    sys.exit(1)  # Exit if environment validation fails

# Import pipeline modules after environment is validated
from src.ingestion_engine.ingestion import IngestionEngine
from src.script_generator.script_gen import ScriptGenerator
from src.animator.animate import Animator
from src.voice_generator.voice_gen import VoiceGenerator
from src.video_composer.compose import VideoComposer
from src.quality_control.qc_checker import QualityControl
from src.uploader.upload import Uploader
from src.content_manager.manager import ContentManager
from src.technician_agent.technician import TechnicianAgent

# Initialize logging
from src.utils.logging_utils import setup_logger
logger = setup_logger("pipeline")

def load_config() -> Dict[str, Any]:
    """Load the main configuration file"""
    config_path = Path(__file__).parent / "config" / "main_config.json"
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        sys.exit(1)

def initialize_modules(config: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize all pipeline modules with configuration"""
    try:
        modules = {
            "ingestion": IngestionEngine(),
            "script_generator": ScriptGenerator(),
            "animator": Animator(),
            "voice_generator": VoiceGenerator(),
            "video_composer": VideoComposer(),
            "quality_control": QualityControl(),
            "uploader": Uploader(),
            "content_manager": ContentManager(),
            "technician": TechnicianAgent()
        }
        logger.info("All pipeline modules initialized successfully")
        return modules
    except Exception as e:
        logger.critical(f"Module initialization failed: {str(e)}")
        sys.exit(1)

def run_pipeline_stage(stage_name: str, func, *args, **kwargs) -> Any:
    """Wrapper to run a pipeline stage with consistent error handling"""
    logger.info(f"Starting stage: {stage_name}")
    start_time = datetime.now()
    
    try:
        result = func(*args, **kwargs)
        if not result:
            raise RuntimeError(f"{stage_name} returned no results")
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Completed {stage_name} in {duration:.2f} seconds")
        return result
        
    except Exception as e:
        logger.error(f"Stage {stage_name} failed: {str(e)}")
        raise  # Re-raise to be caught by the main pipeline handler

def run_full_pipeline(
    modules: Dict[str, Any],
    source_path: str,
    source_type: str,
    topic: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute the full content generation pipeline with robust error handling
    
    Args:
        modules: Dictionary of initialized modules
        source_path: Path to source material
        source_type: Type of source (pdf, html, image)
        topic: Optional topic override
        
    Returns:
        dict: Pipeline execution results and diagnostics
    """
    results = {
        "start_time": datetime.now().isoformat(),
        "stages": {},
        "success": False,
        "error": None
    }
    
    try:
        # 1. Ingestion
        ingested_data = run_pipeline_stage(
            "ingestion",
            modules["ingestion"].process_source,
            source_path,
            source_type
        )
        results["stages"]["ingestion"] = {
            "output": ingested_data["metadata"]["source"],
            "success": True
        }

        # 2. Script Generation
        script_data = run_pipeline_stage(
            "script_generation",
            modules["script_generator"].generate_script,
            ingested_data,
            topic
        )
        results["stages"]["script_generation"] = {
            "output": script_data["metadata"]["source"],
            "success": True
        }

        # 3. Animation
        animation_path = run_pipeline_stage(
            "animation",
            modules["animator"].process_script_for_animation,
            script_data
        )
        results["stages"]["animation"] = {
            "output": str(animation_path),
            "success": True
        }

        # 4. Voice Generation
        voice_results = run_pipeline_stage(
            "voice_generation",
            modules["voice_generator"].process_script,
            script_data
        )
        results["stages"]["voice_generation"] = {
            "output": str(voice_results["voiceover"]),
            "success": True
        }

        # 5. Video Composition
        final_video_path = run_pipeline_stage(
            "video_composition",
            modules["video_composer"].merge_assets,
            animation_path,
            voice_results["voiceover"],
            voice_results.get("subtitles")
        )
        results["stages"]["video_composition"] = {
            "output": str(final_video_path),
            "success": True
        }

        # 6. Quality Control
        qc_report_path = run_pipeline_stage(
            "quality_control",
            modules["quality_control"].generate_qc_report,
            script_data["script"],
            final_video_path
        )
        results["stages"]["quality_control"] = {
            "output": str(qc_report_path),
            "success": qc_report_path is not None
        }

        # 7. Upload
        upload_results = run_pipeline_stage(
            "upload",
            modules["uploader"].upload_all_platforms,
            final_video_path,
            script_data
        )
        results["stages"]["upload"] = {
            "output": {k: v is not None for k, v in upload_results.items()},
            "success": any(upload_results.values())
        }

        results["success"] = True
        logger.info("Pipeline completed successfully")

    except Exception as e:
        results["error"] = str(e)
        logger.error(f"Pipeline failed: {str(e)}")
        
        # Attempt to run diagnostics even after failure
        try:
            logger.info("Running diagnostic checks after pipeline failure")
            modules["technician"].analyze_logs()
            modules["technician"].generate_diagnostic_report()
        except Exception as diag_error:
            logger.error(f"Diagnostics failed: {str(diag_error)}")

    finally:
        results["end_time"] = datetime.now().isoformat()
        
        # Always run maintenance and analysis
        try:
            logger.info("Running content analysis and system diagnostics")
            modules["content_manager"].load_past_upload_data()
            modules["content_manager"].update_performance_metrics()
            modules["technician"].analyze_logs()
            modules["technician"].generate_diagnostic_report()
        except Exception as e:
            logger.error(f"Post-pipeline tasks failed: {str(e)}")

        return results

def parse_arguments():
    """Parse command line arguments with improved validation"""
    parser = argparse.ArgumentParser(
        description="AutoEd Content Generation Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "source_path",
        help="Path to source material (PDF, image, or URL)"
    )
    parser.add_argument(
        "--source-type",
        choices=["pdf", "image", "html"],
        required=True,
        help="Type of source material"
    )
    parser.add_argument(
        "--topic",
        help="Optional topic override for content"
    )
    parser.add_argument(
        "--schedule",
        help="Run on schedule (cron format), e.g. '0 9 * * *' for daily at 9AM"
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Custom path to .env file"
    )
    return parser.parse_args()

def print_summary(results: Dict[str, Any]):
    """Print a user-friendly summary of the pipeline run"""
    duration = (datetime.fromisoformat(results["end_time"]) - 
               datetime.fromisoformat(results["start_time"]))
    
    print("\n=== Pipeline Summary ===")
    print(f"Status: {'SUCCESS' if results['success'] else 'FAILED'}")
    print(f"Duration: {duration}")
    
    if results["error"]:
        print(f"\nError: {results['error']}")
    
    print("\nStage Results:")
    for stage, info in results["stages"].items():
        status = "✓" if info["success"] else "✗"
        print(f"{status} {stage.replace('_', ' ').title():<18} Output: {info.get('output', 'N/A')}")

def main():
    """Main entry point with comprehensive error handling"""
    try:
        args = parse_arguments()
        config = load_config()
        
        # Initialize modules with configuration
        modules = initialize_modules(config)
        
        # Handle scheduled runs
        if args.schedule:
            try:
                from apscheduler.schedulers.blocking import BlockingScheduler
                scheduler = BlockingScheduler()
                
                @scheduler.scheduled_job('cron', args.schedule)
                def scheduled_run():
                    logger.info(f"Running scheduled pipeline for {args.source_path}")
                    results = run_full_pipeline(
                        modules=modules,
                        source_path=args.source_path,
                        source_type=args.source_type,
                        topic=args.topic
                    )
                    print_summary(results)
                
                logger.info(f"Starting scheduler with schedule: {args.schedule}")
                print(f"Pipeline scheduler started. Press Ctrl+C to exit.")
                scheduler.start()
                
            except ImportError:
                logger.error("APScheduler not installed. Run: pip install apscheduler")
                sys.exit(1)
            except Exception as e:
                logger.error(f"Scheduler failed: {str(e)}")
                sys.exit(1)
        else:
            # Single run mode
            results = run_full_pipeline(
                modules=modules,
                source_path=args.source_path,
                source_type=args.source_type,
                topic=args.topic
            )
            print_summary(results)
            sys.exit(0 if results["success"] else 1)
            
    except Exception as e:
        logger.critical(f"Fatal error in main execution: {str(e)}")
        print(f"CRITICAL ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
