"""
Reports API endpoints for SocialPulse
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from services.storage_service import storage_service
from utils.validation import validate_analysis_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/report/{analysis_id}")
async def get_analysis_report(analysis_id: str) -> JSONResponse:
    """
    Get complete analysis report
    
    Args:
        analysis_id: Analysis identifier
        
    Returns:
        Complete analysis report
    """
    try:
        # Validate analysis ID format
        if not validate_analysis_id(analysis_id):
            raise HTTPException(status_code=400, detail="Invalid analysis ID format")
        
        # Load report from storage
        report_data = await storage_service.load_final_report(analysis_id)
        
        if not report_data:
            raise HTTPException(status_code=404, detail="Report not found")
        
        logger.info(f"Report retrieved for {analysis_id}")
        
        return JSONResponse(content=report_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report for {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.get("/report/{analysis_id}/summary")
async def get_report_summary(analysis_id: str) -> JSONResponse:
    """
    Get analysis report summary
    
    Args:
        analysis_id: Analysis identifier
        
    Returns:
        Report summary with key findings
    """
    try:
        # Validate analysis ID format
        if not validate_analysis_id(analysis_id):
            raise HTTPException(status_code=400, detail="Invalid analysis ID format")
        
        # Load full report
        report_data = await storage_service.load_final_report(analysis_id)
        
        if not report_data:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Extract summary information
        summary = {
            "analysis_id": analysis_id,
            "timestamp": report_data.get("timestamp"),
            "risk_score": None,
            "risk_level": None,
            "main_claim": None,
            "summary": None,
            "recommended_action": None
        }
        
        # Extract key information
        if "risk_assessment" in report_data and report_data["risk_assessment"]:
            summary["risk_score"] = report_data["risk_assessment"].get("score")
            summary["risk_level"] = report_data["risk_assessment"].get("level")
        
        if "claim" in report_data and report_data["claim"]:
            summary["main_claim"] = report_data["claim"].get("claim")
        
        if "report" in report_data and report_data["report"]:
            summary["summary"] = report_data["report"].get("summary")
            summary["recommended_action"] = report_data["report"].get("recommended_action")
        
        logger.info(f"Report summary retrieved for {analysis_id}")
        
        return JSONResponse(content=summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report summary for {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/report/{analysis_id}/export")
async def export_report(analysis_id: str, format: str = "json") -> JSONResponse:
    """
    Export analysis report in different formats
    
    Args:
        analysis_id: Analysis identifier
        format: Export format (json, pdf, txt)
        
    Returns:
        Exported report data
    """
    try:
        # Validate analysis ID format
        if not validate_analysis_id(analysis_id):
            raise HTTPException(status_code=400, detail="Invalid analysis ID format")
        
        # Load report from storage
        report_data = await storage_service.load_final_report(analysis_id)
        
        if not report_data:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if format.lower() == "json":
            # Return JSON format
            return JSONResponse(content=report_data)
            
        elif format.lower() == "txt":
            # Convert to text format
            text_report = _format_report_as_text(report_data)
            
            return JSONResponse(
                content={"format": "text", "content": text_report},
                media_type="text/plain"
            )
            
        elif format.lower() == "pdf":
            # PDF export would require additional libraries (reportlab, weasyprint, etc.)
            # For now, return a placeholder
            return JSONResponse(
                content={"error": "PDF export not yet implemented"},
                status_code=501
            )
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export report for {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export report: {str(e)}")


def _format_report_as_text(report_data: Dict[str, Any]) -> str:
    """Format report data as plain text"""
    
    lines = []
    lines.append("=" * 60)
    lines.append("SOCIALPULSE INTELLIGENCE REPORT")
    lines.append("=" * 60)
    lines.append("")
    
    # Basic information
    lines.append(f"Analysis ID: {report_data.get('analysis_id', 'N/A')}")
    lines.append(f"Timestamp: {report_data.get('timestamp', 'N/A')}")
    lines.append("")
    
    # Content analysis
    if report_data.get("content"):
        content = report_data["content"]
        lines.append("CONTENT ANALYSIS")
        lines.append("-" * 20)
        lines.append(f"Content Type: {content.get('content_type', 'N/A')}")
        lines.append(f"Category: {content.get('category', 'N/A')}")
        lines.append(f"Extracted Text: {content.get('extracted_text', 'N/A')}")
        lines.append("")
    
    # Claim analysis
    if report_data.get("claim"):
        claim = report_data["claim"]
        lines.append("CLAIM ANALYSIS")
        lines.append("-" * 20)
        lines.append(f"Main Claim: {claim.get('claim', 'N/A')}")
        lines.append(f"Claim Type: {claim.get('claim_type', 'N/A')}")
        if claim.get("entities"):
            lines.append(f"Entities: {', '.join(claim['entities'])}")
        lines.append("")
    
    # Sentiment analysis
    if report_data.get("sentiment"):
        sentiment = report_data["sentiment"]
        lines.append("SENTIMENT ANALYSIS")
        lines.append("-" * 20)
        lines.append(f"Sentiment: {sentiment.get('label', 'N/A').upper()}")
        lines.append(f"Confidence: {sentiment.get('confidence', 0):.2f}")
        lines.append("")
    
    # Risk assessment
    if report_data.get("risk_assessment"):
        risk = report_data["risk_assessment"]
        lines.append("RISK ASSESSMENT")
        lines.append("-" * 20)
        lines.append(f"Risk Score: {risk.get('score', 0)}/100")
        lines.append(f"Risk Level: {risk.get('level', 'UNKNOWN')}")
        
        if risk.get("reasons"):
            lines.append("Risk Factors:")
            for reason in risk["reasons"]:
                lines.append(f"• {reason}")
        lines.append("")
    
    # Research summary
    if report_data.get("research"):
        research = report_data["research"]
        lines.append("RESEARCH SUMMARY")
        lines.append("-" * 20)
        lines.append(f"Total Sources: {research.get('total_sources', 0)}")
        lines.append(f"Supporting Evidence: {len(research.get('supporting_evidence', []))}")
        lines.append(f"Contradicting Evidence: {len(research.get('contradicting_evidence', []))}")
        lines.append(f"Summary: {research.get('research_summary', 'N/A')}")
        lines.append("")
    
    # Final report
    if report_data.get("report"):
        final_report = report_data["report"]
        lines.append("AI SUMMARY & RECOMMENDATIONS")
        lines.append("-" * 30)
        lines.append(f"Summary: {final_report.get('summary', 'N/A')}")
        lines.append("")
        lines.append(f"Recommended Action: {final_report.get('recommended_action', 'N/A')}")
        lines.append("")
        
        if final_report.get("key_findings"):
            lines.append("Key Findings:")
            for finding in final_report["key_findings"]:
                lines.append(f"• {finding}")
            lines.append("")
    
    # Footer
    lines.append("=" * 60)
    lines.append("This report was generated by SocialPulse AI")
    lines.append("For questions or concerns, please contact your administrator")
    lines.append("=" * 60)
    
    return "\n".join(lines)