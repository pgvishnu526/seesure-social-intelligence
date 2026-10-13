"""
LangGraph state definitions for SocialPulse workflow
"""

from typing import TypedDict, Optional
from datetime import datetime
from models.schemas import (
    AnalysisStatus, ContentAnalysis, ClaimAnalysis, 
    SentimentAnalysis, MediaAnalysis, ResearchResults,
    RiskAssessment, IntelligenceReport
)


class SocialPulseState(TypedDict):
    """State for SocialPulse analysis workflow"""
    
    # Core identifiers
    analysis_id: str
    status: AnalysisStatus
    progress: int
    
    # Input data
    image_path: Optional[str]
    image_data: Optional[bytes]
    
    # Analysis results
    content_analysis: Optional[ContentAnalysis]
    claim_analysis: Optional[ClaimAnalysis]
    sentiment_analysis: Optional[SentimentAnalysis]
    media_analysis: Optional[MediaAnalysis]
    research_results: Optional[ResearchResults]
    risk_assessment: Optional[RiskAssessment]
    final_report: Optional[IntelligenceReport]
    
    # Metadata
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    error_message: Optional[str]
    demo_mode: bool