import os
import time
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any
import PyPDF2
from PIL import Image
import pytesseract
from bs4 import BeautifulSoup

from src.utils.logging_utils import setup_logging, log_operation
from src.utils.file_utils import (
    create_directory_if_not_exists,
    get_file_size,
    save_text_file,
    save_json_file,
    clean_filename
)
from .config import config

# Initialize logging
logger = setup_logging("ingestion_engine")

class IngestionEngine:
    """Core engine for ingesting content from various sources"""
    
    def __init__(self):
        # Ensure directories exist
        create_directory_if_not_exists(config.input_dir)
        create_directory_if_not_exists(config.output_dir)
        create_directory_if_not_exists(config.temp_dir)
        
        logger.info("Ingestion Engine initialized with config:")
        logger.info(f"Input directory: {config.input_dir}")
        logger.info(f"Output directory: {config.output_dir}")

    def read_pdf(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with 'content' (text) and metadata, or None if failed
        """
        log_operation(logger, "read_pdf", "started", {"file": pdf_path})
        
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
                
            file_size = get_file_size(pdf_path)
            if file_size and file_size > config.max_file_size_mb * 1024 * 1024:
                raise ValueError(f"PDF exceeds maximum size of {config.max_file_size_mb}MB")
            
            text = ""
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            
            result = {
                "content": text.strip(),
                "metadata": {
                    "source": pdf_path,
                    "pages": len(reader.pages),
                    "size_bytes": file_size,
                    "source_type": "pdf"
                }
            }
            
            log_operation(logger, "read_pdf", "completed", 
                         {"file": pdf_path, "pages": len(reader.pages), "chars": len(text)})
            return result
            
        except Exception as e:
            log_operation(logger, "read_pdf", "failed", 
                         {"file": pdf_path, "error": str(e)}, level="ERROR")
            return None

    def read_image_with_ocr(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract text from an image using OCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with 'content' (text) and metadata, or None if failed
        """
        log_operation(logger, "read_image_with_ocr", "started", {"file": image_path})
        
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
                
            file_size = get_file_size(image_path)
            if file_size and file_size > config.max_file_size_mb * 1024 * 1024:
                raise ValueError(f"Image exceeds maximum size of {config.max_file_size_mb}MB")
            
            # Alternative: Cloud OCR services could be used here
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang=config.ocr_language, config=config.ocr_config)
            
            result = {
                "content": text.strip(),
                "metadata": {
                    "source": image_path,
                    "size_bytes": file_size,
                    "source_type": "image",
                    "ocr_language": config.ocr_language
                }
            }
            
            log_operation(logger, "read_image_with_ocr", "completed", 
                         {"file": image_path, "chars": len(text)})
            return result
            
        except Exception as e:
            log_operation(logger, "read_image_with_ocr", "failed", 
                         {"file": image_path, "error": str(e)}, level="ERROR")
            return None

    def scrape_html(self, url_or_filepath: str) -> Optional[Dict[str, Any]]:
        """
        Extract main content from a webpage or local HTML file.
        
        Args:
            url_or_filepath: URL or path to HTML file
            
        Returns:
            Dictionary with 'content' (text) and metadata, or None if failed
        """
        log_operation(logger, "scrape_html", "started", {"source": url_or_filepath})
        
        try:
            # Determine if source is URL or file
            is_url = url_or_filepath.startswith(('http://', 'https://'))
            
            if is_url:
                response = requests.get(url_or_filepath, timeout=config.timeout_seconds)
                response.raise_for_status()
                html_content = response.text
            else:
                if not os.path.exists(url_or_filepath):
                    raise FileNotFoundError(f"HTML file not found: {url_or_filepath}")
                with open(url_or_filepath, 'r', encoding='utf-8') as f:
                    html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find main content - heuristic approach
            main_content = None
            for tag in config.valid_content_tags:
                elements = soup.find_all(tag)
                for el in elements:
                    text = el.get_text().strip()
                    if len(text) >= config.min_content_length:
                        main_content = text
                        break
                if main_content:
                    break
            
            # Fallback to body if no content found
            if not main_content:
                main_content = soup.get_text().strip()
            
            result = {
                "content": main_content,
                "metadata": {
                    "source": url_or_filepath,
                    "source_type": "html",
                    "is_url": is_url,
                    "content_heuristic": "found" if main_content else "fallback"
                }
            }
            
            log_operation(logger, "scrape_html", "completed", 
                         {"source": url_or_filepath, "chars": len(main_content)})
            return result
            
        except Exception as e:
            log_operation(logger, "scrape_html", "failed", 
                         {"source": url_or_filepath, "error": str(e)}, level="ERROR")
            return None

    def process_source(self, source_path_or_url: str, source_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Main method to process a source based on its type.
        
        Args:
            source_path_or_url: Path or URL to the source
            source_type: One of 'pdf', 'image', 'html' (auto-detected if None)
            
        Returns:
            Dictionary with content and metadata, or None if failed
        """
        start_time = time.time()
        
        # Auto-detect source type if not specified
        if not source_type:
            if source_path_or_url.lower().endswith('.pdf'):
                source_type = 'pdf'
            elif source_path_or_url.lower().split('?')[0].endswith(('.png', '.jpg', '.jpeg')):
                source_type = 'image'
            elif source_path_or_url.startswith(('http://', 'https://')):
                source_type = 'html'
            else:
                source_type = 'html' if source_path_or_url.lower().endswith('.html') else None
                
        if not source_type:
            logger.error(f"Could not determine source type for: {source_path_or_url}")
            return None
            
        logger.info(f"Processing {source_type} source: {source_path_or_url}")
        
        # Dispatch to appropriate reader
        processor = {
            'pdf': self.read_pdf,
            'image': self.read_image_with_ocr,
            'html': self.scrape_html
        }.get(source_type)
        
        if not processor:
            logger.error(f"Unsupported source type: {source_type}")
            return None
            
        result = processor(source_path_or_url)
        
        # Save results if successful
        if result:
            output_filename = clean_filename(Path(source_path_or_url).stem)
            output_path = config.output_dir / f"{output_filename}.json"
            
            if save_json_file(result, output_path):
                logger.info(f"Saved processed content to: {output_path}")
                result['metadata']['output_path'] = str(output_path)
            else:
                logger.warning(f"Failed to save output for: {source_path_or_url}")
            
            # Log performance
            duration = time.time() - start_time
            logger.info(f"Processing completed in {duration:.2f} seconds")
            
        return result
