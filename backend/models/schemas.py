"""
Pydantic models for SocialPulse API
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AnalysisStatus(str, Enum):
    """Analysis status enumeration"""
    RECEIVED = "received"
    VALIDATING = "validating" 
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    RESEARCHING = "researching"
    VERIFYING = "verifying"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SentimentLabel(str, Enum):
    """Sentiment labels"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


# Analysis Request/Response Models
class AnalysisStartResponse(BaseModel):
    """Response when analysis is started"""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    status: AnalysisStatus = Field(default=AnalysisStatus.RECEIVED)
    message: str = Field(default="Analysis started successfully")


class AnalysisStatusResponse(BaseModel):
    """Analysis status response"""
    analysis_id: str
    status: AnalysisStatus
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    message: Optional[str] = None
    error: Optional[str] = None
    report_url: Optional[str] = None
    estimated_time_remaining: Optional[int] = None  # seconds


# Content Understanding Models
class ContentAnalysis(BaseModel):
    """Content analysis results"""
    extracted_text: str = Field(..., description="Text extracted from image")
    content_type: str = Field(..., description="Type of content (post, story, comment, etc.)")
    category: str = Field(..., description="Content category")
    entities: List[str] = Field(default_factory=list, description="Named entities found")
    topics: List[str] = Field(default_factory=list, description="Main topics")
    language: Optional[str] = Field(None, description="Detected language")
    image_url: Optional[str] = Field(None, description="URL of stored image")


# Claim Extraction Models
class ClaimAnalysis(BaseModel):
    """Extracted claim analysis"""
    claim: str = Field(..., description="Main factual claim")
    claim_type: str = Field(..., description="Type of claim")
    entities: List[str] = Field(default_factory=list, description="Entities in the claim")
    values: List[str] = Field(default_factory=list, description="Numerical/monetary values")
    requires_verification: bool = Field(True, description="Whether claim needs verification")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in extraction")


# Sentiment Analysis Models
class SentimentAnalysis(BaseModel):
    """Sentiment analysis results"""
    label: SentimentLabel = Field(..., description="Sentiment label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    explanation: Optional[str] = Field(None, description="Explanation of sentiment")


# Media Analysis Models
class MediaIndicator(BaseModel):
    """Media authenticity indicator"""
    type: str = Field(..., description="Type of indicator")
    description: str = Field(..., description="Description of the indicator")
    risk_level: str = Field(..., description="Risk level (low, medium, high)")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in detection")


class MediaAnalysis(BaseModel):
    """Media authenticity analysis"""
    authenticity_score: float = Field(0.0, ge=0.0, le=1.0, description="Authenticity score")
    indicators: List[MediaIndicator] = Field(default_factory=list)
    explanation: str = Field("", description="Overall explanation")
    method_used: str = Field("", description="Analysis method used")
    limitations: str = Field("", description="Limitations of the analysis")


# Research Models
class EvidenceItem(BaseModel):
    """Evidence item from research"""
    title: str = Field(..., description="Evidence title")
    summary: str = Field(..., description="Evidence summary")
    url: Optional[str] = Field(None, description="Source URL")
    source: str = Field(..., description="Source name")
    reliability_score: float = Field(0.0, ge=0.0, le=1.0, description="Source reliability")
    date_published: Optional[str] = Field(None, description="Publication date")


class ResearchResults(BaseModel):
    """Research results"""
    total_sources: int = Field(0, description="Total sources checked")
    supporting_evidence: List[EvidenceItem] = Field(default_factory=list)
    contradicting_evidence: List[EvidenceItem] = Field(default_factory=list)
    neutral_evidence: List[EvidenceItem] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="All sources")
    research_summary: str = Field("", description="Summary of research findings")
    limitations: str = Field("", description="Research limitations")


# Risk Assessment Models
class RiskAssessment(BaseModel):
    """Risk assessment results"""
    score: int = Field(..., ge=0, le=100, description="Risk score 0-100")
    level: RiskLevel = Field(..., description="Risk level category")
    reasons: List[str] = Field(default_factory=list, description="Risk factors")
    methodology: str = Field("", description="Assessment methodology")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in assessment")


# Report Models
class IntelligenceReport(BaseModel):
    """Final intelligence report"""
    summary: str = Field(..., description="AI-generated summary")
    recommended_action: str = Field(..., description="Recommended action")
    key_findings: List[str] = Field(default_factory=list, description="Key findings")
    disclaimer: str = Field("", description="Report disclaimer")


# Complete Analysis Report
class AnalysisReport(BaseModel):
    """Complete analysis report"""
    analysis_id: str = Field(..., description="Analysis identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    content: Optional[ContentAnalysis] = None
    claim: Optional[ClaimAnalysis] = None
    sentiment: Optional[SentimentAnalysis] = None
    media_analysis: Optional[MediaAnalysis] = None
    research: Optional[ResearchResults] = None
    risk_assessment: Optional[RiskAssessment] = None
    report: Optional[IntelligenceReport] = None
    processing_time: Optional[float] = Field(None, description="Total processing time in seconds")
    demo_mode: bool = Field(False, description="Whether this was generated in demo mode")


# LangGraph State Model
class AnalysisState(BaseModel):
    """LangGraph workflow state"""
    analysis_id: str
    status: AnalysisStatus = AnalysisStatus.RECEIVED
    progress: int = 0
    
    # Input data
    image_path: Optional[str] = None
    image_data: Optional[bytes] = None
    
    # Analysis results
    content_analysis: Optional[ContentAnalysis] = None
    claim_analysis: Optional[ClaimAnalysis] = None
    sentiment_analysis: Optional[SentimentAnalysis] = None
    media_analysis: Optional[MediaAnalysis] = None
    research_results: Optional[ResearchResults] = None
    risk_assessment: Optional[RiskAssessment] = None
    final_report: Optional[IntelligenceReport] = None
    
    # Metadata
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    demo_mode: bool = False
    
    class Config:
        arbitrary_types_allowed = True


# Error Models
class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")
    analysis_id: Optional[str] = Field(None, description="Analysis ID if applicable")


# Demo Models
class DemoData(BaseModel):
    """Demo data structure"""
    content: ContentAnalysis
    claim: ClaimAnalysis 
    sentiment: SentimentAnalysis
    media_analysis: MediaAnalysis
    research: ResearchResults
    risk_assessment: RiskAssessment
    report: IntelligenceReport