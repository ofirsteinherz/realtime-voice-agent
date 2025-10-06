"""
Session service for WebRTC session creation with OpenAI Realtime API.
"""
import json
import httpx
from typing import Tuple
from config import (
    OPENAI_API_KEY,
    OPENAI_REALTIME_URL,
    INSTRUCTIONS_FILE,
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    REALTIME_MODEL,
    TRANSCRIPTION_MODEL,
    VOICE,
    VAD_THRESHOLD,
    VAD_PREFIX_PADDING_MS,
    VAD_SILENCE_DURATION_MS,
    HTTP_TIMEOUT,
)


def load_instructions(language: str) -> str:
    """
    Load instructions from markdown file and inject language.
    
    Args:
        language: The language code (en or he)
        
    Returns:
        The instructions with language injected
    """
    with open(INSTRUCTIONS_FILE, 'r', encoding='utf-8') as f:
        instructions_template = f.read().strip()
    
    language_name = "English" if language == "en" else "Hebrew"
    return instructions_template.replace("{LANGUAGE}", language_name)


def create_session_config(language: str) -> dict:
    """
    Create session configuration for OpenAI Realtime API.
    
    Args:
        language: The language code (en or he)
        
    Returns:
        Session configuration dictionary
    """
    instructions = load_instructions(language)
    
    return {
        "type": "realtime",
        "model": REALTIME_MODEL,
        "instructions": instructions,
        "audio": {
            "input": {
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": VAD_THRESHOLD,
                    "prefix_padding_ms": VAD_PREFIX_PADDING_MS,
                    "silence_duration_ms": VAD_SILENCE_DURATION_MS
                },
                "transcription": {
                    "model": TRANSCRIPTION_MODEL,
                    "language": language
                }
            },
            "output": {
                "voice": VOICE
            }
        }
    }


async def create_webrtc_session(sdp: bytes, language: str = DEFAULT_LANGUAGE) -> Tuple[str, int]:
    """
    Create a WebRTC session with OpenAI Realtime API.
    
    Args:
        sdp: The SDP offer from the client
        language: The language code (en or he, default: he)
        
    Returns:
        Tuple of (sdp_answer, status_code)
        
    Raises:
        Exception: If session creation fails
    """
    # Validate language parameter
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    
    sdp_text = sdp.decode('utf-8')
    
    print(f"Received SDP offer from client ({len(sdp_text)} bytes)")
    print(f"Selected language: {language}")
    
    # Create session configuration
    session_config = create_session_config(language)
    
    # Create multipart form data
    async with httpx.AsyncClient() as client:
        files = {
            'sdp': (None, sdp_text, 'application/sdp'),
            'session': (None, json.dumps(session_config), 'application/json')
        }
        
        headers = {
            'Authorization': f"Bearer {OPENAI_API_KEY}"
        }
        
        try:
            response = await client.post(
                OPENAI_REALTIME_URL,
                files=files,
                headers=headers,
                timeout=HTTP_TIMEOUT
            )
            
            response.raise_for_status()
            answer_sdp = response.text
            
            print(f"Received SDP answer from OpenAI ({len(answer_sdp)} bytes)")
            
            return answer_sdp, 200
            
        except httpx.HTTPError as e:
            print(f"Error creating session: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            
            error_message = f"Error: {str(e)}"
            return error_message, 500