"""
Report generation agent for SocialPulse
"""

import os
import json
import logging
from typing import List
import google.generativeai as genai
from models.schemas import IntelligenceReport, AnalysisState

logger = logging.getLogger(__name__)


class ReportAgent:
    """Agent responsible for generating final intelligence reports"""
    
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
                logger.warning("GEMINI_API_KEY not found, report generation will use demo mode")
                self.demo_mode = True
                return
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini report agent initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini for reports: {e}")
            self.demo_mode = True
    
    async def process(self, state: AnalysisState) -> AnalysisState:
        """
        Process report generation for the given analysis state
        
        Args:
            state: Current analysis state
            
        Returns:
            Updated analysis state with final report
        """
        logger.info(f"Report agent processing analysis {state.analysis_id}")
        
        try:
            if self.demo_mode:
                report_data = self._get_demo_report(state)
            else:
                report_data = await self._generate_report(state)
            
            state.final_report = IntelligenceReport(
                summary=report_data.get("summary", "Analysis completed"),
                recommended_action=report_data.get("recommended_action", "No specific action required"),
                key_findings=report_data.get("key_findings", []),
                disclaimer=report_data.get("disclaimer", "This analysis is AI-assisted and should be used as guidance only")
            )
            
            state.progress = 100  # Report generation complete
            
            logger.info(f"Report generation completed for {state.analysis_id}")
            
            return state
            
        except Exception as e:
            logger.error(f"Report agent error for {state.analysis_id}: {e}")
            state.error_message = f"Report generation failed: {str(e)}"
            return state
    
    async def _generate_report(self, state: AnalysisState) -> dict:
        """Generate comprehensive report using AI"""
        
        try:
            # Prepare comprehensive context
            context = self._prepare_report_context(state)
            
            prompt = f"""
            Generate a comprehensive intelligence report based on this analysis:

            {context}

            Create a professional report suitable for an analyst or decision-maker:

            {{
                "summary": "2-3 paragraph executive summary of findings",
                "recommended_action": "Specific actionable recommendation",
                "key_findings": [
                    "List of 3-5 most important findings",
                    "Each finding should be specific and evidence-based"
                ],
                "disclaimer": "Appropriate disclaimer about limitations"
            }}

            Guidelines for the report:
            - Professional, objective tone
            - Clear and actionable language  
            - Evidence-based conclusions
            - Appropriate level of caution
            - Useful for non-technical audience
            - Highlight both risks and legitimate aspects
            - Be specific about evidence quality

            For the recommended action:
            - If high risk: Recommend avoiding/verifying through official channels
            - If medium risk: Recommend caution and additional verification
            - If low risk: May proceed but with standard precautions
            - Always suggest verification methods when applicable

            Return only the JSON object.
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
            result = self._validate_report_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return self._get_fallback_report()
    
    def _prepare_report_context(self, state: AnalysisState) -> str:
        """Prepare comprehensive context for report generation"""
        
        context_parts = ["ANALYSIS SUMMARY:"]
        
        # Basic information
        context_parts.append(f"Analysis ID: {state.analysis_id}")
        
        # Content summary
        if state.content_analysis:
            context_parts.append(f"\nCONTENT:")
            context_parts.append(f"- Type: {state.content_analysis.content_type}")
            context_parts.append(f"- Category: {state.content_analysis.category}")
            context_parts.append(f"- Text: {state.content_analysis.extracted_text}")
            context_parts.append(f"- Entities: {', '.join(state.content_analysis.entities)}")
        
        # Claim analysis
        if state.claim_analysis:
            context_parts.append(f"\nCLAIM ANALYSIS:")
            context_parts.append(f"- Main claim: {state.claim_analysis.claim}")
            context_parts.append(f"- Type: {state.claim_analysis.claim_type}")
            context_parts.append(f"- Requires verification: {state.claim_analysis.requires_verification}")
            context_parts.append(f"- Confidence: {state.claim_analysis.confidence:.2f}")
        
        # Sentiment
        if state.sentiment_analysis:
            context_parts.append(f"\nSENTIMENT:")
            context_parts.append(f"- {state.sentiment_analysis.label.upper()} ({state.sentiment_analysis.confidence:.2f} confidence)")
            context_parts.append(f"- {state.sentiment_analysis.explanation}")
        
        # Media analysis
        if state.media_analysis:
            context_parts.append(f"\nMEDIA ANALYSIS:")
            context_parts.append(f"- Authenticity score: {state.media_analysis.authenticity_score:.2f}")
            context_parts.append(f"- {state.media_analysis.explanation}")
            if state.media_analysis.indicators:
                context_parts.append("- Indicators:")
                for indicator in state.media_analysis.indicators:
                    context_parts.append(f"  • {indicator.type}: {indicator.description} ({indicator.risk_level})")
        
        # Research findings
        if state.research_results:
            context_parts.append(f"\nRESEARCH FINDINGS:")
            context_parts.append(f"- Total sources: {state.research_results.total_sources}")
            context_parts.append(f"- Supporting evidence: {len(state.research_results.supporting_evidence)} items")
            context_parts.append(f"- Contradicting evidence: {len(state.research_results.contradicting_evidence)} items")
            context_parts.append(f"- Summary: {state.research_results.research_summary}")
            
            if state.research_results.supporting_evidence:
                context_parts.append("- Supporting evidence:")
                for evidence in state.research_results.supporting_evidence[:3]:  # Top 3
                    context_parts.append(f"  • {evidence.summary} (reliability: {evidence.reliability_score:.2f})")
            
            if state.research_results.contradicting_evidence:
                context_parts.append("- Contradicting evidence:")
                for evidence in state.research_results.contradicting_evidence[:3]:  # Top 3
                    context_parts.append(f"  • {evidence.summary} (reliability: {evidence.reliability_score:.2f})")
        
        # Risk assessment
        if state.risk_assessment:
            context_parts.append(f"\nRISK ASSESSMENT:")
            context_parts.append(f"- Score: {state.risk_assessment.score}/100 ({state.risk_assessment.level})")
            context_parts.append(f"- Confidence: {state.risk_assessment.confidence:.2f}")
            if state.risk_assessment.reasons:
                context_parts.append("- Risk factors:")
                for reason in state.risk_assessment.reasons:
                    context_parts.append(f"  • {reason}")
        
        return "\n".join(context_parts)
    
    def _validate_report_result(self, result: dict) -> dict:
        """Validate and clean report generation result"""
        
        validated = {
            "summary": result.get("summary", "Analysis completed successfully."),
            "recommended_action": result.get("recommended_action", "Review findings and proceed with appropriate caution."),
            "key_findings": result.get("key_findings", []),
            "disclaimer": result.get("disclaimer", "This analysis is AI-assisted and should be used as guidance only. Human judgment and additional verification may be required.")
        }
        
        # Ensure key_findings is a list
        if not isinstance(validated["key_findings"], list):
            validated["key_findings"] = []
        
        # Ensure strings are not empty
        for key in ["summary", "recommended_action", "disclaimer"]:
            if not validated[key] or not isinstance(validated[key], str):
                validated[key] = f"Information unavailable for {key}"
        
        return validated
    
    def _get_demo_report(self, state: AnalysisState) -> dict:
        """Generate demo report"""
        
        # Get risk level for tailored recommendations
        risk_level = "MEDIUM"
        if state.risk_assessment:
            risk_level = state.risk_assessment.level
        
        summary = f"""
        Analysis of social media content claiming iPhone 17 Pro availability at ₹19,999 reveals significant concerns. 
        The claimed price is substantially below official retail pricing and matches patterns commonly associated with 
        fraudulent promotional offers. Research indicates no authorized retailers are offering the product at this price point.
        
        While the content appears to be a promotional post rather than sophisticated manipulation, the pricing claim 
        raises red flags. Media analysis shows typical promotional styling but no strong technical manipulation indicators.
        However, the combination of unrealistic pricing and limited verification sources suggests this may be a scam.
        """
        
        if risk_level in ["HIGH", "CRITICAL"]:
            recommended_action = "Do not engage with this offer. Verify any iPhone purchase through official Apple channels or authorized retailers. Be cautious of similar offers that seem too good to be true."
        elif risk_level == "MEDIUM":
            recommended_action = "Exercise caution and verify this claim through official channels before proceeding. Contact Apple or authorized retailers to confirm pricing and availability."
        else:
            recommended_action = "While some concerns exist, proceed with standard verification practices. Always purchase from authorized retailers."
        
        key_findings = [
            "DEMO - Claimed price (₹19,999) significantly below official retail pricing",
            "DEMO - No evidence of authorized retailers offering at claimed price",
            "DEMO - Content matches known patterns of promotional scams", 
            "DEMO - Media analysis shows promotional styling but no strong manipulation indicators",
            "DEMO - Limited contact information and verification sources available"
        ]
        
        return {
            "summary": summary.strip(),
            "recommended_action": recommended_action,
            "key_findings": key_findings,
            "disclaimer": "DEMO DATA - This analysis demonstrates the system's capabilities using simulated research data. In production, all sources and findings would be based on real web research.",
            "demo_data": True
        }
    
    def _get_fallback_report(self) -> dict:
        """Generate fallback report when service fails"""
        return {
            "summary": "Analysis completed with limited AI assistance due to service availability.",
            "recommended_action": "Manual review recommended due to system limitations.",
            "key_findings": ["Analysis service temporarily unavailable", "Manual verification recommended"],
            "disclaimer": "This report was generated with limited AI assistance. Full analysis capabilities were not available.",
            "error": "Report generation service unavailable"
        }


# Global report agent instance  
report_agent = ReportAgent()