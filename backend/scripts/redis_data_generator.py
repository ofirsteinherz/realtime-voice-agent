"""
Redis Data Generator Script - Pharmacy Management System
This script generates sample data for customers, medicines, reviews, and conversation history
"""

import redis
import json
import random
from datetime import datetime, timedelta
import uuid


def connect_redis():
    """Connect to Redis server"""
    try:
        # Connect to Redis (docker service name)
        r = redis.Redis(
            host='redis',
            port=6379,
            decode_responses=True
        )
        r.ping()
        print("Successfully connected to Redis")
        return r
    except redis.ConnectionError:
        print("Failed to connect to Redis")
        return None


def get_predefined_customers():
    """Get predefined customer data for testing based on test_cases.json"""
    return {
        1: {'customer_id': 1, 'full_name': 'Sarah Chen', 'gender': 'Female'},
        2: {'customer_id': 2, 'full_name': 'Michael Rodriguez', 'gender': 'Male'},
        3: {'customer_id': 3, 'full_name': 'Lisa Thompson', 'gender': 'Female'},
        4: {'customer_id': 4, 'full_name': 'David Kim', 'gender': 'Male'},
        5: {'customer_id': 5, 'full_name': 'Emma Watson', 'gender': 'Female'},
        6: {'customer_id': 6, 'full_name': 'Robert Johnson', 'gender': 'Male'},
    }


def generate_customer_data(customer_id):
    """Get predefined customer data"""
    predefined = get_predefined_customers()
    if customer_id in predefined:
        return predefined[customer_id]
    
    # Return None if customer_id is not in predefined list
    return None




def get_predefined_prescriptions(customer_id):
    """Get predefined prescriptions for testing based on test_cases.json"""
    # Helper to create prescription with specific ID
    def make_prescription(prescription_id, medicine_id, amount, frequency, duration):
        created_date = datetime.now() - timedelta(days=5)
        expiration_date = created_date + timedelta(days=60)
        return {
            'prescription_id': prescription_id,
            'medicine_id': medicine_id,
            'amount': amount,
            'dispensed_amount': 0,
            'status': 'active',
            'frequency': frequency,
            'duration': duration,
            'created_date': created_date.strftime('%Y-%m-%d'),
            'expiration_date': expiration_date.strftime('%Y-%m-%d')
        }
    
    prescriptions = {
        # Customer 1: Sarah Chen - Blood pressure medication patient
        1: [
            make_prescription('1', 7, 2, 'Once a day', '30 days'),  # Concor (blood pressure)
            make_prescription(str(uuid.uuid4()), 1, 1, 'As needed', '30 days'),  # Acamol
        ],
        # Customer 2: Michael Rodriguez - Multiple chronic conditions (diabetes, cholesterol)
        2: [
            make_prescription(str(uuid.uuid4()), 8, 2, 'Twice a day', '30 days'),  # Metformin (diabetes)
            make_prescription(str(uuid.uuid4()), 7, 1, 'Once a day', '30 days'),  # Concor (blood pressure)
            make_prescription(str(uuid.uuid4()), 4, 1, 'Once a day', '30 days'),  # Vitamin D
        ],
        # Customer 3: Lisa Thompson - Headache medication
        3: [
            make_prescription(str(uuid.uuid4()), 1, 1, 'As needed', '30 days'),  # Acamol
            make_prescription(str(uuid.uuid4()), 3, 1, 'As needed', '14 days'),  # Optalgin
        ],
        # Customer 4: David Kim - Bulk purchase testing
        4: [
            make_prescription(str(uuid.uuid4()), 1, 3, 'As needed', '90 days'),  # Acamol (3 boxes)
        ],
        # Customer 5: Emma Watson - Insufficient stock scenario (needs 100 pills = 13 boxes * 8 pills)
        5: [
            make_prescription(str(uuid.uuid4()), 1, 13, 'Three times a day', '30 days'),  # Acamol (13 boxes = 104 pills)
        ],
        # Customer 6: Robert Johnson - NO prescriptions (empty list for testing)
        6: [],
    }
    
    return prescriptions.get(customer_id, [])


def generate_medicine_data(medicine_id):
    """Generate sample medicine data"""
    medicines = [
        {
            'name': 'Acamol',
            'description': 'Pain reliever and fever reducer',
            'consumption_info': 'Take with water, can be taken with or without food',
            'pills_per_unit': 8
        },
        {
            'name': 'Nurofen',
            'description': 'Anti-inflammatory and pain relief medication',
            'consumption_info': 'Take after food with a full glass of water',
            'pills_per_unit': 10
        },
        {
            'name': 'Optalgin',
            'description': 'Strong pain reliever',
            'consumption_info': 'Do not take on an empty stomach',
            'pills_per_unit': 12
        },
        {
            'name': 'Vitamin D',
            'description': 'Vitamin D supplement for bone strengthening',
            'consumption_info': 'Take with a fatty meal for better absorption',
            'pills_per_unit': 30
        },
        {
            'name': 'Zithromax',
            'description': 'Antibiotic for treating bacterial infections',
            'consumption_info': 'Complete the entire course even if feeling better',
            'pills_per_unit': 6
        },
        {
            'name': 'Lustral',
            'description': 'Medication for depression and anxiety',
            'consumption_info': 'Take at the same time each day, morning or evening',
            'pills_per_unit': 28
        },
        {
            'name': 'Concor',
            'description': 'Blood pressure lowering medication',
            'consumption_info': 'Take in the morning before breakfast',
            'pills_per_unit': 30
        },
        {
            'name': 'Metformin',
            'description': 'Medication for treating type 2 diabetes',
            'consumption_info': 'Take with meals to reduce side effects',
            'pills_per_unit': 60
        }
    ]
    
    medicine = medicines[medicine_id - 1] if medicine_id <= len(medicines) else medicines[0]
    
    return {
        'medicine_id': medicine_id,
        'name': medicine['name'],
        'description': medicine['description'],
        'consumption_info': medicine['consumption_info'],
        'pills_per_unit': medicine['pills_per_unit']
    }


def generate_conversation_history():
    """Generate sample conversation history"""
    conversations = [
        [
            {"role": "user", "content": "Hello, I want to know when to take my medications"},
            {"role": "assistant", "content": "Hello! I'd be happy to help. What's the name of the medicine?"},
            {"role": "user", "content": "Acamol"},
            {"role": "assistant", "content": "Acamol can be taken up to 4 times a day, with water. Can be taken with or without food."}
        ],
        [
            {"role": "user", "content": "I have a headache, what should I take?"},
            {"role": "assistant", "content": "I see you have Optalgin and Acamol in your prescription. I recommend starting with Acamol."},
            {"role": "user", "content": "Thank you!"}
        ],
        [
            {"role": "user", "content": "I forgot to take my medicine in the morning"},
            {"role": "assistant", "content": "No worries. Take it now and continue as usual tomorrow."}
        ]
    ]
    
    return random.choice(conversations)


def insert_data(r, num_customers=10, num_medicines=8):
    """Insert generated data into Redis"""
    
    print("\n" + "="*60)
    print("Inserting data into pharmacy management system")
    print("="*60)
    
    # Insert medicines first
    print(f"\nInserting {num_medicines} medicines...")
    medicine_ids = list(range(1, num_medicines + 1))
    
    for medicine_id in medicine_ids:
        medicine_data = generate_medicine_data(medicine_id)
        key = f"medicine:{medicine_id}"
        r.hset(key, mapping=medicine_data)
        print(f"  ✓ Medicine {medicine_id}: {medicine_data['name']}")
    
    # Insert inventory
    print(f"\nInserting inventory data...")
    for medicine_id in medicine_ids:
        # Set specific inventory levels for testing
        if medicine_id == 1:  # Acamol - exactly 50 units for insufficient stock test
            quantity = 50
        else:
            quantity = 100  # Other medicines have good stock
        
        inventory_data = {
            'medicine_id': medicine_id,
            'quantity': quantity
        }
        r.hset(f"inventory:{medicine_id}", mapping=inventory_data)
        medicine = r.hgetall(f"medicine:{medicine_id}")
        print(f"  ✓ Medicine inventory {medicine.get('name')}: {inventory_data['quantity']} units")
    
    # Insert customers with prescriptions (only predefined customers)
    print(f"\nInserting {num_customers} customers...")
    for customer_id in range(1, num_customers + 1):
        # Customer basic data
        customer_data = generate_customer_data(customer_id)
        if not customer_data:
            continue  # Skip if customer not in predefined list
        
        key = f"customer:{customer_id}"
        r.hset(key, mapping=customer_data)
        
        # Get predefined prescriptions
        prescriptions = get_predefined_prescriptions(customer_id)
        
        # Store prescriptions as JSON
        r.set(f"customer:{customer_id}:prescriptions", json.dumps(prescriptions, ensure_ascii=False))
        
        num_prescriptions = len(prescriptions)
        print(f"  ✓ Customer {customer_id}: {customer_data['full_name']} ({num_prescriptions} prescriptions)")
    
    # Insert reviews/opinions
    print(f"\nInserting reviews...")
    reviews = [
        "Excellent service! The pharmacist was very patient and explained everything about the medications.",
        "I received the medications quickly. Highly recommend!",
        "The wait was a bit long but the service was good.",
        "The pharmacist helped me find a cheaper alternative to the medication. Thank you very much!",
        "Clean and organized place. Friendly and professional staff."
    ]
    
    for i in range(min(5, num_customers)):
        session_id = str(uuid.uuid4())
        customer_id = random.randint(1, num_customers)
        
        review_data = {
            'session_id': session_id,
            'customer_id': customer_id,
            'review_text': random.choice(reviews),
            'timestamp': datetime.now().isoformat()
        }
        
        r.hset(f"review:{session_id}", mapping=review_data)
        print(f"  ✓ Review from customer {customer_id}")
    
    # Insert conversation history
    print(f"\nInserting conversation history...")
    for i in range(min(3, num_customers)):
        session_id = str(uuid.uuid4())
        customer_id = random.randint(1, num_customers)
        
        conversation_data = {
            'session_id': session_id,
            'customer_id': customer_id,
            'conversation_history': json.dumps(generate_conversation_history(), ensure_ascii=False),
            'timestamp': datetime.now().isoformat()
        }
        
        r.hset(f"conversation:{session_id}", mapping=conversation_data)
        print(f"  ✓ Conversation of customer {customer_id}")
    
    # Add counters
    r.set('total_customers', num_customers)
    r.set('total_medicines', num_medicines)
    
    print("\n✅ Data insertion completed successfully!")


def initialize_test_results_table(r):
    """Initialize test results table structure (empty table)"""
    # Set counter for tracking number of test results
    r.set('test_results:count', 0)
    print("\n✅ Test results table initialized (empty)")


def initialize_moderation_table(r):
    """Initialize moderation table structure (empty table)"""
    # Set counter for tracking total moderation attempts across all sessions
    r.set('moderation:count', 0)
    print("✅ Moderation table initialized (empty)")
    print("   Pattern: moderation:{session_id} - stores moderation attempts per session")


def display_stats(r):
    """Display database statistics"""
    print("\n" + "="*60)
    print("Database Statistics")
    print("="*60)
    
    # Get all keys count
    total_keys = len(r.keys('*'))
    print(f"\nTotal keys in system: {total_keys}")
    
    # Display counters
    print(f"\nCounters:")
    print(f"  Total customers: {r.get('total_customers')}")
    print(f"  Total medicines: {r.get('total_medicines')}")
    
    # Display sample customer
    print(f"\nSample customer (customer:1):")
    customer_data = r.hgetall('customer:1')
    for key, value in customer_data.items():
        print(f"  {key}: {value}")
    
    # Display customer prescriptions
    prescriptions = r.get('customer:1:prescriptions')
    if prescriptions:
        print(f"\nPrescriptions for customer 1:")
        prescriptions_list = json.loads(prescriptions)
        for i, prescription in enumerate(prescriptions_list, 1):
            medicine = r.hgetall(f"medicine:{prescription['medicine_id']}")
            print(f"  {i}. {medicine.get('name', 'Unknown')}:")
            print(f"     - ID: {prescription.get('prescription_id', 'N/A')[:8]}...")
            print(f"     - Amount: {prescription['amount']} boxes, Dispensed: {prescription.get('dispensed_amount', 0)}")
            print(f"     - Status: {prescription.get('status', 'N/A')}")
            print(f"     - Frequency: {prescription['frequency']}, Duration: {prescription['duration']}")
            print(f"     - Created: {prescription.get('created_date', 'N/A')}, Expires: {prescription.get('expiration_date', 'N/A')}")
    
    # Display sample medicine
    print(f"\nSample medicine (medicine:1):")
    medicine_data = r.hgetall('medicine:1')
    for key, value in medicine_data.items():
        print(f"  {key}: {value}")
    
    # Display reviews count
    review_keys = r.keys('review:*')
    print(f"\nTotal reviews: {len(review_keys)}")
    
    # Display conversation count
    conversation_keys = r.keys('conversation:*')
    print(f"Total conversations: {len(conversation_keys)}")
    
    if conversation_keys:
        print(f"\nSample conversation:")
        sample_conv = r.hgetall(conversation_keys[0])
        conv_history = json.loads(sample_conv.get('conversation_history', '[]'))
        for msg in conv_history[:2]:
            print(f"  {msg['role']}: {msg['content']}")
    
    # Display inventory
    print(f"\nSample inventory:")
    inventory_keys = r.keys('inventory:*')
    for i, key in enumerate(inventory_keys[:3], 1):
        inventory = r.hgetall(key)
        medicine = r.hgetall(f"medicine:{inventory['medicine_id']}")
        print(f"  {medicine.get('name', 'Unknown')}: {inventory['quantity']} units in stock")
    
    print(f"\nTotal items in inventory: {len(inventory_keys)}")
    
    print("\n" + "="*60)


def main():
    """Main function"""
    print("\n" + "="*60)
    print("Pharmacy Management System Data Generator")
    print("MODE: Predefined Test Data (based on test_cases.json)")
    print("="*60)
    
    # Connect to Redis
    r = connect_redis()
    if not r:
        return
    
    # Clear existing data (optional)
    print("\nClearing existing data...")
    r.flushdb()
    print("✓ Data cleared")
    
    # Insert new data (6 predefined customers, 8 medicines)
    insert_data(r, num_customers=6, num_medicines=8)
    
    # Initialize test results table (empty)
    initialize_test_results_table(r)
    
    # Initialize moderation table (empty)
    initialize_moderation_table(r)
    
    # Display statistics
    display_stats(r)
    
    print("\n✅ Script completed successfully!")
    print("\n📋 Data is configured for test_cases.json scenarios:")
    print("  - 6 predefined customers (Sarah Chen, Michael Rodriguez, etc.)")
    print("  - Customer 6 (Robert Johnson) has NO prescriptions")
    print("  - Customer 5 (Emma Watson) needs 104 Acamol pills")
    print("  - Acamol inventory set to 50 units (400 pills) for insufficient stock test")
    print("  - Customer 1 has prescription_id='1' for testing")
    print("\nData is saved in volume: ./redis-data")
    print("Redis will save data every 60 seconds if at least one key changed")
    print("\nTo start Redis: docker-compose up -d redis")
    print("To view data: docker-compose exec redis redis-cli")


if __name__ == "__main__":
    main()