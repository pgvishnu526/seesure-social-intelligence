"""
Content understanding agent for SocialPulse
"""

import logging
from typing import Dict, Any
from models.schemas import ContentAnalysis, AnalysisState
from services.vision_service import vision_service

logger = logging.getLogger(__name__)


class ContentAgent:
    """Agent responsible for understanding and analyzing content"""
    
    async def process(self, state: AnalysisState) -> AnalysisState:
        """
        Process content understanding for the given analysis state
        
        Args:
            state: Current analysis state
            
        Returns:
            Updated analysis state with content analysis
        """
        logger.info(f"Content agent processing analysis {state.analysis_id}")
        
        try:
            if not state.image_path:
                raise ValueError("No image path available for content analysis")
            
            # Perform OCR and content analysis
            content_data = await vision_service.extract_text_and_analyze(state.image_path)
            
            # Create ContentAnalysis object
            content_analysis = ContentAnalysis(
                extracted_text=content_data.get("extracted_text", ""),
                content_type=content_data.get("content_type", "unknown"),
                category=content_data.get("category", "general"),
                entities=content_data.get("entities", []),
                topics=content_data.get("topics", []),
                language=content_data.get("language", "en"),
                image_url=state.image_path  # Will be updated with public URL later
            )
            
            # Update state
            state.content_analysis = content_analysis
            state.progress = 30  # Content understanding complete
            
            logger.info(f"Content analysis completed for {state.analysis_id}")
            logger.debug(f"Extracted text length: {len(content_analysis.extracted_text)} characters")
            logger.debug(f"Content type: {content_analysis.content_type}")
            logger.debug(f"Entities found: {len(content_analysis.entities)}")
            
            return state
            
        except Exception as e:
            logger.error(f"Content agent error for {state.analysis_id}: {e}")
            state.error_message = f"Content analysis failed: {str(e)}"
            return state


# Global content agent instance
content_agent = ContentAgent()