"""
Research agent for SocialPulse
"""

import logging
from models.schemas import ResearchResults, AnalysisState, EvidenceItem
from services.research_service import research_service

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Agent responsible for researching claims"""
    
    async def process(self, state: AnalysisState) -> AnalysisState:
        """
        Process research for the given analysis state
        
        Args:
            state: Current analysis state
            
        Returns:
            Updated analysis state with research results
        """
        logger.info(f"Research agent processing analysis {state.analysis_id}")
        
        try:
            if not state.claim_analysis:
                logger.warning(f"No claim analysis available for research {state.analysis_id}")
                state.research_results = ResearchResults()
                return state
            
            claim = state.claim_analysis.claim
            entities = state.claim_analysis.entities
            
            # Only research if claim requires verification
            if not state.claim_analysis.requires_verification:
                logger.info(f"Claim does not require verification for {state.analysis_id}")
                state.research_results = ResearchResults(
                    research_summary="Claim does not require external verification",
                    limitations="No research needed for this type of content"
                )
                return state
            
            # Perform research
            research_data = await research_service.research_claim(claim, entities)
            
            # Convert to ResearchResults object
            supporting_evidence = []
            for item in research_data.get("supporting_evidence", []):
                supporting_evidence.append(EvidenceItem(
                    title=item.get("title", ""),
                    summary=item.get("summary", ""),
                    url=item.get("url", ""),
                    source=item.get("source", ""),
                    reliability_score=item.get("reliability_score", 0.0),
                    date_published=item.get("date_published")
                ))
            
            contradicting_evidence = []
            for item in research_data.get("contradicting_evidence", []):
                contradicting_evidence.append(EvidenceItem(
                    title=item.get("title", ""),
                    summary=item.get("summary", ""),
                    url=item.get("url", ""),
                    source=item.get("source", ""),
                    reliability_score=item.get("reliability_score", 0.0),
                    date_published=item.get("date_published")
                ))
            
            neutral_evidence = []
            for item in research_data.get("neutral_evidence", []):
                neutral_evidence.append(EvidenceItem(
                    title=item.get("title", ""),
                    summary=item.get("summary", ""),
                    url=item.get("url", ""),
                    source=item.get("source", ""),
                    reliability_score=item.get("reliability_score", 0.0),
                    date_published=item.get("date_published")
                ))
            
            state.research_results = ResearchResults(
                total_sources=research_data.get("total_sources", 0),
                supporting_evidence=supporting_evidence,
                contradicting_evidence=contradicting_evidence,
                neutral_evidence=neutral_evidence,
                sources=research_data.get("sources", []),
                research_summary=research_data.get("research_summary", ""),
                limitations=research_data.get("limitations", "")
            )
            
            state.progress = 70  # Research complete
            
            logger.info(f"Research completed for {state.analysis_id}")
            logger.debug(f"Found {len(supporting_evidence)} supporting and {len(contradicting_evidence)} contradicting evidence items")
            
            return state
            
        except Exception as e:
            logger.error(f"Research agent error for {state.analysis_id}: {e}")
            state.error_message = f"Research failed: {str(e)}"
            return state


# Global research agent instance
research_agent = ResearchAgent()