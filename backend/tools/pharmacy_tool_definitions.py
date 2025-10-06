"""
Pharmacy Tool Definitions for OpenAI Realtime API

This module contains the tool schemas that define what functions are available
to the AI pharmacist assistant. These definitions follow OpenAI's function calling format.
"""

# All pharmacy tools organized by category
PHARMACY_TOOLS = [
    # ========== Customer Operations ==========
    {
        "type": "function",
        "name": "get_customer_info",
        "description": "Retrieve complete customer information including personal details by customer ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The customer's unique identifier"
                }
            },
            "required": ["customer_id"]
        }
    },
    {
        "type": "function",
        "name": "get_customer_prescriptions",
        "description": "Retrieve all prescriptions for a specific customer with medicine details, including amounts, status, frequency, and expiration dates.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The customer's unique identifier"
                }
            },
            "required": ["customer_id"]
        }
    },
    
    # ========== Medicine Operations ==========
    {
        "type": "function",
        "name": "get_medicine_info",
        "description": "Retrieve complete information about a specific medicine including description, consumption instructions, and pills per unit.",
        "parameters": {
            "type": "object",
            "properties": {
                "medicine_id": {
                    "type": "integer",
                    "description": "The medicine's unique identifier"
                }
            },
            "required": ["medicine_id"]
        }
    },
    {
        "type": "function",
        "name": "search_medicine_by_name",
        "description": "Search for medicines by full or partial name match (case-insensitive).",
        "parameters": {
            "type": "object",
            "properties": {
                "partial_name": {
                    "type": "string",
                    "description": "Full or partial medicine name to search for"
                }
            },
            "required": ["partial_name"]
        }
    },
    {
        "type": "function",
        "name": "calculate_total_pills_available",
        "description": "Calculate the total number of pills available for a medicine based on inventory units and pills per unit.",
        "parameters": {
            "type": "object",
            "properties": {
                "medicine_id": {
                    "type": "integer",
                    "description": "The medicine's unique identifier"
                }
            },
            "required": ["medicine_id"]
        }
    },
    
    # ========== Dispensing Operations ==========
    {
        "type": "function",
        "name": "check_medicine_availability",
        "description": "Check if sufficient quantity of a medicine is available in inventory to fulfill a request.",
        "parameters": {
            "type": "object",
            "properties": {
                "medicine_id": {
                    "type": "integer",
                    "description": "The medicine's unique identifier"
                },
                "boxes_needed": {
                    "type": "integer",
                    "description": "Number of boxes/units needed"
                }
            },
            "required": ["medicine_id", "boxes_needed"]
        }
    },
    {
        "type": "function",
        "name": "dispense_medicine",
        "description": "Dispense medicine to a customer, updating both prescription status and inventory atomically. This is the final step in fulfilling a prescription.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The customer's unique identifier"
                },
                "medicine_id": {
                    "type": "integer",
                    "description": "The medicine's unique identifier"
                },
                "boxes_to_dispense": {
                    "type": "integer",
                    "description": "Number of boxes to dispense"
                }
            },
            "required": ["customer_id", "medicine_id", "boxes_to_dispense"]
        }
    },
    {
        "type": "function",
        "name": "validate_prescription_availability",
        "description": "Check if all medicines in a customer's prescriptions are available in sufficient quantities. Use this before attempting to dispense.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The customer's unique identifier"
                }
            },
            "required": ["customer_id"]
        }
    },
    
    # ========== Conversation & Feedback ==========
    {
        "type": "function",
        "name": "save_review",
        "description": "Save customer feedback/review for a session. Use this to store customer satisfaction feedback.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The customer's unique identifier"
                },
                "review_text": {
                    "type": "string",
                    "description": "Customer's review text"
                }
            },
            "required": ["customer_id", "review_text"]
        }
    }
]