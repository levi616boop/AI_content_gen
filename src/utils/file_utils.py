import os
import json
from pathlib import Path
from typing import Any, Optional, Dict
from .logging_utils import setup_logger

# Initialize logger for file operations
logger = setup_logger("file_utils")

def create_directory_if_not_exists(path: str) -> bool:
    """
    Create a directory if it doesn't exist.
    
    Args:
        path: Directory path to create
        
    Returns:
        bool: True if directory exists or was created, False if failed
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {str(e)}")
        return False

def get_file_size(filepath: str) -> Optional[int]:
    """
    Get file size in bytes.
    
    Args:
        filepath: Path to the file
        
    Returns:
        int: File size in bytes or None if file doesn't exist
    """
    try:
        size = os.path.getsize(filepath)
        logger.debug(f"File size retrieved for {filepath}: {size} bytes")
        return size
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}")
        return None
    except Exception as e:
        logger.error(f"Error getting size for {filepath}: {str(e)}")
        return None

def save_text_file(content: str, filepath: str) -> bool:
    """
    Save text content to a file.
    
    Args:
        content: Text to save
        filepath: Destination file path
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Text file saved successfully: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save text file {filepath}: {str(e)}")
        return False

def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load data from a JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        dict: Parsed JSON data or None if failed
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"JSON file loaded successfully: {filepath}")
        return data
    except FileNotFoundError:
        logger.warning(f"JSON file not found: {filepath}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in file: {filepath}")
        return None
    except Exception as e:
        logger.error(f"Failed to load JSON file {filepath}: {str(e)}")
        return None

def save_json_file(data: Dict[str, Any], filepath: str, indent: int = 2) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        data: Dictionary to save as JSON
        filepath: Destination file path
        indent: Indentation level for pretty-printing
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        logger.info(f"JSON file saved successfully: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON file {filepath}: {str(e)}")
        return False

def clean_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*\0'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename
