# Pharmacy Tools Implementation

This directory contains the complete implementation of the pharmacist agent tools for the voice bot application.

## 🛠️ Components

### 1. pharmacy_tool_definitions.py

Contains the OpenAI Realtime API function definitions for all 9 pharmacy tools:

**Customer Operations (2 tools)**
- `get_customer_info` - Get customer details by ID
- `get_customer_prescriptions` - Get all customer prescriptions

**Medicine Operations (3 tools)**
- `get_medicine_info` - Get medicine details by ID
- `search_medicine_by_name` - Search medicines by name
- `calculate_total_pills_available` - Calculate total pills in stock

**Dispensing Operations (3 tools)**
- `check_medicine_availability` - Check if medicine is in stock
- `dispense_medicine` - Dispense medicine to customer
- `validate_prescription_availability` - Validate all prescriptions available

**Conversation & Feedback (1 tool)**
- `save_review` - Save customer feedback

### 2. pharmacy_tool_implementations.py

Python implementations that interact with Redis database:

- All 9 tool functions with full error handling
- Redis connection management (singleton pattern)
- Type hints for better IDE support
- Consistent error response format
- JSON serialization for complex data

### 3. pharmacy_tool_orchestrator.py

Routes tool calls to implementations:

- `execute_pharmacy_tool(tool_name, arguments)` - Main execution handler
- `TOOL_REGISTRY` - Mapping of tool names to functions
- Automatic type conversion for arguments
- Comprehensive error handling
- Logging for debugging

## 🔄 Data Flow

```
AI Assistant
    ↓ (tool call)
server.py /execute-tool endpoint
    ↓
pharmacy_tool_orchestrator.py
    ↓ (lookup in TOOL_REGISTRY)
pharmacy_tool_implementations.py
    ↓ (query)
Redis Database
    ↓ (data)
pharmacy_tool_implementations.py
    ↓ (JSON result)
pharmacy_tool_orchestrator.py
    ↓ (response)
server.py
    ↓ (return)
AI Assistant
```

## 📝 Usage Examples

### From Python

```python
from tools import execute_pharmacy_tool

# Get customer info
result = execute_pharmacy_tool("get_customer_info", {"customer_id": 1})
print(result)  # JSON string

# Search medicines
result = execute_pharmacy_tool("search_medicine_by_name", {"partial_name": "Acamol"})
print(result)  # JSON string with list of medicines
```

### From Server Endpoint

```bash
curl -X POST http://localhost:8000/execute-tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_customer_info",
    "arguments": {"customer_id": 1}
  }'
```

## 🧪 Testing

Run the test suite:

```bash
cd backend
python test_pharmacy_tools.py
```

The test suite validates:
- Customer operations
- Medicine operations
- Dispensing operations
- Error handling
- Tool listing

## 🔧 Configuration

### Redis Connection

Default connection settings in `pharmacy_tool_implementations.py`:

```python
redis.Redis(
    host='redis',      # Docker service name
    port=6379,
    decode_responses=True
)
```

For local testing outside Docker, change `host='redis'` to `host='localhost'`.

## 📊 Error Handling

All tools return consistent error responses:

```json
{
  "success": false,
  "error": "error_type",
  "message": "Human readable error message"
}
```

Error types:
- `database_error` - Redis connection or query error
- `unknown_tool` - Tool name not found
- `invalid_arguments` - Missing or invalid parameters
- `execution_error` - Unexpected error during execution
- `not_found` - Resource not found (returns None)

## 🚀 Integration

The tools are automatically integrated into the server via:

```python
# server.py
from tools import PHARMACY_TOOLS, execute_pharmacy_tool

@app.get("/tools")
async def get_tools():
    return JSONResponse(content={"tools": PHARMACY_TOOLS})

@app.post("/execute-tool")
async def execute_tool(request: Request):
    result = execute_pharmacy_tool(tool_name, arguments)
    return JSONResponse(content={"success": True, "result": result})
```

## 📚 Related Documentation

- [README_TOOLS.md](../../README_TOOLS.md) - Complete tool specifications
- [README_REDIS.md](../../README_REDIS.md) - Redis data structure
- [backend/server.py](../server.py) - Server integration

## 🔐 Security Notes

- All customer and medicine IDs are validated
- Input parameters are type-checked and sanitized
- Database errors are caught and logged
- No sensitive data in error messages
- All dispensing operations are logged

## 🎯 Future Enhancements

Potential additions:
- Transaction support for atomic operations
- Caching layer for frequently accessed data
- Rate limiting for tool calls
- Audit trail for all dispensing operations
- Real-time inventory alerts via pub/sub
- Performance metrics and monitoring