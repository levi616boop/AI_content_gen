import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# Configure logging to use structured JSON format
class StructuredMessage:
    def __init__(self, message, **kwargs):
        self.message = message
        self.kwargs = kwargs

    def __str__(self):
        return f"{self.message} | {json.dumps(self.kwargs)}"

def setup_logging(
    module_name: str,
    log_dir: str = "data/logs",
    log_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configure structured logging for a pipeline module.
    
    Args:
        module_name: Name of the module (e.g., 'ingestion', 'script_generator')
        log_dir: Base directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    # Ensure log directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Create module-specific log file path
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = Path(log_dir) / f"{module_name}_{timestamp}.log"
    
    # Set up logger
    logger = logging.getLogger(module_name)
    logger.setLevel(log_level.upper())
    
    # Clear existing handlers to avoid duplication
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler for persistent logs
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler for real-time output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def log_operation(
    logger: logging.Logger,
    operation: str,
    status: str,
    metadata: Optional[Dict] = None,
    level: str = "INFO"
):
    """
    Helper function for standardized operation logging.
    
    Args:
        logger: Configured logger instance
        operation: Name of the operation being logged
        status: Current status (e.g., 'started', 'completed', 'failed')
        metadata: Additional context as a dictionary
        level: Log level for the message
    """
    log_method = getattr(logger, level.lower(), logger.info)
    message = StructuredMessage(
        f"Operation: {operation} | Status: {status}",
        operation=operation,
        status=status,
        **(metadata or {})
    )
    log_method(message)

# Example usage:
# logger = setup_logging("ingestion_engine")
# log_operation(logger, "pdf_processing", "started", {"file": "example.pdf"})
