"""
Test script to retrieve and display all medicines in inventory
"""

import redis
import sys


def connect_redis():
    """Connect to Redis server"""
    try:
        r = redis.Redis(
            host='redis',
            port=6379,
            decode_responses=True
        )
        r.ping()
        print("✓ Successfully connected to Redis\n")
        return r
    except redis.ConnectionError:
        print("✗ Failed to connect to Redis")
        print("Make sure Redis is running: docker-compose up -d redis")
        sys.exit(1)


def get_all_medicines_in_inventory(r):
    """Get all medicines from inventory and print their details"""
    print("="*60)
    print("MEDICINES IN INVENTORY")
    print("="*60)
    
    # Get all inventory keys
    inventory_keys = r.keys('inventory:*')
    
    if not inventory_keys:
        print("No medicines found in inventory.")
        return
    
    print(f"\nTotal medicines in stock: {len(inventory_keys)}\n")
    
    # Sort by medicine_id for consistent ordering
    inventory_keys.sort(key=lambda x: int(x.split(':')[1]))
    
    # Display each medicine
    for i, key in enumerate(inventory_keys, 1):
        inventory = r.hgetall(key)
        medicine_id = inventory.get('medicine_id')
        quantity = inventory.get('quantity')
        
        # Get medicine details
        medicine = r.hgetall(f"medicine:{medicine_id}")
        name = medicine.get('name', 'Unknown')
        description = medicine.get('description', 'No description')
        
        print(f"{i}. {name}")
        print(f"   ID: {medicine_id}")
        print(f"   Quantity: {quantity} units")
        print(f"   Description: {description}")
        print()
    
    print("="*60)


def main():
    """Main function"""
    print("\n" + "="*60)
    print("Redis Inventory Test Script")
    print("="*60 + "\n")
    
    # Connect to Redis
    r = connect_redis()
    
    # Get and display all medicines
    get_all_medicines_in_inventory(r)
    
    print("\n✓ Test completed successfully!\n")


if __name__ == "__main__":
    main()