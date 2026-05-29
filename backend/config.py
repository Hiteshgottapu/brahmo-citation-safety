"""
Configuration module for the Brahmo Citation Safety Engine.
Loads environment variables from ../.env and defines constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (one level up from backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

# --- External Service Keys ---
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")


# --- Cost Constants (in INR ₹) ---
COST_PER_SEARCH: float = 0.50
COST_PER_DOCMETA: float = 0.30

# --- Validation Constants ---
CURRENT_YEAR: int = 2026
MAX_SCC_VOLUME: int = 25
MAX_PAGE: int = 5000
MIN_YEAR: int = 1900
