"""
Configuration file for the backend service.
All environment variables, paths, and constants in one place.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# API Endpoints
OPENAI_MODERATION_URL = "https://api.openai.com/v1/moderations"
OPENAI_REALTIME_URL = "https://api.openai.com/v1/realtime/calls"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# Directory Paths
BACKEND_DIR = Path(__file__).parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
INSTRUCTIONS_FILE = BACKEND_DIR / "instructions.md"

# Server Configuration
HOST = "0.0.0.0"
PORT = 8000

# Session Configuration
DEFAULT_LANGUAGE = "he"
SUPPORTED_LANGUAGES = ["en", "he"]

# Moderation Configuration
OPENAI_MODERATION_MODEL = "omni-moderation-latest"
LLAMA_GUARD_MODEL = "meta-llama/llama-prompt-guard-2-86m"
MODERATION_THRESHOLD = 0.1  # OpenAI category score threshold
LLAMA_ATTACK_THRESHOLD = 0.5  # Llama Prompt Guard attack threshold

# Session Audio Configuration
REALTIME_MODEL = "gpt-realtime"
TRANSCRIPTION_MODEL = "gpt-4o-transcribe"  # or whisper-1 (slower but more accurate)
VOICE = "cedar"
VAD_THRESHOLD = 0.6
VAD_PREFIX_PADDING_MS = 300
VAD_SILENCE_DURATION_MS = 500

# HTTP Client Configuration
HTTP_TIMEOUT = 30.0