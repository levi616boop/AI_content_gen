import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Tuple, Optional
from src.utils.logging_utils import setup_logger

# Initialize logger
logger = setup_logger("env_initializer")

# Define mandatory and optional environment variables
MANDATORY_ENV_VARS = {
    "OPENAI_API_KEY": "API key for OpenAI services",
    "ELEVENLABS_API_KEY": "API key for ElevenLabs voice generation",
    "YOUTUBE_API_KEY": "API key for YouTube uploads",
}

OPTIONAL_ENV_VARS = {
    "TIKTOK_API_KEY": "API key for TikTok uploads (optional)",
    "INSTAGRAM_API_KEY": "API key for Instagram uploads (optional)",
    "LOG_LEVEL": "Logging level (default: INFO)",
}

def initialize_env(env_path: Optional[Path] = None) -> bool:
    """
    Initialize and validate environment variables from .env file.
    
    Args:
        env_path: Optional custom path to .env file. If None, looks in project root.
        
    Returns:
        bool: True if all mandatory variables are present, False otherwise.
        
    Raises:
        SystemExit: If mandatory variables are missing.
    """
    # Determine .env file path
    if env_path is None:
        env_path = Path(__file__).parent.parent.parent / ".env"
    
    # Load environment variables
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        logger.warning(f".env file not found at {env_path} - checking system environment")
    
    # Validate environment variables
    missing_mandatory = []
    missing_optional = []
    
    for var, desc in MANDATORY_ENV_VARS.items():
        if os.getenv(var) is None:
            missing_mandatory.append((var, desc))
    
    for var, desc in OPTIONAL_ENV_VARS.items():
        if os.getenv(var) is None:
            missing_optional.append((var, desc))
    
    # Handle missing variables
    if missing_mandatory:
        error_msg = "Missing mandatory environment variables:\n"
        for var, desc in missing_mandatory:
            error_msg += f"  - {var}: {desc}\n"
        
        logger.critical(error_msg)
        
        # User-friendly console message
        print("\nERROR: Missing required configuration:")
        print(error_msg)
        print("Please create/update your .env file based on these templates:")
        print(f"  - {Path(__file__).parent / 'api_keys.py.template'}")
        print(f"  - {Path(__file__).parent.parent.parent / '.env.template'}")
        print("\nRemember to NEVER commit .env to version control!")
        print("Add these lines to your .gitignore file:")
        print(".env\n*.env\n")
        
        sys.exit(1)
    
    if missing_optional:
        warning_msg = "Missing optional environment variables:\n"
        for var, desc in missing_optional:
            warning_msg += f"  - {var}: {desc}\n"
        logger.warning(warning_msg)
    
    return True

def get_env_variable(name: str, default: Optional[str] = None) -> str:
    """
    Safely get environment variable with validation.
    
    Args:
        name: Name of the environment variable
        default: Default value if variable not found
        
    Returns:
        str: Value of the environment variable
        
    Raises:
        ValueError: If variable is mandatory
