You are evaluating a conversation between a customer and a pharmacy assistant.

CUSTOMER'S GOAL:
{customer_goal}

EXPECTED OUTCOME:
{expected_outcome}

CONVERSATION SO FAR:
{conversation_text}

Evaluate this conversation and respond with a JSON object:
{{
    "should_continue": true/false,
    "status": "success" | "failed" | "in_progress",
    "reason": "brief explanation",
    "confidence": 0.0-1.0
}}

Guidelines:
- "success": Goal achieved, conversation can end
- "failed": Conversation stuck, error, or cannot achieve goal
- "in_progress": Making progress, should continue
- should_continue: false if status is "success" or "failed"
- Detect loops (same questions/responses repeating)
- Detect if customer is satisfied or frustrated