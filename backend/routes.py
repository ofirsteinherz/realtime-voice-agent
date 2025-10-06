"""
API routes for the backend service.
All route handlers - thin layer that calls services.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response, JSONResponse
from services.file_service import get_index_html, get_static_file_content
from services.tool_service import get_available_tools, execute_tool
from services.conversation_service import save_conversation_data
from services.moderation_service import moderate_text
from services.session_service import create_webrtc_session

router = APIRouter()


@router.get("/")
async def get_index():
    """Serve the HTML interface"""
    html_content = get_index_html()
    return HTMLResponse(content=html_content)


@router.get("/tools")
async def get_tools():
    """Return the list of available tools for the frontend to send via session.update"""
    tools = get_available_tools()
    return JSONResponse(content=tools)


@router.post("/execute-tool")
async def execute_tool_endpoint(request: Request):
    """
    Execute a tool call from the Realtime API.
    Receives tool name and arguments, executes the tool, and returns the result.
    """
    try:
        data = await request.json()
        tool_name = data.get("name")
        arguments = data.get("arguments", {})
        session_id = data.get("session_id")  # Extract session_id from frontend
        
        result = execute_tool(tool_name, arguments, session_id)
        
        if result.get("success"):
            return JSONResponse(content=result)
        else:
            return JSONResponse(content=result, status_code=500)
        
    except Exception as e:
        print(f"Error in execute-tool endpoint: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e)
            },
            status_code=500
        )


@router.post("/save-conversation")
async def save_conversation_endpoint(request: Request):
    """
    Save conversation history to Redis.
    Called automatically from frontend after each conversation event.
    """
    try:
        data = await request.json()
        session_id = data.get("session_id")
        customer_id = data.get("customer_id")  # Can be None
        messages = data.get("messages", [])
        
        result = save_conversation_data(session_id, customer_id, messages)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        print(f"Error in save-conversation endpoint: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e)
            },
            status_code=500
        )


@router.post("/moderate")
async def moderate_endpoint(request: Request):
    """Moderate text using both OpenAI and Llama Prompt Guard concurrently"""
    try:
        data = await request.json()
        text = data.get("text", "")
        session_id = data.get("session_id")
        
        if not text:
            return JSONResponse(
                content={"success": False, "error": "Text cannot be empty"},
                status_code=400
            )
        
        result = await moderate_text(text, session_id)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        print(f"Error in moderate endpoint: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e)
            },
            status_code=500
        )


@router.post("/session")
async def create_session_endpoint(request: Request, language: str = "he"):
    """
    Create a WebRTC session with OpenAI Realtime API.
    Accepts SDP offer from client and returns SDP answer.
    Supports language parameter: 'en' or 'he' (default: Hebrew)
    """
    # Get SDP from request body
    sdp = await request.body()
    
    # Create session
    answer_sdp, status_code = await create_webrtc_session(sdp, language)
    
    if status_code == 200:
        return Response(content=answer_sdp, media_type='application/sdp')
    else:
        return Response(content=answer_sdp, status_code=status_code)


@router.get("/{filename:path}")
async def get_static_file(filename: str):
    """Serve static files from frontend directory (including subdirectories)"""
    result = get_static_file_content(filename)
    
    if result is None:
        return Response(content="Not found", status_code=404)
    
    content, media_type = result
    return Response(content=content, media_type=media_type)