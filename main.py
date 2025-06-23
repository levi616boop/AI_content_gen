#!/usr/bin/env python3
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Import pipeline modules
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('data/logs/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pipeline")

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
    """Initialize all pipeline modules"""
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
    logger.info("All pipeline modules initialized")
    return modules

def run_full_pipeline(
    modules: Dict[str, Any],
    source_path: str,
    source_type: str,
    topic: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute the full content generation pipeline
    
    Args:
        modules: Dictionary of initialized modules
        source_path: Path to source material
        source_type: Type of source (pdf, html, image)
        topic: Optional topic override
        
    Returns:
        dict: Pipeline execution results
    """
    results = {
        "start_time": datetime.now().isoformat(),
        "stages": {},
        "success": False
    }
    
    try:
        logger.info(f"Starting pipeline for {source_path} (type: {source_type})")
        
        # 1. Ingestion
        logger.info("Running ingestion...")
        ingested_data = modules["ingestion"].process_source(source_path, source_type)
        if not ingested_data:
            raise RuntimeError("Ingestion failed")
        results["stages"]["ingestion"] = {
            "output": ingested_data["metadata"]["source"],
            "success": True
        }
        
        # 2. Script Generation
        logger.info("Generating script...")
        script_data = modules["script_generator"].generate_script(
            ingested_data_json=ingested_data,
            topic=topic
        )
        if not script_data:
            raise RuntimeError("Script generation failed")
        results["stages"]["script_generation"] = {
            "output": script_data["metadata"]["source"],
            "success": True
        }
        
        # 3. Animation
        logger.info("Creating animation...")
        animation_path = modules["animator"].process_script_for_animation(script_data)
        if not animation_path:
            raise RuntimeError("Animation failed")
        results["stages"]["animation"] = {
            "output": str(animation_path),
            "success": True
        }
        
        # 4. Voice Generation
        logger.info("Generating voiceover...")
        voice_results = modules["voice_generator"].process_script(script_data)
        if not voice_results or not voice_results["voiceover"]:
            raise RuntimeError("Voice generation failed")
        results["stages"]["voice_generation"] = {
            "output": str(voice_results["voiceover"]),
            "success": True
        }
        
        # 5. Video Composition
        logger.info("Composing final video...")
        final_video_path = modules["video_composer"].merge_assets(
            animation_mp4_path=animation_path,
            voice_mp3_path=voice_results["voiceover"],
            subtitles_srt_path=voice_results.get("subtitles")
        )
        if not final_video_path:
            raise RuntimeError("Video composition failed")
        results["stages"]["video_composition"] = {
            "output": str(final_video_path),
            "success": True
        }
        
        # 6. Quality Control
        logger.info("Running quality control...")
        qc_report_path = modules["quality_control"].generate_qc_report(
            script_text=script_data["script"],
            video_path=final_video_path
        )
        if not qc_report_path:
            logger.warning("Quality control failed, but continuing pipeline")
        else:
            results["stages"]["quality_control"] = {
                "output": str(qc_report_path),
                "success": True
            }
        
        # 7. Upload
        logger.info("Uploading content...")
        upload_results = modules["uploader"].upload_all_platforms(
            video_path=final_video_path,
            script_json=script_data
        )
        results["stages"]["upload"] = {
            "output": {k: v is not None for k, v in upload_results.items()},
            "success": any(upload_results.values())
        }
        
        # Mark pipeline as successful
        results["success"] = True
        logger.info("Pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        results["error"] = str(e)
        # Attempt to save partial results
        if "stages" not in results:
            results["stages"] = {}
    
    finally:
        results["end_time"] = datetime.now().isoformat()
        
        # Run maintenance and analysis (even if pipeline failed)
        try:
            logger.info("Running content analysis...")
            modules["content_manager"].load_past_upload_data()
            modules["content_manager"].update_performance_metrics()
            
            logger.info("Running system diagnostics...")
            modules["technician"].analyze_logs()
            modules["technician"].generate_diagnostic_report()
        except Exception as e:
            logger.error(f"Maintenance tasks failed: {str(e)}")
        
        return results

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="AutoEd Content Generation Pipeline")
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
        help="Optional topic override"
    )
    parser.add_argument(
        "--schedule",
        help="Run on schedule (cron format), e.g. '0 9 * * *' for daily at 9AM"
    )
    return parser.parse_args()

def main():
    """Main entry point for the pipeline"""
    args = parse_arguments()
    config = load_config()
    modules = initialize_modules(config)
    
    # Check if running on schedule
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
                logger.info(f"Scheduled run completed: {results['success']}")
            
            logger.info(f"Starting scheduler with schedule: {args.schedule}")
            scheduler.start()
            
        except ImportError:
            logger.error("APScheduler not installed. Run 'pip install apscheduler' for scheduling.")
        except Exception as e:
            logger.error(f"Scheduler failed: {str(e)}")
    else:
        # Run once
        results = run_full_pipeline(
            modules=modules,
            source_path=args.source_path,
            source_type=args.source_type,
            topic=args.topic
        )
        
        # Print summary
        print("\nPipeline Summary:")
        print(f"Success: {results['success']}")
        print(f"Duration: {datetime.fromisoformat(results['end_time']) - datetime.fromisoformat(results['start_time'])}")
        for stage, info in results['stages'].items():
            print(f"{stage.replace('_', ' ').title()}: {'Success' if info['success'] else 'Failed'}")
        
        if not results['success']:
            sys.exit(1)

if __name__ == "__main__":
    main()
