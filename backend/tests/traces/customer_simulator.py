"""
Customer simulator using OpenAI to simulate realistic customer behavior
"""
import os
from openai import OpenAI


class CustomerSimulator:
    """Simulates a customer based on test case profile"""
    
    def __init__(self, customer_id, customer_name, story, situation, goal, behavior_notes):
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.story = story
        self.situation = situation
        self.goal = goal
        self.behavior_notes = behavior_notes
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Build system prompt from template
        with open('backend/tests/traces/prompts/customer_simulator_prompt.md', 'r') as f:
            self.system_prompt = f.read()
            self.system_prompt = self.system_prompt.replace('{customer_id}', str(customer_id))
            self.system_prompt = self.system_prompt.replace('{customer_name}', customer_name)
            self.system_prompt = self.system_prompt.replace('{story}', story)
            self.system_prompt = self.system_prompt.replace('{situation}', situation)
            self.system_prompt = self.system_prompt.replace('{goal}', goal)
            self.system_prompt = self.system_prompt.replace('{behavior_notes}', behavior_notes)
    
    def generate_message(self, conversation_history):
        """Generate next customer message based on conversation history"""
        
        # Skip if last message was empty from agent
        if conversation_history and conversation_history[-1]["role"] == "agent" and not conversation_history[-1]["content"].strip():
            # Wait a bit and try again
            return None
        
        # Format conversation history
        history_text = self._format_history(conversation_history)
        prompt = self.system_prompt.replace('{convesation_history}', history_text)
        
        # Build messages for OpenAI
        messages = [{"role": "system", "content": prompt}]
        
        # Add conversation history (skip empty messages)
        for msg in conversation_history:
            if msg["content"].strip():  # Only add non-empty messages
                role = "assistant" if msg["role"] == "agent" else "user"
                messages.append({"role": role, "content": msg["content"]})
        
        # Generate response
        response = self.client.chat.completions.create(
            model="gpt-4o", # We can switch to gpt-5 for better results
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )
        
        return response.choices[0].message.content
    
    def _format_history(self, conversation_history):
        """Format conversation history for prompt"""
        if not conversation_history:
            return "No messages yet. Start the conversation."
        
        history = []
        for msg in conversation_history:
            role = "You" if msg["role"] == "customer" else "Agent"
            history.append(f"{role}: {msg['content']}")
        
        return "\n".join(history)
    