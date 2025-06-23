import os
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any
import svgwrite
import cairosvg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.utils.logging_utils import setup_logging, log_operation
from src.utils.file_utils import (
    create_directory_if_not_exists,
    save_json_file,
    load_json_file
)
from .config import config

# Initialize logging
logger = setup_logging("animator")

class Animator:
    """Core animation generator using Manim and SVG"""
    
    def __init__(self):
        create_directory_if_not_exists(config.output_dir)
        self.template = self._load_default_template()
        logger.info("Animator initialized with config:")
        logger.info(f"Resolution: {config.resolution}")
        logger.info(f"FPS: {config.fps}")

    def _load_default_template(self) -> Dict[str, Any]:
        """Load the default animation template"""
        template_path = config.template_dir / "default_template.json"
        try:
            return load_json_file(template_path)
        except Exception as e:
            logger.error(f"Failed to load template: {str(e)}")
            return {}

    def generate_manim_animation(self, script_text: str, output_path: Path) -> bool:
        """
        Generate animation using Manim by calling it as subprocess
        
        Args:
            script_text: Text content from script
            output_path: Output directory for animation
            
        Returns:
            bool: True if successful, False otherwise
        """
        log_operation(logger, "generate_manim_animation", "started", 
                     {"output_path": str(output_path)})
        
        try:
            # Create temporary Manim script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                temp_script_path = Path(f.name)
                
                # Generate basic Manim script (simplified example)
                manim_script = f"""
from manim import *

class GeneratedAnimation(Scene):
    def construct(self):
        # Example simple animation
        title = Text("{script_text[:50]}...", font_size=48)
        self.play(Write(title))
        self.wait(2)
        self.play(FadeOut(title))
"""
                f.write(manim_script)
            
            # Call Manim via subprocess
            result = subprocess.run([
                config.manim_path,
                "-ql",  # Medium quality
                "-o", output_path.stem,
                str(temp_script_path),
                "GeneratedAnimation"
            ], cwd=output_path.parent, capture_output=True, text=True)
            
            # Clean up temporary file
            temp_script_path.unlink()
            
            if result.returncode != 0:
                logger.error(f"Manim failed: {result.stderr}")
                return False
                
            log_operation(logger, "generate_manim_animation", "completed", 
                         {"output_path": str(output_path)})
            return True
            
        except Exception as e:
            logger.error(f"Manim generation failed: {str(e)}")
            return False

    def generate_svg_animation(self, script_json: Dict[str, Any], output_path: Path) -> bool:
        """
        Generate animation frames using SVG
        
        Args:
            script_json: Structured script data
            output_path: Output directory for frames
            
        Returns:
            bool: True if successful, False otherwise
        """
        log_operation(logger, "generate_svg_animation", "started", 
                     {"output_path": str(output_path)})
        
        try:
            create_directory_if_not_exists(output_path)
            
            # Get resolution from config
            width, height = config.resolution_map.get(config.resolution, (1920, 1080))
            
            # Generate frames for each section
            sections = self._parse_script_to_sections(script_json)
            frame_count = 0
            
            for i, section in enumerate(sections):
                # Create SVG for each section
                dwg = svgwrite.Drawing(size=(f"{width}px", f"{height}px"))
                
                # Background
                dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='#333333'))
                
                # Title
                dwg.add(dwg.text(
                    section.get('title', 'Educational Content'),
                    insert=(width//2, height//2),
                    font_size="48px",
                    fill="#FFFFFF",
                    text_anchor="middle"
                ))
                
                # Save SVG
                svg_file = output_path / f"frame_{frame_count:04d}.svg"
                dwg.saveas(svg_file)
                
                # Convert to PNG
                png_file = output_path / f"frame_{frame_count:04d}.png"
                cairosvg.svg2png(url=str(svg_file), write_to=str(png_file))
                
                frame_count += 1
                
                # Remove intermediate SVG
                svg_file.unlink()
            
            log_operation(logger, "generate_svg_animation", "completed", 
                         {"frames_generated": frame_count})
            return True
            
        except Exception as e:
            logger.error(f"SVG generation failed: {str(e)}")
            return False

    def _parse_script_to_sections(self, script_json: Dict[str, Any]) -> list:
        """
        Parse script JSON into animation sections
        """
        # This is a simplified parser - would be more sophisticated in production
        script = script_json.get("script", "")
        sections = []
        
        # Split by sections if marked in script
        if "[SECTION:" in script:
            section_parts = script.split("[SECTION:")[1:]
            for part in section_parts:
                section_name, content = part.split("]", 1)
                sections.append({
                    "title": section_name.strip(),
                    "content": content.strip()
                })
        else:
            sections.append({
                "title": script_json.get("metadata", {}).get("content_attributes", {}).get("topic", "Educational Content"),
                "content": script
            })
            
        return sections

    def compile_frames_to_mp4(self, frame_dir: Path, output_mp4: Path, fps: int = None) -> bool:
        """
        Compile PNG frames to MP4 using ffmpeg
        
        Args:
            frame_dir: Directory containing frames (frame_0001.png, etc.)
            output_mp4: Output MP4 file path
            fps: Frames per second
            
        Returns:
            bool: True if successful, False otherwise
        """
        log_operation(logger, "compile_frames_to_mp4", "started", 
                     {"frame_dir": str(frame_dir), "output": str(output_mp4)})
        
        try:
            if not fps:
                fps = config.fps
                
            # Check if frames exist
            frame_files = sorted(frame_dir.glob("frame_*.png"))
            if not frame_files:
                logger.error("No frames found to compile")
                return False
                
            # Build ffmpeg command
            cmd = [
                config.ffmpeg_path,
                "-y",  # Overwrite output
                "-framerate", str(fps),
                "-i", str(frame_dir / "frame_%04d.png"),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-vf", f"scale={config.resolution_map[config.resolution][0]}:{config.resolution_map[config.resolution][1]}",
                str(output_mp4)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"ffmpeg failed: {result.stderr}")
                return False
                
            log_operation(logger, "compile_frames_to_mp4", "completed", 
                         {"output": str(output_mp4), "frame_count": len(frame_files)})
            return True
            
        except Exception as e:
            logger.error(f"Frame compilation failed: {str(e)}")
            return False

    def process_script_for_animation(self, script_json: Dict[str, Any]) -> Optional[Path]:
        """
        Main method to process script and generate animation
        
        Args:
            script_json: Structured script data from ScriptGenerator
            
        Returns:
            Path: Path to generated animation file, or None if failed
        """
        start_time = time.time()
        script_source = script_json.get("metadata", {}).get("source", {}).get("source", "unknown")
        log_operation(logger, "process_script_for_animation", "started", 
                     {"source": script_source})
        
        try:
            # Create output directory
            source_name = Path(script_source).stem
            output_dir = config.output_dir / source_name
            create_directory_if_not_exists(output_dir)
            
            # Choose animation method (simplified logic)
            use_manim = "KEY_CONCEPT" in script_json.get("script", "")  # Example heuristic
            
            if use_manim:
                output_path = output_dir / f"{source_name}_manim.mp4"
                success = self.generate_manim_animation(
                    script_json.get("script", ""),
                    output_path
                )
            else:
                # Generate SVG frames then compile
                frames_dir = output_dir / "frames"
                create_directory_if_not_exists(frames_dir)
                
                success = self.generate_svg_animation(script_json, frames_dir)
                if success:
                    output_path = output_dir / f"{source_name}_svg.mp4"
                    success = self.compile_frames_to_mp4(frames_dir, output_path)
            
            if not success:
                return None
                
            duration = time.time() - start_time
            log_operation(logger, "process_script_for_animation", "completed", 
                         {"output": str(output_path), "duration_sec": duration})
            
            return output_path
            
        except Exception as e:
            logger.error(f"Animation processing failed: {str(e)}")
            return None
