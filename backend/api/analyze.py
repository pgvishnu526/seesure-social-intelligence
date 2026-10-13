"""
Analysis API endpoints for SocialPulse
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from models.schemas import (
    AnalysisStartResponse, AnalysisStatusResponse, AnalysisStatus, AnalysisState
)
from utils.validation import validate_image_content, sanitize_filename
from services.storage_service import storage_service
from graph.workflow import socialpulse_workflow

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for analysis states (in production, use Redis or database)
analysis_states: Dict[str, AnalysisState] = {}

# Analysis counter for generating IDs
analysis_counter = 1


def generate_analysis_id() -> str:
    """Generate unique analysis ID"""
    global analysis_counter
    current_year = datetime.utcnow().year
    analysis_id = f"SP-{current_year}-{analysis_counter:06d}"
    analysis_counter += 1
    return analysis_id


async def run_analysis_workflow(analysis_id: str, image_data: bytes):
    """Run analysis workflow in background"""
    try:
        demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        
        # Create initial state
        state = AnalysisState(
            analysis_id=analysis_id,
            status=AnalysisStatus.RECEIVED,
            progress=0,
            image_data=image_data,
            demo_mode=demo_mode,
            start_time=datetime.utcnow()
        )
        
        # Store initial state
        analysis_states[analysis_id] = state
        
        # Run workflow
        final_state = await socialpulse_workflow.run_analysis(analysis_id, image_data, demo_mode)
        
        # Update stored state
        analysis_states[analysis_id] = final_state
        
        logger.info(f"Analysis workflow completed for {analysis_id}: {final_state.status}")
        
    except Exception as e:
        logger.error(f"Analysis workflow failed for {analysis_id}: {e}")
        
        # Update state with error
        if analysis_id in analysis_states:
            analysis_states[analysis_id].status = AnalysisStatus.FAILED
            analysis_states[analysis_id].error_message = str(e)


@router.post("/analyze", response_model=AnalysisStartResponse)
async def start_analysis(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...)
) -> AnalysisStartResponse:
    """
    Start analysis of uploaded social media image
    
    Args:
        image: Uploaded image file
        
    Returns:
        Analysis start response with analysis ID
    """
    try:
        # Validate file
        if not image.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Read image data
        image_data = await image.read()
        
        # Validate image content
        is_valid, error_message = validate_image_content(image_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Generate analysis ID
        analysis_id = generate_analysis_id()
        
        # Start analysis in background
        background_tasks.add_task(run_analysis_workflow, analysis_id, image_data)
        
        logger.info(f"Analysis started: {analysis_id}")
        
        return AnalysisStartResponse(
            analysis_id=analysis_id,
            status=AnalysisStatus.RECEIVED,
            message="Analysis started successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")


@router.get("/analyze/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str) -> AnalysisStatusResponse:
    """
    Get status of analysis
    
    Args:
        analysis_id: Analysis identifier
        
    Returns:
        Current analysis status
    """
    try:
        # Check if analysis exists
        if analysis_id not in analysis_states:
            # Try to load from storage
            stored_state = await storage_service.load_analysis_state(analysis_id)
            if stored_state:
                # Reconstruct state from stored data
                state = AnalysisState(
                    analysis_id=stored_state["analysis_id"],
                    status=AnalysisStatus(stored_state["status"]),
                    progress=stored_state.get("progress", 0),
                    error_message=stored_state.get("error_message")
                )
                analysis_states[analysis_id] = state
            else:
                raise HTTPException(status_code=404, detail="Analysis not found")
        
        state = analysis_states[analysis_id]
        
        # Prepare response
        response = AnalysisStatusResponse(
            analysis_id=analysis_id,
            status=state.status,
            progress=state.progress,
            error=state.error_message
        )
        
        # Add report URL if completed
        if state.status == AnalysisStatus.COMPLETED:
            response.report_url = f"/api/report/{analysis_id}"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis status for {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


# Optional: Endpoint to cancel analysis
@router.delete("/analyze/{analysis_id}")
async def cancel_analysis(analysis_id: str) -> JSONResponse:
    """
    Cancel ongoing analysis
    
    Args:
        analysis_id: Analysis identifier
        
    Returns:
        Cancellation confirmation
    """
    try:
        if analysis_id not in analysis_states:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        state = analysis_states[analysis_id]
        
        if state.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
            raise HTTPException(status_code=400, detail="Analysis already finished")
        
        # Mark as cancelled (we'll treat this as failed)
        state.status = AnalysisStatus.FAILED
        state.error_message = "Analysis cancelled by user"
        
        logger.info(f"Analysis cancelled: {analysis_id}")
        
        return JSONResponse(
            content={"message": "Analysis cancelled successfully"},
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel: {str(e)}")


# Optional: List recent analyses
@router.get("/analyses")
async def list_analyses(limit: int = 20) -> JSONResponse:
    """
    List recent analyses
    
    Args:
        limit: Maximum number of results
        
    Returns:
        List of recent analyses
    """
    try:
        # Get from storage service
        analyses = await storage_service.list_analyses(limit)
        
        return JSONResponse(content={"analyses": analyses})
        
    except Exception as e:
        logger.error(f"Failed to list analyses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list analyses: {str(e)}")