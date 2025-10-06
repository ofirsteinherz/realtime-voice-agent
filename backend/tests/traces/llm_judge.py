"""
LLM Judge to evaluate conversation quality and progress
"""
import os
from openai import OpenAI


class ConversationJudge:
    """Evaluates conversations to determine if they should continue"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Load evaluation prompt template
        with open('backend/tests/traces/prompts/judge_evaluation_prompt.md', 'r') as f:
            self.prompt_template = f.read()
    
    def evaluate_conversation(self, conversation, customer_goal, expected_outcome):
        """
        Evaluate if conversation should continue or has completed/failed
        
        Returns:
            dict with keys:
                - should_continue: bool
                - status: 'success' | 'failed' | 'in_progress'
                - reason: str explanation
                - confidence: float (0-1)
        """
        # Format conversation
        conversation_text = self._format_conversation(conversation)
        
        # Build evaluation prompt from template
        prompt = self.prompt_template.replace('{customer_goal}', customer_goal)
        prompt = prompt.replace('{expected_outcome}', expected_outcome)
        prompt = prompt.replace('{conversation_text}', conversation_text)
        
        # Get evaluation
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a conversation quality evaluator. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        return result
    
    def _format_conversation(self, conversation):
        """Format conversation for evaluation"""
        formatted = []
        for msg in conversation:
            role = "Customer" if msg["role"] == "customer" else "Agent"
            content = msg["content"]
            if content:
                formatted.append(f"{role}: {content}")
        return "\n".join(formatted)