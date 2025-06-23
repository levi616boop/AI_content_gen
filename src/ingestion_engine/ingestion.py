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
            if file_size and file_size > config.max_file
