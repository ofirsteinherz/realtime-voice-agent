"""
Test script for pharmacy tools

This script tests the pharmacy tools implementation to ensure everything works correctly.
It requires a running Redis instance with the pharmacy data loaded.
"""

import sys
import json
from tools.pharmacy_tool_orchestrator import execute_pharmacy_tool, list_available_tools


def print_result(tool_name: str, result: str):
    """Pretty print tool execution result"""
    print(f"\n{'='*60}")
    print(f"Tool: {tool_name}")
    print(f"{'='*60}")
    try:
        parsed = json.loads(result)
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    except:
        print(result)
    print(f"{'='*60}\n")


def test_customer_operations():
    """Test customer-related tools"""
    print("\n" + "🧑 TESTING CUSTOMER OPERATIONS ".center(60, "="))
    
    # Test 1: Get customer info
    result = execute_pharmacy_tool("get_customer_info", {"customer_id": 1})
    print_result("get_customer_info(customer_id=1)", result)
    
    # Test 2: Search customer by name
    result = execute_pharmacy_tool("search_customer_by_name", {"name": "Cohen"})
    print_result("search_customer_by_name(name='Cohen')", result)
    
    # Test 3: Get customer prescriptions
    result = execute_pharmacy_tool("get_customer_prescriptions", {"customer_id": 1})
    print_result("get_customer_prescriptions(customer_id=1)", result)


def test_medicine_operations():
    """Test medicine-related tools"""
    print("\n" + "💊 TESTING MEDICINE OPERATIONS ".center(60, "="))
    
    # Test 1: Get medicine info
    result = execute_pharmacy_tool("get_medicine_info", {"medicine_id": 1})
    print_result("get_medicine_info(medicine_id=1)", result)
    
    # Test 2: Search medicine by name
    result = execute_pharmacy_tool("search_medicine_by_name", {"partial_name": "Aca"})
    print_result("search_medicine_by_name(partial_name='Aca')", result)
    
    # Test 3: List all medicines
    result = execute_pharmacy_tool("list_all_medicines", {})
    print_result("list_all_medicines()", result)
    
    # Test 4: Calculate total pills available
    result = execute_pharmacy_tool("calculate_total_pills_available", {"medicine_id": 1})
    print_result("calculate_total_pills_available(medicine_id=1)", result)


def test_dispensing_operations():
    """Test dispensing-related tools"""
    print("\n" + "💉 TESTING DISPENSING OPERATIONS ".center(60, "="))
    
    # Test 1: Check medicine availability
    result = execute_pharmacy_tool("check_medicine_availability", {
        "medicine_id": 1,
        "boxes_needed": 2
    })
    print_result("check_medicine_availability(medicine_id=1, boxes_needed=2)", result)
    
    # Test 2: Validate prescription availability
    result = execute_pharmacy_tool("validate_prescription_availability", {"customer_id": 1})
    print_result("validate_prescription_availability(customer_id=1)", result)
    
    # Note: Not testing dispense_medicine to avoid modifying the database during testing


def test_inventory_operations():
    """Test inventory-related tools"""
    print("\n" + "📦 TESTING INVENTORY OPERATIONS ".center(60, "="))
    
    # Test 1: Get inventory status
    result = execute_pharmacy_tool("get_inventory_status", {"medicine_id": 1})
    print_result("get_inventory_status(medicine_id=1)", result)
    
    # Test 2: Check low stock
    result = execute_pharmacy_tool("check_low_stock", {"threshold": 20})
    print_result("check_low_stock(threshold=20)", result)


def test_error_handling():
    """Test error handling"""
    print("\n" + "⚠️  TESTING ERROR HANDLING ".center(60, "="))
    
    # Test 1: Unknown tool
    result = execute_pharmacy_tool("unknown_tool", {})
    print_result("unknown_tool (should fail)", result)
    
    # Test 2: Invalid customer ID
    result = execute_pharmacy_tool("get_customer_info", {"customer_id": 99999})
    print_result("get_customer_info(customer_id=99999) (should return None)", result)
    
    # Test 3: Missing required parameter
    result = execute_pharmacy_tool("get_customer_info", {})
    print_result("get_customer_info() (missing customer_id)", result)


def test_list_tools():
    """Test tool listing"""
    print("\n" + "📋 LISTING AVAILABLE TOOLS ".center(60, "="))
    tools = list_available_tools()
    print(json.dumps(tools, indent=2))


def main():
    """Run all tests"""
    print("\n" + "🧪 PHARMACY TOOLS TEST SUITE ".center(60, "="))
    print("Testing pharmacy tools implementation...")
    print("Make sure Redis is running with pharmacy data loaded!\n")
    
    try:
        # List available tools
        test_list_tools()
        
        # Run all test categories
        test_customer_operations()
        test_medicine_operations()
        test_dispensing_operations()
        test_inventory_operations()
        test_error_handling()
        
        print("\n" + "✅ ALL TESTS COMPLETED ".center(60, "="))
        print("Review the output above to verify correctness.\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()