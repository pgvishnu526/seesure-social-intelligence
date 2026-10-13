"""
Media analysis agent for SocialPulse
"""

import logging
from models.schemas import MediaAnalysis, MediaIndicator, AnalysisState
from services.vision_service import vision_service

logger = logging.getLogger(__name__)


class MediaAgent:
    """Agent responsible for media authenticity analysis"""
    
    async def process(self, state: AnalysisState) -> AnalysisState:
        """
        Process media analysis for the given analysis state
        
        Args:
            state: Current analysis state
            
        Returns:
            Updated analysis state with media analysis
        """
        logger.info(f"Media agent processing analysis {state.analysis_id}")
        
        try:
            if not state.image_path:
                raise ValueError("No image path available for media analysis")
            
            # Perform media authenticity analysis
            media_data = await vision_service.analyze_media_authenticity(state.image_path)
            
            # Convert indicators to MediaIndicator objects
            indicators = []
            for indicator_data in media_data.get("indicators", []):
                indicators.append(MediaIndicator(
                    type=indicator_data.get("type", "general"),
                    description=indicator_data.get("description", ""),
                    risk_level=indicator_data.get("risk_level", "low"),
                    confidence=indicator_data.get("confidence", 0.0)
                ))
            
            # Create MediaAnalysis object
            state.media_analysis = MediaAnalysis(
                authenticity_score=media_data.get("authenticity_score", 0.8),
                indicators=indicators,
                explanation=media_data.get("explanation", "No specific concerns detected"),
                method_used=media_data.get("method_used", "Visual AI analysis"),
                limitations=media_data.get("limitations", "Analysis based on visual indicators only")
            )
            
            # Media analysis happens in parallel with sentiment, so don't update progress here
            
            logger.info(f"Media analysis completed for {state.analysis_id}")
            logger.debug(f"Authenticity score: {state.media_analysis.authenticity_score:.2f}")
            logger.debug(f"Indicators found: {len(state.media_analysis.indicators)}")
            
            return state
            
        except Exception as e:
            logger.error(f"Media agent error for {state.analysis_id}: {e}")
            state.error_message = f"Media analysis failed: {str(e)}"
            return state


# Global media agent instance
media_agent = MediaAgent()