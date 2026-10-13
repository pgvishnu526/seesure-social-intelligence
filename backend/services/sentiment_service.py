"""
Sentiment analysis service using Gemini
"""

import os
import logging
from typing import Dict, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)


class SentimentService:
    """Sentiment analysis service"""
    
    def __init__(self):
        self.model = None
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        
        if not self.demo_mode:
            self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Gemini client"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY not found, sentiment analysis will use demo mode")
                self.demo_mode = True
                return
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini sentiment service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini for sentiment: {e}")
            self.demo_mode = True
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of the given text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        if self.demo_mode:
            return self._get_demo_sentiment(text)
        
        if not text or not text.strip():
            return {
                "label": "neutral",
                "confidence": 0.0,
                "explanation": "No text provided for analysis"
            }
        
        try:
            prompt = f"""
            Analyze the sentiment of this social media content text:
            
            "{text}"
            
            Provide your analysis as JSON with these exact fields:
            {{
                "label": "positive" | "negative" | "neutral",
                "confidence": 0.85,  // confidence score between 0.0 and 1.0
                "explanation": "Brief explanation of why this sentiment was detected"
            }}
            
            Guidelines:
            - "positive": Optimistic, encouraging, happy, excited, grateful
            - "negative": Angry, sad, frustrated, critical, hostile, fearful
            - "neutral": Factual, informational, balanced, or unclear sentiment
            - Be conservative with confidence scores
            - Consider context of social media and promotional content
            - Factor in emojis and informal language if present
            
            Only return the JSON object, no other text.
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            import json
            result = json.loads(response_text)
            
            # Validate and clean the response
            result = self._validate_sentiment_result(result)
            
            logger.info(f"Sentiment analysis completed: {result['label']} ({result['confidence']:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return self._get_fallback_sentiment()
    
    def _validate_sentiment_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean sentiment analysis result"""
        valid_labels = ["positive", "negative", "neutral"]
        
        # Ensure label is valid
        label = result.get("label", "neutral").lower()
        if label not in valid_labels:
            label = "neutral"
        
        # Ensure confidence is a float between 0 and 1
        try:
            confidence = float(result.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.5
        
        # Ensure explanation is a string
        explanation = result.get("explanation", "No explanation provided")
        if not isinstance(explanation, str):
            explanation = "No explanation provided"
        
        return {
            "label": label,
            "confidence": confidence,
            "explanation": explanation
        }
    
    def _get_demo_sentiment(self, text: str) -> Dict[str, Any]:
        """Return demo sentiment analysis"""
        # Simple rule-based demo sentiment
        text_lower = text.lower()
        
        positive_words = ["great", "awesome", "excellent", "amazing", "love", "best", "fantastic", "wonderful", "perfect"]
        negative_words = ["terrible", "awful", "hate", "worst", "bad", "horrible", "disgusting", "scam", "fake"]
        promotional_words = ["deal", "offer", "discount", "sale", "limited", "exclusive", "available"]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        promotional_count = sum(1 for word in promotional_words if word in text_lower)
        
        if promotional_count > 0:
            # Promotional content tends to be neutral with positive framing
            return {
                "label": "neutral",
                "confidence": 0.75,
                "explanation": "DEMO - Promotional content with neutral to slightly positive tone",
                "demo_data": True
            }
        elif positive_count > negative_count:
            return {
                "label": "positive", 
                "confidence": 0.8,
                "explanation": "DEMO - Positive language and tone detected",
                "demo_data": True
            }
        elif negative_count > positive_count:
            return {
                "label": "negative",
                "confidence": 0.8, 
                "explanation": "DEMO - Negative language and tone detected",
                "demo_data": True
            }
        else:
            return {
                "label": "neutral",
                "confidence": 0.6,
                "explanation": "DEMO - Neutral or balanced tone",
                "demo_data": True
            }
    
    def _get_fallback_sentiment(self) -> Dict[str, Any]:
        """Return fallback sentiment when service fails"""
        return {
            "label": "neutral",
            "confidence": 0.0,
            "explanation": "Sentiment analysis service temporarily unavailable",
            "error": "Service unavailable"
        }


# Global sentiment service instance
sentiment_service = SentimentService()