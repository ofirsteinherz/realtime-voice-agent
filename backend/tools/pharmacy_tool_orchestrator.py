"""
Pharmacy Tool Orchestrator

This module routes tool calls from the AI assistant to the appropriate
implementation functions and handles errors consistently.
"""

import json
import logging
from typing import Dict, Any
from .pharmacy_tool_implementations import (
    # Customer Operations
    get_customer_info,
    get_customer_prescriptions,
    # Medicine Operations
    get_medicine_info,
    search_medicine_by_name,
    calculate_total_pills_available,
    # Dispensing Operations
    check_medicine_availability,
    dispense_medicine,
    validate_prescription_availability,
    # Conversation & Feedback
    save_review
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Tool registry mapping tool names to implementation functions
TOOL_REGISTRY = {
    # Customer Operations
    "get_customer_info": get_customer_info,
    "get_customer_prescriptions": get_customer_prescriptions,
    
    # Medicine Operations
    "get_medicine_info": get_medicine_info,
    "search_medicine_by_name": search_medicine_by_name,
    "calculate_total_pills_available": calculate_total_pills_available,
    
    # Dispensing Operations
    "check_medicine_availability": check_medicine_availability,
    "dispense_medicine": dispense_medicine,
    "validate_prescription_availability": validate_prescription_availability,
    
    # Conversation & Feedback
    "save_review": save_review
}


def execute_pharmacy_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a pharmacy tool and return the result as a JSON string.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments from the AI
        
    Returns:
        JSON string containing the tool execution result
    """
    try:
        logger.info(f"Executing tool: {tool_name} with arguments: {arguments}")
        
        # Get the tool function
        tool_func = TOOL_REGISTRY.get(tool_name)
        
        if not tool_func:
            error_result = {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }
            logger.error(f"Unknown tool requested: {tool_name}")
            return json.dumps(error_result, ensure_ascii=False)
        
        # Execute the tool
        result = tool_func(**arguments)
        
        # Handle None results (not found cases)
        if result is None:
            result = {
                "success": False,
                "error": "not_found"
            }
        
        # Return as JSON string
        logger.info(f"Tool {tool_name} executed successfully")
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        # Handle any errors during execution
        error_result = {
            "success": False,
            "error": str(e)
        }
        logger.error(f"Error executing {tool_name}: {e}", exc_info=True)
        return json.dumps(error_result, ensure_ascii=False)