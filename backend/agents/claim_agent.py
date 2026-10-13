"""
Claim extraction agent for SocialPulse
"""

import os
import json
import logging
from typing import Dict, Any, List
import google.generativeai as genai
from models.schemas import ClaimAnalysis, AnalysisState

logger = logging.getLogger(__name__)


class ClaimAgent:
    """Agent responsible for extracting and analyzing claims"""
    
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
                logger.warning("GEMINI_API_KEY not found, claim extraction will use demo mode")
                self.demo_mode = True
                return
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini claim agent initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini for claims: {e}")
            self.demo_mode = True
    
    async def process(self, state: AnalysisState) -> AnalysisState:
        """
        Process claim extraction for the given analysis state
        
        Args:
            state: Current analysis state
            
        Returns:
            Updated analysis state with claim analysis
        """
        logger.info(f"Claim agent processing analysis {state.analysis_id}")
        
        try:
            if not state.content_analysis or not state.content_analysis.extracted_text:
                logger.warning(f"No extracted text available for claim analysis {state.analysis_id}")
                state.claim_analysis = ClaimAnalysis(
                    claim="No verifiable claim detected",
                    claim_type="none",
                    entities=[],
                    values=[],
                    requires_verification=False,
                    confidence=0.0
                )
                return state
            
            extracted_text = state.content_analysis.extracted_text
            
            if self.demo_mode:
                claim_data = self._get_demo_claim_analysis(extracted_text)
            else:
                claim_data = await self._extract_claims(extracted_text)
            
            # Create ClaimAnalysis object
            state.claim_analysis = ClaimAnalysis(
                claim=claim_data.get("claim", "No verifiable claim detected"),
                claim_type=claim_data.get("claim_type", "none"),
                entities=claim_data.get("entities", []),
                values=claim_data.get("values", []),
                requires_verification=claim_data.get("requires_verification", False),
                confidence=claim_data.get("confidence", 0.0)
            )
            
            state.progress = 40  # Claim extraction complete
            
            logger.info(f"Claim extraction completed for {state.analysis_id}")
            logger.debug(f"Main claim: {state.claim_analysis.claim}")
            logger.debug(f"Claim type: {state.claim_analysis.claim_type}")
            logger.debug(f"Requires verification: {state.claim_analysis.requires_verification}")
            
            return state
            
        except Exception as e:
            logger.error(f"Claim agent error for {state.analysis_id}: {e}")
            state.error_message = f"Claim extraction failed: {str(e)}"
            return state
    
    async def _extract_claims(self, text: str) -> Dict[str, Any]:
        """Extract claims using Gemini"""
        
        try:
            prompt = f"""
            Analyze this social media text and extract the main factual claim that can be verified:
            
            TEXT: "{text}"
            
            Look for:
            1. Product availability claims
            2. Price/cost claims  
            3. Promotional offers
            4. Product specifications
            5. Company announcements
            6. Event information
            7. Statistical claims
            
            Return your analysis as JSON:
            {{
                "claim": "Main verifiable factual claim (be specific and complete)",
                "claim_type": "product_price | product_availability | promotion | specification | announcement | statistic | event | other | none",
                "entities": ["list", "of", "named", "entities", "in", "claim"],
                "values": ["numerical", "values", "prices", "dates", "etc"],
                "requires_verification": true/false,
                "confidence": 0.85,  // confidence in extraction accuracy
                "reasoning": "Why this was identified as the main claim"
            }}
            
            Guidelines:
            - Focus on the PRIMARY factual claim that matters most
            - Ignore opinion statements and subjective claims
            - Extract specific entities (product names, companies, etc.)
            - Extract numerical values (prices, percentages, dates, quantities)
            - Only set requires_verification=true for factual claims that can be researched
            - If no verifiable claim exists, set claim_type to "none" 
            
            Only return the JSON, no other text.
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            result = json.loads(response_text)
            
            # Validate and clean the response
            result = self._validate_claim_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting claims: {e}")
            return self._get_fallback_claim_analysis()
    
    def _validate_claim_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean claim extraction result"""
        
        valid_types = [
            "product_price", "product_availability", "promotion", "specification", 
            "announcement", "statistic", "event", "other", "none"
        ]
        
        validated = {
            "claim": result.get("claim", "No verifiable claim detected"),
            "claim_type": result.get("claim_type", "none"),
            "entities": result.get("entities", []),
            "values": result.get("values", []),
            "requires_verification": bool(result.get("requires_verification", False)),
            "confidence": float(result.get("confidence", 0.0)),
            "reasoning": result.get("reasoning", "")
        }
        
        # Validate claim type
        if validated["claim_type"] not in valid_types:
            validated["claim_type"] = "other"
        
        # Clamp confidence
        validated["confidence"] = max(0.0, min(1.0, validated["confidence"]))
        
        # Ensure lists are lists
        if not isinstance(validated["entities"], list):
            validated["entities"] = []
        if not isinstance(validated["values"], list):
            validated["values"] = []
        
        return validated
    
    def _get_demo_claim_analysis(self, text: str) -> Dict[str, Any]:
        """Get demo claim analysis"""
        
        # Simple pattern matching for demo
        text_lower = text.lower()
        
        if "iphone" in text_lower and "₹" in text:
            return {
                "claim": "iPhone 17 Pro is available for ₹19,999",
                "claim_type": "product_price",
                "entities": ["iPhone 17 Pro", "Apple"],
                "values": ["₹19,999"],
                "requires_verification": True,
                "confidence": 0.9,
                "reasoning": "DEMO - Clear price claim identified for specific product",
                "demo_data": True
            }
        elif "available" in text_lower and any(char.isdigit() for char in text):
            return {
                "claim": "Product availability claim detected",
                "claim_type": "product_availability", 
                "entities": ["product"],
                "values": [],
                "requires_verification": True,
                "confidence": 0.7,
                "reasoning": "DEMO - Product availability statement found",
                "demo_data": True
            }
        else:
            return {
                "claim": "No specific verifiable claim detected",
                "claim_type": "none",
                "entities": [],
                "values": [],
                "requires_verification": False,
                "confidence": 0.5,
                "reasoning": "DEMO - No clear factual claims identified",
                "demo_data": True
            }
    
    def _get_fallback_claim_analysis(self) -> Dict[str, Any]:
        """Get fallback claim analysis when service fails"""
        return {
            "claim": "Claim extraction service temporarily unavailable",
            "claim_type": "none",
            "entities": [],
            "values": [],
            "requires_verification": False,
            "confidence": 0.0,
            "reasoning": "Service unavailable",
            "error": "Claim extraction service unavailable"
        }


# Global claim agent instance
claim_agent = ClaimAgent()