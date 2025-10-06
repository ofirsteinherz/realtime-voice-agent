"""
Tool service for handling pharmacy tool operations.
"""
from typing import Dict, Any, Optional
from tools.pharmacy_tool_definitions import PHARMACY_TOOLS
from tools.pharmacy_tool_orchestrator import execute_pharmacy_tool


def get_available_tools() -> Dict:
    """
    Get the list of available pharmacy tools.
    
    Returns:
        Dictionary containing the tools array
    """
    return {"tools": PHARMACY_TOOLS}


def execute_tool(tool_name: str, arguments: Dict[str, Any], session_id: Optional[str] = None) -> Dict:
    """
    Execute a pharmacy tool with the given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        session_id: Optional session ID to inject for certain tools
        
    Returns:
        Dictionary with success status and result or error
    """
    print(f"Executing tool: {tool_name} with arguments: {arguments}")
    
    # Inject session_id for tools that need it (transparently to the AI)
    if tool_name in ["save_review", "save_conversation"] and session_id:
        arguments["session_id"] = session_id
        print(f"Injected session_id: {session_id}")
    
    try:
        # Execute the tool
        result = execute_pharmacy_tool(tool_name, arguments)
        
        print(f"Tool result: {result}")
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        print(f"Error executing tool: {e}")
        return {
            "success": False,
            "error": str(e)
        }