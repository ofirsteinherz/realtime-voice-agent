# 📖 Function Reference

Complete documentation for all 9 pharmacy tools.

## Customer Operations

### `get_customer_info`

**Purpose:** Retrieve complete customer information by customer ID.

**Inputs:**
- `customer_id` (integer, required) - The customer's unique identifier

**Output Schema:**
```python
{
    "id": str,                    # Customer ID
    "full_name": str,             # Customer's full name
    "phone_number": str,          # Contact phone number
    "date_of_birth": str,         # DOB in YYYY-MM-DD format
    "address": str                # Customer's address
}
```
<details>
<summary><b>Use Example</b></summary>

```
TOOL CALL: get_customer_info
{
    "customer_id": 101
}
```

```
TOOL RESPONSE: get_customer_info
{
    "id": "101",
    "full_name": "דוד כהן",
    "phone_number": "052-1234567",
    "date_of_birth": "1975-03-15",
    "address": "רחוב הרצל 25, תל אביב"
}
```
</details>

**Error Handling:**
- Returns `None` if customer not found
- Returns error dict on database failure:
  ```python
  {"success": False, "error": "database_error", "message": str}
  ```
**Fallback Behavior:**
- Returns None for non-existent customers (allows graceful handling by caller)
- Catches and wraps all Redis exceptions

---

### `get_customer_prescriptions`

**Purpose:** Retrieve all prescriptions for a customer with enriched medicine details.

**Inputs:**
- `customer_id` (integer, required) - The customer's unique identifier

**Output Schema:**
```python
[
    {
        "prescription_id": str,
        "medicine_id": int,
        "medicine_name": str,         # Enriched from medicine table
        "amount": int,                # Total boxes prescribed
        "dispensed_amount": int,      # Boxes already dispensed
        "status": str,                # "pending", "partial", "fulfilled"
        "frequency": str,             # E.g., "twice daily"
        "expiration_date": str        # YYYY-MM-DD format
    },
    ...
]
```
<details>
<summary><b>Use Example</b></summary>

```
TOOL CALL: get_customer_prescriptions
{
    "customer_id": 101
}
```

```
TOOL RESPONSE: get_customer_prescriptions
[
    {
        "prescription_id": "RX-2024-001",
        "medicine_id": 5,
        "medicine_name": "נורופן",
        "amount": 3,
        "dispensed_amount": 1,
        "status": "partial",
        "frequency": "כל 8 שעות",
        "expiration_date": "2024-12-31"
    },
    {
        "prescription_id": "RX-2024-002",
        "medicine_id": 12,
        "medicine_name": "אקמול",
        "amount": 2,
        "dispensed_amount": 0,
        "status": "pending",
        "frequency": "פעמיים ביום",
        "expiration_date": "2024-11-30"
    }
]
```
</details>

**Error Handling:**
- Returns empty list `[]` if no prescriptions found
- Returns list with error dict on database failure:
  ```python
  [{"success": False, "error": "database_error", "message": str}]
  ```
**Fallback Behavior:**
- Sets medicine_name to "Unknown" if medicine not found
- Returns empty list for customers without prescriptions

---

## Medicine Operations

### `get_medicine_info`

**Purpose:** Retrieve complete information about a specific medicine.

**Inputs:**
- `medicine_id` (integer, required) - The medicine's unique identifier

**Output Schema:**
```python
{
    "id": str,
    "name": str,                      # Medicine name
    "description": str,               # Usage and effects
    "how_to_consume": str,           # Consumption instructions
    "pills_per_unit": str            # Pills per box/unit
}
```
<details>
<summary><b>Use Example</b></summary>

```
TOOL CALL: get_medicine_info
{
    "medicine_id": 5
}
```

```
TOOL RESPONSE: get_medicine_info
{
    "id": "5",
    "name": "נורופן",
    "description": "משכך כאבים ומפחית חום ודלקת. מכיל איבופרופן 400 מ״ג",
    "how_to_consume": "יש לקחת טבליה אחת כל 8 שעות עם מים. לא לעבור על 1200 מ״ג ביום",
    "pills_per_unit": "20"
}
```
</details>

**Error Handling:**
- Returns `None` if medicine not found
- Returns error dict on database failure:
  ```python
  {"success": False, "error": "database_error", "message": str}
  ```
**Fallback Behavior:**
- Returns None for non-existent medicines
- Catches all Redis exceptions

---

### `search_medicine_by_name`

**Purpose:** Search medicines using case-insensitive partial name matching.

**Inputs:**
- `partial_name` (string, required) - Full or partial medicine name

**Output Schema:**
```python
[
    {
        "id": str,
        "name": str,
        "description": str,
        "how_to_consume": str,
        "pills_per_unit": str
    },
    ...
]
```
<details>
<summary><b>Use Example</b></summary>

```
TOOL CALL: search_medicine_by_name
{
    "partial_name": "נורו"
}
```

```
TOOL RESPONSE: search_medicine_by_name
[
    {
        "id": "5",
        "name": "נורופן",
        "description": "משכך כאבים ומפחית חום ודלקת. מכיל איבופרופן 400 מ״ג",
        "how_to_consume": "יש לקחת טבליה אחת כל 8 שעות עם מים",
        "pills_per_unit": "20"
    },
    {
        "id": "18",
        "name": "נורופן פורטה",
        "description": "נורופן בצורת אבקה לספיגה מהירה",
        "how_to_consume": "להמיס בכוס מים ולשתות",
        "pills_per_unit": "12"
    }
]
```
</details>

**Error Handling:**
- Returns list with error dict on database failure:
  ```python
  [{"success": False, "error": "database_error", "message": str}]
  ```
**Fallback Behavior:**
- Returns empty list `[]` if no matches found
- Case-insensitive matching

---

### `calculate_total_pills_available`

**Purpose:** Calculate total pills available based on inventory units and pills per unit.

**Inputs:**
- `medicine_id` (integer, required) - The medicine's unique identifier

**Output Schema:**
```python
{
    "medicine_id": int,
    "medicine_name": str,
    "units_in_stock": int,           # Number of boxes
    "pills_per_unit": int,
    "total_pills": int               # units * pills_per_unit
}
```
<details>
<summary><b>Use Example</b></summary>

```
TOOL CALL: calculate_total_pills_available
{
    "medicine_id": 5
}
```

```
TOOL RESPONSE: calculate_total_pills_available
{
    "medicine_id": 5,
    "medicine_name": "נורופן",
    "units_in_stock": 15,
    "pills_per_unit": 20,
    "total_pills": 300
}
```
</details>

**Error Handling:**
- Returns `None` if medicine or inventory not found
- Returns error dict on database failure:
  ```python
  {"success": False, "error": "database_error", "message": str}
  ```
**Fallback Behavior:**
- Returns None for non-existent medicines
- Defaults to 0 for missing pills_per_unit or quantity values

---

## Dispensing Operations

### `check_medicine_availability`

**Purpose:** Verify if sufficient quantity of medicine is available to fulfill a request.

**Inputs:**
- `medicine_id` (integer, required) - The medicine's unique identifier
- `boxes_needed` (integer, required) - Number of boxes/units required

**Output Schema:**
```python
{
    "medicine_id": int,
    "medicine_name": str,
    "boxes_needed": int,
    "boxes_available": int,
    "pills_needed": int,
    "pills_available": int,
    "available": bool,               # Medicine exists
    "can_fulfill": bool              # Sufficient quantity
}
```
<details>
<summary><b>Use Example</b></summary>

```
TOOL CALL: check_medicine_availability
{
    "medicine_id": 5,
    "boxes_needed": 2
}
```

```
TOOL RESPONSE: check_medicine_availability
{
    "medicine_id": 5,
    "medicine_name": "נורופן",
    "boxes_needed": 2,
    "boxes_available": 15,
    "pills_needed": 40,
    "pills_available": 300,
    "available": true,
    "can_fulfill": true
}
```
</details>

**Error Handling:**
- Returns error structure if medicine not found:
  ```python
  {"available": False, "message": "Medicine not found"}
  ```
- Returns error dict on database failure:
  ```python
  {"success": False, "error": "database_error", "message": str}
  ```
**Fallback Behavior:**
- Calculates pills based on boxes × pills_per_unit
- Returns detailed availability info even if insufficient stock

---

### `dispense_medicine`

**Purpose:** Dispense medicine to customer, atomically updating prescription status and inventory.

**Inputs:**
- `customer_id` (integer, required) - The customer's unique identifier
- `medicine_id` (integer, required) - The medicine's unique identifier
- `boxes_to_dispense` (integer, required) - Number of boxes to dispense

**Output Schema (Success):**
```python
{
    "success": True,
    "customer_id": int,
    "medicine_id": int,
    "medicine_name": str,
    "boxes_dispensed": int,
    "pills_dispensed": int,
    "remaining_boxes_in_inventory": int,
    "prescription_status": str       # "fulfilled", "partial", "no_prescription"
}
```
<details>
<summary><b>Use Example</b></summary>

```
TOOL CALL: dispense_medicine
{
    "customer_id": 101,
    "medicine_id": 5,
    "boxes_to_dispense": 2
}
```

```
TOOL RESPONSE: dispense_medicine
{
    "success": true,
    "customer_id": 101,
    "medicine_id": 5,
    "medicine_name": "נורופן",
    "boxes_dispensed": 2,
    "pills_dispensed": 40,
    "remaining_boxes_in_inventory": 13,
    "prescription_status": "fulfilled"
}
```
</details>

**Output Schema (Failure):**
```python
{
    "success": False,
    "message": str,                  # Error description
    "boxes_needed": int,
    "boxes_available": int
}
```
**Error Handling:**
- Checks availability before dispensing
- Returns failure with stock info if insufficient
- Returns error dict on database failure:
  ```python
  {"success": False, "error": "database_error", "message": str}
  ```
**Fallback Behavior:**
- Atomically updates both inventory and prescription
- Tracks dispensed amount for partial fulfillment
- Sets prescription_status based on fulfillment:
  - "fulfilled" - All prescribed amount dispensed
  - "partial" - Some dispensed, more needed
  - "no_prescription" - No prescription found

---

### `validate_prescription_availability`

**Purpose:** Check if all prescribed medicines for a customer are available in sufficient quantities.

**Inputs:**
- `customer_id` (integer, required) - The customer's unique identifier

**Output Schema:**
```python
{
    "customer_id": int,
    "all_available": bool,
    "prescriptions": [
        {
            "medicine_id": int,
            "medicine_name": str,
            "needed": int,              # Boxes still needed
            "available": int,           # Boxes in stock
            "can_fulfill": bool
        },
        ...
    ],
    "unavailable_medicines": [...]     # Subset that can't be fulfilled
}
```
<details>
<summary><b>Use Example</b></summary>

```
TOOL CALL: validate_prescription_availability
{
    "customer_id": 101
}
```

```
TOOL RESPONSE: validate_prescription_availability
{
    "customer_id": 101,
    "all_available": false,
    "prescriptions": [
        {
            "medicine_id": 5,
            "medicine_name": "נורופן",
            "needed": 2,
            "available": 15,
            "can_fulfill": true
        },
        {
            "medicine_id": 23,
            "medicine_name": "אנטיביוטיקה מיוחדת",
            "needed": 1,
            "available": 0,
            "can_fulfill": false
        }
    ],
    "unavailable_medicines": [
        {
            "medicine_id": 23,
            "medicine_name": "אנטיביוטיקה מיוחדת",
            "needed": 1,
            "available": 0,
            "can_fulfill": false
        }
    ]
}
```
</details>

**Error Handling:**
- Returns structure with message if no prescriptions:
  ```python
  {"customer_id": int, "all_available": False, "message": "No prescriptions found"}
  ```
- Returns error dict on database failure:
  ```python
  {"success": False, "error": "database_error", "message": str}
  ```
**Fallback Behavior:**
- Skips already fulfilled prescriptions
- Calculates needed = total - dispensed_amount
- Returns detailed unavailable list for decision making

---

## Conversation & Feedback

### `save_review`

**Purpose:** Persist customer feedback/review for a session.

**Inputs:**
- `session_id` (string, required) - Unique session identifier (UUID)
- `customer_id` (integer, required) - The customer's unique identifier
- `review_text` (string, required) - Customer's review text

**Output Schema (Success):**
```python
{
    "success": True,
    "session_id": str,
    "customer_id": int,
    "timestamp": str                # ISO 8601 format
}
```
<details>
<summary><b>Use Example</b></summary>

```
TOOL CALL: save_review
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "customer_id": 101,
    "review_text": "שירות מצוין! קיבלתי את התרופות במהירות והצוות היה מאוד עוזר"
}
```

```
TOOL RESPONSE: save_review
{
    "success": true,
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "customer_id": 101,
    "timestamp": "2024-01-15T14:30:00Z"
}
```
</details>

**Error Handling:**
- Returns error dict on database failure:
  ```python
  {"success": False, "error": "database_error", "message": str}
  ```
**Fallback Behavior:**
- Auto-generates timestamp
- Stores in Redis hash for easy retrieval
- Overwrites existing review for same session_id