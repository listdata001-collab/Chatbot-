import os
import logging
from google import genai
from google.genai import types

class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = "gemini-2.5-flash"
    
    def generate_response(self, message, personality="You are a helpful assistant.", conversation_history=None):
        """
        Generate AI response using Google Gemini
        
        Args:
            message (str): User message
            personality (str): Bot personality/system prompt
            conversation_history (list): Previous conversation context
        
        Returns:
            dict: Response with text, tokens_used, and response_time
        """
        try:
            import time
            start_time = time.time()
            
            # Build conversation context
            conversation_prompt = personality + "\n\n"
            
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages for context
                    role = "User" if msg.is_from_user else "Assistant"
                    conversation_prompt += f"{role}: {msg.content}\n"
            
            conversation_prompt += f"User: {message}\nAssistant:"
            
            # Generate response
            response = self.client.models.generate_content(
                model=self.model,
                contents=conversation_prompt
            )
            
            response_time = time.time() - start_time
            
            if response.text:
                return {
                    'text': response.text.strip(),
                    'tokens_used': self._estimate_tokens(conversation_prompt + response.text),
                    'response_time': response_time,
                    'success': True
                }
            else:
                return {
                    'text': "I'm sorry, I couldn't generate a response. Please try again.",
                    'tokens_used': 0,
                    'response_time': response_time,
                    'success': False
                }
                
        except Exception as e:
            logging.error(f"AI Service error: {e}")
            return {
                'text': "I'm experiencing technical difficulties. Please try again later.",
                'tokens_used': 0,
                'response_time': 0,
                'success': False
            }
    
    def _estimate_tokens(self, text):
        """Rough token estimation (1 token ≈ 4 characters)"""
        return len(text) // 4
    
    def validate_api_key(self):
        """Validate if API key is working"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents="Hello"
            )
            return response.text is not None
        except Exception as e:
            logging.error(f"API key validation failed: {e}")
            return False
