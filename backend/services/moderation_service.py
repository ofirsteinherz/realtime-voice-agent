"""
Text moderation service using OpenAI and Llama Prompt Guard.
"""
import asyncio
import time
import json
from datetime import datetime
from typing import Dict, Optional
import httpx
from config import (
    OPENAI_API_KEY,
    GROQ_API_KEY,
    OPENAI_MODERATION_URL,
    GROQ_CHAT_URL,
    OPENAI_MODERATION_MODEL,
    LLAMA_GUARD_MODEL,
    MODERATION_THRESHOLD,
    LLAMA_ATTACK_THRESHOLD,
    HTTP_TIMEOUT,
)
from services.conversation_service import get_redis_connection


async def check_openai_moderation(message: str) -> Dict:
    """
    Test message against OpenAI Moderation API.
    
    Args:
        message: The text to moderate
        
    Returns:
        Dictionary with moderation results
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    data = {
        "model": OPENAI_MODERATION_MODEL,
        "input": message
    }
    
    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(OPENAI_MODERATION_URL, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
        response_time = time.time() - start_time
        
        # Extract relevant information
        if result.get("results"):
            first_result = result["results"][0]
            category_scores = first_result.get("category_scores", {})
            
            # Filter scores > threshold and find the highest
            filtered_scores = {k: v for k, v in category_scores.items() if v > MODERATION_THRESHOLD}
            top_category = max(filtered_scores.items(), key=lambda x: x[1]) if filtered_scores else (None, 0)
            
            # Custom flagging logic: flag if any score > threshold
            custom_flagged = any(score > MODERATION_THRESHOLD for score in category_scores.values())
            
            return {
                "service": "openai",
                "flagged": custom_flagged,
                "category_scores": category_scores,
                "top_category": top_category[0] if top_category[0] else None,
                "top_score": top_category[1],
                "response_time": response_time
            }
    except Exception as e:
        response_time = time.time() - start_time if 'start_time' in locals() else 0
        return {
            "service": "openai",
            "error": str(e),
            "response_time": response_time
        }
    
    return {
        "service": "openai",
        "error": "No results returned",
        "response_time": 0
    }


async def check_llama_prompt_guard(message: str) -> Dict:
    """
    Test message against Groq Llama Prompt Guard.
    
    The model returns a probability score:
    - Close to 0.0: Safe/benign content
    - Close to 1.0: Malicious/attack content
    - Threshold: 0.5 (scores >= 0.5 are considered attacks)
    
    Args:
        message: The text to check for prompt injection attacks
        
    Returns:
        Dictionary with detection results
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    
    data = {
        "model": LLAMA_GUARD_MODEL,
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ]
    }
    
    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(GROQ_CHAT_URL, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
        response_time = time.time() - start_time
        
        # Extract the response content (probability score)
        if result.get("choices"):
            content = result["choices"][0]["message"]["content"]
            try:
                # Parse the score as a float
                score = float(content)
                # Threshold: >= 0.5 is considered an attack
                detected = score >= LLAMA_ATTACK_THRESHOLD
                return {
                    "service": "llama",
                    "score": score,
                    "detected_attack": detected,
                    "response_time": response_time
                }
            except ValueError:
                return {
                    "service": "llama",
                    "error": f"Could not parse score: {content}",
                    "response_time": response_time
                }
    except Exception as e:
        response_time = time.time() - start_time if 'start_time' in locals() else 0
        return {
            "service": "llama",
            "error": str(e),
            "response_time": response_time
        }
    
    return {
        "service": "llama",
        "error": "No results returned",
        "response_time": 0
    }


async def save_moderation_attempt(
    session_id: str,
    message: str,
    openai_result: Dict,
    llama_result: Dict
) -> Dict:
    """
    Save moderation attempt to Redis.
    
    Args:
        session_id: Session identifier
        message: The text that was moderated
        openai_result: OpenAI moderation result
        llama_result: Llama Guard result
        
    Returns:
        Dictionary with save status
    """
    try:
        r = get_redis_connection()
        
        # Determine if flagged by either service
        flagged = (
            openai_result.get("flagged", False) or
            llama_result.get("detected_attack", False)
        )
        
        # Create attempt data
        attempt_data = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "openai": {
                "flagged": openai_result.get("flagged"),
                "top_category": openai_result.get("top_category"),
                "top_score": openai_result.get("top_score")
            },
            "llama": {
                "detected_attack": llama_result.get("detected_attack"),
                "score": llama_result.get("score")
            },
            "flagged": flagged
        }
        
        # Increment global moderation count
        r.incr("moderation:count")
        
        # Append to list for this session
        r.rpush(
            f"moderation:{session_id}",
            json.dumps(attempt_data, ensure_ascii=False)
        )
        
        # Set TTL of 7 days on the key
        r.expire(f"moderation:{session_id}", 7 * 24 * 3600)
        
        return {"success": True, "flagged": flagged}
    except Exception as e:
        print(f"Error saving moderation attempt: {e}")
        return {"success": False, "error": str(e)}


async def moderate_text(text: str, session_id: Optional[str] = None) -> Dict:
    """
    Moderate text using both OpenAI and Llama Prompt Guard concurrently.
    
    Args:
        text: The text to moderate
        session_id: Optional session ID for logging moderation attempts
        
    Returns:
        Dictionary with results from both services
    """
    # Run both moderation checks concurrently
    openai_result, llama_result = await asyncio.gather(
        check_openai_moderation(text),
        check_llama_prompt_guard(text)
    )
    
    # Save to database ONLY if flagged and session_id provided
    if session_id:
        # Check if either service flagged the content
        flagged = (
            openai_result.get("flagged", False) or
            llama_result.get("detected_attack", False)
        )
        
        if flagged:
            await save_moderation_attempt(session_id, text, openai_result, llama_result)
    
    return {
        "openai_result": openai_result,
        "llama_result": llama_result
    }