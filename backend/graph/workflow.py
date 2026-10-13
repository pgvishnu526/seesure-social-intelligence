"""
LangGraph workflow for SocialPulse analysis
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from models.schemas import AnalysisState, AnalysisStatus
from agents.content_agent import content_agent
from agents.claim_agent import claim_agent
from agents.research_agent import research_agent
from agents.media_agent import media_agent
from agents.risk_agent import risk_agent
from agents.report_agent import report_agent
from services.sentiment_service import sentiment_service
from services.storage_service import storage_service

logger = logging.getLogger(__name__)


class SocialPulseWorkflow:
    """LangGraph workflow for SocialPulse analysis"""
    
    def __init__(self):
        self.workflow = None
        self.app = None
        self._build_workflow()
    
    def _build_workflow(self):
        """Build the LangGraph workflow"""
        
        # Create workflow graph
        workflow = StateGraph(AnalysisState)
        
        # Add workflow nodes
        workflow.add_node("validate_input", self.validate_input)
        workflow.add_node("store_image", self.store_image)
        workflow.add_node("content_understanding", self.content_understanding)
        workflow.add_node("claim_extraction", self.claim_extraction)
        workflow.add_node("parallel_analysis", self.parallel_analysis)
        workflow.add_node("research_claims", self.research_claims)
        workflow.add_node("risk_assessment", self.risk_assessment)
        workflow.add_node("generate_report", self.generate_report)
        workflow.add_node("finalize", self.finalize)
        
        # Define workflow edges
        workflow.add_edge(START, "validate_input")
        workflow.add_edge("validate_input", "store_image")
        workflow.add_edge("store_image", "content_understanding")
        workflow.add_edge("content_understanding", "claim_extraction")
        workflow.add_edge("claim_extraction", "parallel_analysis")
        workflow.add_edge("parallel_analysis", "research_claims")
        workflow.add_edge("research_claims", "risk_assessment")
        workflow.add_edge("risk_assessment", "generate_report")
        workflow.add_edge("generate_report", "finalize")
        workflow.add_edge("finalize", END)
        
        # Compile workflow
        memory = MemorySaver()
        self.app = workflow.compile(checkpointer=memory)
        
        logger.info("SocialPulse workflow compiled successfully")
    
    async def validate_input(self, state: AnalysisState) -> AnalysisState:
        """Validate input and initialize analysis"""
        logger.info(f"Validating input for analysis {state.analysis_id}")
        
        state.status = AnalysisStatus.VALIDATING
        state.progress = 5
        
        # Basic validation
        if not state.image_data and not state.image_path:
            state.error_message = "No image data provided"
            state.status = AnalysisStatus.FAILED
            return state
        
        # Initialize timestamps
        if not state.start_time:
            state.start_time = datetime.utcnow()
        
        logger.info(f"Input validation completed for {state.analysis_id}")
        return state
    
    async def store_image(self, state: AnalysisState) -> AnalysisState:
        """Store image and update state"""
        logger.info(f"Storing image for analysis {state.analysis_id}")
        
        state.status = AnalysisStatus.UPLOADED
        state.progress = 10
        
        try:
            if state.image_data and not state.image_path:
                # Store image data
                image_url = await storage_service.store_image(
                    state.analysis_id, 
                    state.image_data, 
                    "input.png"
                )
                state.image_path = image_url
            
            logger.info(f"Image stored for {state.analysis_id}: {state.image_path}")
            
        except Exception as e:
            logger.error(f"Failed to store image for {state.analysis_id}: {e}")
            state.error_message = f"Image storage failed: {str(e)}"
            state.status = AnalysisStatus.FAILED
        
        return state
    
    async def content_understanding(self, state: AnalysisState) -> AnalysisState:
        """Perform content understanding"""
        logger.info(f"Content understanding for analysis {state.analysis_id}")
        
        state.status = AnalysisStatus.EXTRACTING
        state.progress = 20
        
        try:
            # Process with content agent
            state = await content_agent.process(state)
            
            if state.error_message:
                state.status = AnalysisStatus.FAILED
                return state
            
        except Exception as e:
            logger.error(f"Content understanding failed for {state.analysis_id}: {e}")
            state.error_message = f"Content understanding failed: {str(e)}"
            state.status = AnalysisStatus.FAILED
        
        return state
    
    async def claim_extraction(self, state: AnalysisState) -> AnalysisState:
        """Extract and analyze claims"""
        logger.info(f"Claim extraction for analysis {state.analysis_id}")
        
        state.status = AnalysisStatus.ANALYZING
        state.progress = 35
        
        try:
            # Process with claim agent
            state = await claim_agent.process(state)
            
            if state.error_message:
                state.status = AnalysisStatus.FAILED
                return state
                
        except Exception as e:
            logger.error(f"Claim extraction failed for {state.analysis_id}: {e}")
            state.error_message = f"Claim extraction failed: {str(e)}"
            state.status = AnalysisStatus.FAILED
        
        return state
    
    async def parallel_analysis(self, state: AnalysisState) -> AnalysisState:
        """Perform parallel sentiment and media analysis"""
        logger.info(f"Parallel analysis for analysis {state.analysis_id}")
        
        state.progress = 50
        
        try:
            # Run sentiment and media analysis in parallel
            tasks = []
            
            # Sentiment analysis task
            if state.content_analysis and state.content_analysis.extracted_text:
                async def sentiment_task():
                    sentiment_data = await sentiment_service.analyze_sentiment(
                        state.content_analysis.extracted_text
                    )
                    from models.schemas import SentimentAnalysis, SentimentLabel
                    state.sentiment_analysis = SentimentAnalysis(
                        label=SentimentLabel(sentiment_data["label"]),
                        confidence=sentiment_data["confidence"],
                        explanation=sentiment_data.get("explanation", "")
                    )
                
                tasks.append(sentiment_task())
            
            # Media analysis task  
            if state.image_path:
                async def media_task():
                    return await media_agent.process(state)
                
                tasks.append(media_task())
            
            # Execute tasks in parallel
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Handle any exceptions
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Parallel analysis task {i} failed: {result}")
                    elif isinstance(result, AnalysisState):
                        # Update state from media analysis
                        state = result
            
        except Exception as e:
            logger.error(f"Parallel analysis failed for {state.analysis_id}: {e}")
            # Don't fail the entire analysis for parallel analysis issues
            logger.warning("Continuing analysis despite parallel analysis issues")
        
        return state
    
    async def research_claims(self, state: AnalysisState) -> AnalysisState:
        """Research extracted claims"""
        logger.info(f"Research phase for analysis {state.analysis_id}")
        
        state.status = AnalysisStatus.RESEARCHING
        state.progress = 65
        
        try:
            # Process with research agent
            state = await research_agent.process(state)
            
            if state.error_message:
                state.status = AnalysisStatus.FAILED
                return state
                
        except Exception as e:
            logger.error(f"Research failed for {state.analysis_id}: {e}")
            state.error_message = f"Research failed: {str(e)}"
            state.status = AnalysisStatus.FAILED
        
        return state
    
    async def risk_assessment(self, state: AnalysisState) -> AnalysisState:
        """Perform risk assessment"""
        logger.info(f"Risk assessment for analysis {state.analysis_id}")
        
        state.status = AnalysisStatus.VERIFYING
        state.progress = 80
        
        try:
            # Process with risk agent
            state = await risk_agent.process(state)
            
            if state.error_message:
                state.status = AnalysisStatus.FAILED
                return state
                
        except Exception as e:
            logger.error(f"Risk assessment failed for {state.analysis_id}: {e}")
            state.error_message = f"Risk assessment failed: {str(e)}"
            state.status = AnalysisStatus.FAILED
        
        return state
    
    async def generate_report(self, state: AnalysisState) -> AnalysisState:
        """Generate final intelligence report"""
        logger.info(f"Report generation for analysis {state.analysis_id}")
        
        state.status = AnalysisStatus.GENERATING_REPORT
        state.progress = 90
        
        try:
            # Process with report agent
            state = await report_agent.process(state)
            
            if state.error_message:
                state.status = AnalysisStatus.FAILED
                return state
                
        except Exception as e:
            logger.error(f"Report generation failed for {state.analysis_id}: {e}")
            state.error_message = f"Report generation failed: {str(e)}"
            state.status = AnalysisStatus.FAILED
        
        return state
    
    async def finalize(self, state: AnalysisState) -> AnalysisState:
        """Finalize analysis and save results"""
        logger.info(f"Finalizing analysis {state.analysis_id}")
        
        try:
            # Set completion status
            state.status = AnalysisStatus.COMPLETED
            state.progress = 100
            state.end_time = datetime.utcnow()
            
            # Save final state to storage
            state_dict = self._state_to_dict(state)
            await storage_service.store_analysis_state(state.analysis_id, state_dict)
            
            # Save final report
            if state.final_report:
                report_dict = self._create_full_report(state)
                await storage_service.store_final_report(state.analysis_id, report_dict)
            
            processing_time = (state.end_time - state.start_time).total_seconds() if state.start_time else 0
            logger.info(f"Analysis {state.analysis_id} completed in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Finalization failed for {state.analysis_id}: {e}")
            state.error_message = f"Finalization failed: {str(e)}"
            state.status = AnalysisStatus.FAILED
        
        return state
    
    def _state_to_dict(self, state: AnalysisState) -> Dict[str, Any]:
        """Convert state to dictionary for storage"""
        return {
            "analysis_id": state.analysis_id,
            "status": state.status,
            "progress": state.progress,
            "image_path": state.image_path,
            "content_analysis": state.content_analysis.model_dump() if state.content_analysis else None,
            "claim_analysis": state.claim_analysis.model_dump() if state.claim_analysis else None,
            "sentiment_analysis": state.sentiment_analysis.model_dump() if state.sentiment_analysis else None,
            "media_analysis": state.media_analysis.model_dump() if state.media_analysis else None,
            "research_results": state.research_results.model_dump() if state.research_results else None,
            "risk_assessment": state.risk_assessment.model_dump() if state.risk_assessment else None,
            "final_report": state.final_report.model_dump() if state.final_report else None,
            "start_time": state.start_time.isoformat() if state.start_time else None,
            "end_time": state.end_time.isoformat() if state.end_time else None,
            "error_message": state.error_message,
            "demo_mode": state.demo_mode
        }
    
    def _create_full_report(self, state: AnalysisState) -> Dict[str, Any]:
        """Create complete report for API response"""
        
        # Get image URL for frontend
        image_url = None
        if state.image_path and not state.image_path.startswith('http'):
            # Convert local path to accessible URL
            # In production, this would be a proper URL
            image_url = f"/api/image/{state.analysis_id}"
        else:
            image_url = state.image_path
        
        return {
            "analysis_id": state.analysis_id,
            "timestamp": state.end_time.isoformat() if state.end_time else datetime.utcnow().isoformat(),
            "content": {
                **state.content_analysis.model_dump() if state.content_analysis else {},
                "image_url": image_url
            },
            "claim": state.claim_analysis.model_dump() if state.claim_analysis else None,
            "sentiment": state.sentiment_analysis.model_dump() if state.sentiment_analysis else None,
            "media_analysis": state.media_analysis.model_dump() if state.media_analysis else None,
            "research": state.research_results.model_dump() if state.research_results else None,
            "risk_assessment": state.risk_assessment.model_dump() if state.risk_assessment else None,
            "report": state.final_report.model_dump() if state.final_report else None,
            "processing_time": (state.end_time - state.start_time).total_seconds() if state.start_time and state.end_time else 0,
            "demo_mode": state.demo_mode
        }
    
    async def run_analysis(self, analysis_id: str, image_data: bytes, demo_mode: bool = False) -> AnalysisState:
        """Run complete analysis workflow"""
        
        # Create initial state
        initial_state = AnalysisState(
            analysis_id=analysis_id,
            status=AnalysisStatus.RECEIVED,
            progress=0,
            image_data=image_data,
            demo_mode=demo_mode,
            start_time=datetime.utcnow()
        )
        
        # Run workflow
        config = {"configurable": {"thread_id": analysis_id}}
        
        try:
            final_state = await self.app.ainvoke(initial_state, config)
            return final_state
        except Exception as e:
            logger.error(f"Workflow execution failed for {analysis_id}: {e}")
            initial_state.error_message = f"Workflow execution failed: {str(e)}"
            initial_state.status = AnalysisStatus.FAILED
            return initial_state


# Global workflow instance
socialpulse_workflow = SocialPulseWorkflow()