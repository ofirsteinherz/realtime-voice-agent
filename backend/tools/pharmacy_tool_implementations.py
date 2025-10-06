"""
Pharmacy Tool Implementations

This module contains the actual Python implementations of all pharmacy tools.
All functions interact with Redis to retrieve and manipulate pharmacy data.
"""

import redis
import json
from datetime import datetime
from typing import Optional, List, Dict, Any


# Redis connection singleton
_redis_client = None

def get_redis_connection() -> redis.Redis:
    """
    Get or create Redis connection.
    Uses singleton pattern to avoid creating multiple connections.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host='redis', 
            port=6379, 
            decode_responses=True
        )
    return _redis_client


# ========== Customer Operations ==========

def get_customer_info(customer_id: int) -> Optional[Dict[str, Any]]:
    """
    Get customer information by ID.
    
    Args:
        customer_id: The customer's unique identifier
        
    Returns:
        Customer information dict or None if not found
    """
    try:
        r = get_redis_connection()
        customer = r.hgetall(f'customer:{customer_id}')
        if not customer:
            return None
        return dict(customer)
    except Exception as e:
        return {
            'success': False,
            'error': 'database_error',
            'message': str(e)
        }


def get_customer_prescriptions(customer_id: int) -> List[Dict[str, Any]]:
    """
    Get all prescriptions for a customer with medicine details.
    
    Args:
        customer_id: The customer's unique identifier
        
    Returns:
        List of prescriptions with medicine information
    """
    try:
        r = get_redis_connection()
        prescriptions_json = r.get(f'customer:{customer_id}:prescriptions')
        if not prescriptions_json:
            return []
        
        prescriptions = json.loads(prescriptions_json)
        results = []
        
        for prescription in prescriptions:
            medicine = r.hgetall(f"medicine:{prescription['medicine_id']}")
            prescription['medicine_name'] = medicine.get('name', 'Unknown')
            results.append(prescription)
        
        return results
    except Exception as e:
        return [{
            'success': False,
            'error': 'database_error',
            'message': str(e)
        }]


# ========== Medicine Operations ==========

def get_medicine_info(medicine_id: int) -> Optional[Dict[str, Any]]:
    """
    Get complete medicine information.
    
    Args:
        medicine_id: The medicine's unique identifier
        
    Returns:
        Medicine information dict or None if not found
    """
    try:
        r = get_redis_connection()
        medicine = r.hgetall(f'medicine:{medicine_id}')
        if not medicine:
            return None
        return dict(medicine)
    except Exception as e:
        return {
            'success': False,
            'error': 'database_error',
            'message': str(e)
        }


def search_medicine_by_name(partial_name: str) -> List[Dict[str, Any]]:
    """
    Search for medicines by name (case-insensitive partial match).
    
    Args:
        partial_name: Full or partial medicine name
        
    Returns:
        List of matching medicines
    """
    try:
        r = get_redis_connection()
        medicine_keys = r.keys('medicine:*')
        results = []
        
        for key in medicine_keys:
            medicine = r.hgetall(key)
            if medicine and partial_name.lower() in medicine.get('name', '').lower():
                results.append(dict(medicine))
        
        return results
    except Exception as e:
        return [{
            'success': False,
            'error': 'database_error',
            'message': str(e)
        }]


def calculate_total_pills_available(medicine_id: int) -> Optional[Dict[str, Any]]:
    """
    Calculate total pills available for a medicine.
    
    Args:
        medicine_id: The medicine's unique identifier
        
    Returns:
        Dict with pills calculation or None if not found
    """
    try:
        r = get_redis_connection()
        medicine = r.hgetall(f"medicine:{medicine_id}")
        inventory = r.hgetall(f"inventory:{medicine_id}")
        
        if not medicine or not inventory:
            return None
        
        pills_per_unit = int(medicine.get('pills_per_unit', 0))
        units_in_stock = int(inventory.get('quantity', 0))
        total_pills = pills_per_unit * units_in_stock
        
        return {
            'medicine_id': medicine_id,
            'medicine_name': medicine.get('name'),
            'units_in_stock': units_in_stock,
            'pills_per_unit': pills_per_unit,
            'total_pills': total_pills
        }
    except Exception as e:
        return {
            'success': False,
            'error': 'database_error',
            'message': str(e)
        }


# ========== Dispensing Operations ==========

def check_medicine_availability(medicine_id: int, boxes_needed: int) -> Dict[str, Any]:
    """
    Check if medicine is available in required quantity.
    
    Args:
        medicine_id: The medicine's unique identifier
        boxes_needed: Number of boxes/units needed
        
    Returns:
        Availability information dict
    """
    try:
        r = get_redis_connection()
        medicine = r.hgetall(f"medicine:{medicine_id}")
        inventory = r.hgetall(f"inventory:{medicine_id}")
        
        if not medicine or not inventory:
            return {
                'available': False,
                'message': 'Medicine not found'
            }
        
        pills_per_unit = int(medicine.get('pills_per_unit', 0))
        boxes_available = int(inventory.get('quantity', 0))
        pills_available = boxes_available * pills_per_unit
        pills_needed = boxes_needed * pills_per_unit
        
        return {
            'medicine_id': medicine_id,
            'medicine_name': medicine.get('name'),
            'boxes_needed': boxes_needed,
            'boxes_available': boxes_available,
            'pills_needed': pills_needed,
            'pills_available': pills_available,
            'available': True,
            'can_fulfill': boxes_available >= boxes_needed
        }
    except Exception as e:
        return {
            'success': False,
            'error': 'database_error',
            'message': str(e)
        }


def dispense_medicine(customer_id: int, medicine_id: int, boxes_to_dispense: int) -> Dict[str, Any]:
    """
    Dispense medicine and update both prescription and inventory.
    
    Args:
        customer_id: The customer's unique identifier
        medicine_id: The medicine's unique identifier
        boxes_to_dispense: Number of boxes to dispense
        
    Returns:
        Dispensing result dict
    """
    try:
        r = get_redis_connection()
        
        # Check availability
        availability = check_medicine_availability(medicine_id, boxes_to_dispense)
        if not availability.get('can_fulfill'):
            return {
                'success': False,
                'message': 'Insufficient stock',
                'boxes_needed': boxes_to_dispense,
                'boxes_available': availability.get('boxes_available', 0)
            }
        
        # Update inventory
        inventory = r.hgetall(f"inventory:{medicine_id}")
        current_stock = int(inventory.get('quantity', 0))
        new_stock = current_stock - boxes_to_dispense
        r.hset(f"inventory:{medicine_id}", 'quantity', new_stock)
        
        # Update prescription status
        prescriptions_json = r.get(f'customer:{customer_id}:prescriptions')
        prescription_status = 'no_prescription'
        
        if prescriptions_json:
            prescriptions = json.loads(prescriptions_json)
            for prescription in prescriptions:
                if prescription['medicine_id'] == medicine_id:
                    prescription['dispensed_amount'] = prescription.get('dispensed_amount', 0) + boxes_to_dispense
                    if prescription['dispensed_amount'] >= prescription['amount']:
                        prescription['status'] = 'fulfilled'
                        prescription_status = 'fulfilled'
                    else:
                        prescription['status'] = 'partial'
                        prescription_status = 'partial'
            r.set(f'customer:{customer_id}:prescriptions', json.dumps(prescriptions))
        
        medicine = r.hgetall(f"medicine:{medicine_id}")
        pills_per_unit = int(medicine.get('pills_per_unit', 0))
        
        return {
            'success': True,
            'customer_id': customer_id,
            'medicine_id': medicine_id,
            'medicine_name': medicine.get('name'),
            'boxes_dispensed': boxes_to_dispense,
            'pills_dispensed': boxes_to_dispense * pills_per_unit,
            'remaining_boxes_in_inventory': new_stock,
            'prescription_status': prescription_status
        }
    except Exception as e:
        return {
            'success': False,
            'error': 'database_error',
            'message': str(e)
        }


def validate_prescription_availability(customer_id: int) -> Dict[str, Any]:
    """
    Check if all prescribed medicines are available.
    
    Args:
        customer_id: The customer's unique identifier
        
    Returns:
        Validation result with availability for each prescription
    """
    try:
        prescriptions = get_customer_prescriptions(customer_id)
        if not prescriptions:
            return {
                'customer_id': customer_id,
                'all_available': False,
                'message': 'No prescriptions found'
            }
        
        results = []
        unavailable = []
        
        for prescription in prescriptions:
            # Skip already fulfilled prescriptions
            if prescription.get('status') == 'fulfilled':
                continue
                
            medicine_id = prescription['medicine_id']
            needed = prescription['amount'] - prescription.get('dispensed_amount', 0)
            
            availability = check_medicine_availability(medicine_id, needed)
            
            result = {
                'medicine_id': medicine_id,
                'medicine_name': prescription.get('medicine_name'),
                'needed': needed,
                'available': availability.get('boxes_available', 0),
                'can_fulfill': availability.get('can_fulfill', False)
            }
            
            results.append(result)
            if not result['can_fulfill']:
                unavailable.append(result)
        
        return {
            'customer_id': customer_id,
            'all_available': len(unavailable) == 0,
            'prescriptions': results,
            'unavailable_medicines': unavailable
        }
    except Exception as e:
        return {
            'success': False,
            'error': 'database_error',
            'message': str(e)
        }


# ========== Conversation & Feedback ==========

def save_review(session_id: str, customer_id: int, review_text: str) -> Dict[str, Any]:
    """
    Save a customer review.
    
    Args:
        session_id: Unique session identifier (UUID)
        customer_id: The customer's unique identifier
        review_text: Customer's review text
        
    Returns:
        Save result dict
    """
    try:
        r = get_redis_connection()
        review_data = {
            'session_id': session_id,
            'customer_id': str(customer_id),
            'review_text': review_text,
            'timestamp': datetime.now().isoformat()
        }
        
        r.hset(f"review:{session_id}", mapping=review_data)
        
        return {
            'success': True,
            'session_id': session_id,
            'customer_id': customer_id,
            'timestamp': review_data['timestamp']
        }
    except Exception as e:
        return {
            'success': False,
            'error': 'database_error',
            'message': str(e)
        }

