from pathlib import Path
from dotenv import load_dotenv
import os

"""
Centralized project configuration.

This module loads environment variables and exposes
shared configuration values used throughout the project.
"""

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GOOGLE_CREDENTIALS_RELATIVE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if GOOGLE_CREDENTIALS_RELATIVE is None:
    raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")

GOOGLE_CREDENTIALS_PATH = PROJECT_ROOT / GOOGLE_CREDENTIALS_RELATIVE

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

