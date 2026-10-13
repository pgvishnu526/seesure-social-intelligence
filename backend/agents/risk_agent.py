"""
Risk assessment agent for SocialPulse
"""

import os
import json
import logging
from typing import List
import google.generativeai as genai
from models.schemas import RiskAssessment, RiskLevel, AnalysisState

logger = logging.getLogger(__name__)


class RiskAgent:
    """Agent responsible for risk assessment"""
    
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
                logger.warning("GEMINI_API_KEY not found, risk assessment will use demo mode")
                self.demo_mode = True
                return
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini risk agent initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini for risk assessment: {e}")
            self.demo_mode = True
    
    async def process(self, state: AnalysisState) -> AnalysisState:
        """
        Process risk assessment for the given analysis state
        
        Args:
            state: Current analysis state
            
        Returns:
            Updated analysis state with risk assessment
        """
        logger.info(f"Risk agent processing analysis {state.analysis_id}")
        
        try:
            if self.demo_mode:
                risk_data = self._get_demo_risk_assessment(state)
            else:
                risk_data = await self._calculate_risk_score(state)
            
            # Determine risk level based on score
            score = risk_data["score"]
            if score <= 30:
                level = RiskLevel.LOW
            elif score <= 60:
                level = RiskLevel.MEDIUM
            elif score <= 80:
                level = RiskLevel.HIGH
            else:
                level = RiskLevel.CRITICAL
            
            state.risk_assessment = RiskAssessment(
                score=score,
                level=level,
                reasons=risk_data.get("reasons", []),
                methodology=risk_data.get("methodology", "AI-assisted risk assessment"),
                confidence=risk_data.get("confidence", 0.0)
            )
            
            state.progress = 85  # Risk assessment complete
            
            logger.info(f"Risk assessment completed for {state.analysis_id}")
            logger.info(f"Risk score: {score}/100 ({level})")
            
            return state
            
        except Exception as e:
            logger.error(f"Risk agent error for {state.analysis_id}: {e}")
            state.error_message = f"Risk assessment failed: {str(e)}"
            return state
    
    async def _calculate_risk_score(self, state: AnalysisState) -> dict:
        """Calculate risk score using AI analysis"""
        
        try:
            # Prepare context for risk assessment
            context = self._prepare_risk_context(state)
            
            prompt = f"""
            Analyze the following information and calculate a comprehensive risk score (0-100) for this social media content:

            {context}

            Consider these risk factors:
            1. Claim verification status (supporting vs contradicting evidence)
            2. Source reliability and authority
            3. Media authenticity indicators  
            4. Content category and type
            5. Promotional vs informational nature
            6. Potential for financial harm
            7. Likelihood of misinformation
            8. Evidence quality and quantity

            Risk Score Guidelines:
            - 0-30: LOW - Minimal risk, appears legitimate
            - 31-60: MEDIUM - Some concerns, warrants caution  
            - 61-80: HIGH - Significant red flags, likely problematic
            - 81-100: CRITICAL - Strong indicators of fraud/misinformation

            Return your assessment as JSON:
            {{
                "score": 78,
                "reasons": [
                    "List of specific risk factors identified",
                    "Each reason should be clear and actionable"
                ],
                "methodology": "Brief explanation of assessment approach",
                "confidence": 0.85,
                "key_concerns": "Primary concerns summary"
            }}

            Be objective and evidence-based. Explain your reasoning clearly.
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            result = json.loads(response_text)
            
            # Validate the response
            result = self._validate_risk_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return self._get_fallback_risk_assessment()
    
    def _prepare_risk_context(self, state: AnalysisState) -> str:
        """Prepare context information for risk assessment"""
        
        context_parts = []
        
        # Content information
        if state.content_analysis:
            context_parts.append(f"CONTENT:")
            context_parts.append(f"- Type: {state.content_analysis.content_type}")
            context_parts.append(f"- Category: {state.content_analysis.category}")
            context_parts.append(f"- Extracted text: {state.content_analysis.extracted_text[:200]}...")
        
        # Claim information  
        if state.claim_analysis:
            context_parts.append(f"CLAIM:")
            context_parts.append(f"- Main claim: {state.claim_analysis.claim}")
            context_parts.append(f"- Claim type: {state.claim_analysis.claim_type}")
            context_parts.append(f"- Requires verification: {state.claim_analysis.requires_verification}")
            context_parts.append(f"- Entities: {', '.join(state.claim_analysis.entities)}")
        
        # Research results
        if state.research_results:
            supporting_count = len(state.research_results.supporting_evidence)
            contradicting_count = len(state.research_results.contradicting_evidence)
            context_parts.append(f"RESEARCH:")
            context_parts.append(f"- Total sources: {state.research_results.total_sources}")
            context_parts.append(f"- Supporting evidence: {supporting_count} items")
            context_parts.append(f"- Contradicting evidence: {contradicting_count} items")
            context_parts.append(f"- Summary: {state.research_results.research_summary}")
        
        # Media analysis
        if state.media_analysis:
            context_parts.append(f"MEDIA ANALYSIS:")
            context_parts.append(f"- Authenticity score: {state.media_analysis.authenticity_score}")
            context_parts.append(f"- Indicators count: {len(state.media_analysis.indicators)}")
            context_parts.append(f"- Explanation: {state.media_analysis.explanation}")
        
        # Sentiment
        if state.sentiment_analysis:
            context_parts.append(f"SENTIMENT:")
            context_parts.append(f"- Label: {state.sentiment_analysis.label}")
            context_parts.append(f"- Confidence: {state.sentiment_analysis.confidence}")
        
        return "\n".join(context_parts)
    
    def _validate_risk_result(self, result: dict) -> dict:
        """Validate and clean risk assessment result"""
        
        validated = {
            "score": int(result.get("score", 50)),
            "reasons": result.get("reasons", []),
            "methodology": result.get("methodology", "AI-assisted risk assessment"),
            "confidence": float(result.get("confidence", 0.0))
        }
        
        # Clamp score to valid range
        validated["score"] = max(0, min(100, validated["score"]))
        
        # Clamp confidence
        validated["confidence"] = max(0.0, min(1.0, validated["confidence"]))
        
        # Ensure reasons is a list
        if not isinstance(validated["reasons"], list):
            validated["reasons"] = []
        
        return validated
    
    def _get_demo_risk_assessment(self, state: AnalysisState) -> dict:
        """Get demo risk assessment"""
        
        # Calculate demo score based on available data
        score = 50  # Base score
        reasons = []
        
        # Adjust based on claim analysis
        if state.claim_analysis:
            if state.claim_analysis.claim_type == "product_price":
                score += 20
                reasons.append("DEMO - Product pricing claim requires verification")
            
            if state.claim_analysis.requires_verification:
                score += 10
                reasons.append("DEMO - Claim requires external verification")
        
        # Adjust based on research
        if state.research_results:
            contradicting = len(state.research_results.contradicting_evidence)
            supporting = len(state.research_results.supporting_evidence)
            
            if contradicting > supporting:
                score += 15
                reasons.append("DEMO - More contradicting than supporting evidence found")
            elif supporting > contradicting:
                score -= 10
                reasons.append("DEMO - Supporting evidence outweighs contradicting evidence")
        
        # Adjust based on media analysis
        if state.media_analysis and state.media_analysis.authenticity_score < 0.7:
            score += 10
            reasons.append("DEMO - Media authenticity concerns detected")
        
        # Demo-specific reasons
        if "iphone" in (state.content_analysis.extracted_text or "").lower():
            reasons.extend([
                "DEMO - Pricing significantly below market rate",
                "DEMO - Limited contact information provided", 
                "DEMO - Matches pattern of known promotional scams"
            ])
        
        return {
            "score": max(0, min(100, score)),
            "reasons": reasons,
            "methodology": "DEMO - Multi-factor AI risk assessment simulation",
            "confidence": 0.8,
            "demo_data": True
        }
    
    def _get_fallback_risk_assessment(self) -> dict:
        """Get fallback risk assessment when service fails"""
        return {
            "score": 50,
            "reasons": ["Risk assessment service temporarily unavailable"],
            "methodology": "Fallback assessment",
            "confidence": 0.0,
            "error": "Risk assessment service unavailable"
        }


# Global risk agent instance
risk_agent = RiskAgent()