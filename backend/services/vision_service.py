"""
Vision and OCR service using Google Gemini
"""

import os
import base64
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import google.generativeai as genai
from PIL import Image
import io

logger = logging.getLogger(__name__)


class VisionService:
    """Vision service for OCR and image analysis using Gemini"""
    
    def __init__(self):
        self.client = None
        self.model = None
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        
        if not self.demo_mode:
            self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Gemini client"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY not found, vision features will use demo mode")
                self.demo_mode = True
                return
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini vision service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.demo_mode = True
    
    async def extract_text_and_analyze(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text and perform content analysis on an image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing extracted text and analysis
        """
        if self.demo_mode:
            return self._get_demo_content_analysis()
        
        try:
            # Load and validate image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Prepare the prompt for content analysis
            prompt = """
            Analyze this social media content image and provide a detailed analysis in JSON format.
            
            Extract and analyze:
            1. All visible text (OCR)
            2. Content type (post, story, comment, advertisement, etc.)
            3. Platform indicators (if visible - Instagram, Facebook, Twitter, etc.)
            4. Category (news, product, personal, promotional, etc.) 
            5. Main topics/subjects
            6. Named entities (people, places, brands, products)
            7. Language detected
            8. Visual elements description
            
            Return your analysis as a JSON object with these fields:
            {
                "extracted_text": "All visible text found in the image",
                "content_type": "Type of social media content",
                "platform": "Social media platform if identifiable", 
                "category": "Content category",
                "topics": ["list", "of", "main", "topics"],
                "entities": ["list", "of", "named", "entities"],
                "language": "detected language code",
                "visual_description": "Description of visual elements",
                "text_regions": [
                    {
                        "text": "text in this region",
                        "position": "description of position",
                        "style": "description of text style"
                    }
                ]
            }
            
            Be thorough but concise. If you cannot determine something, use appropriate default values or "unknown".
            """
            
            # Generate content with Gemini
            response = self.model.generate_content([prompt, image])
            
            # Parse JSON response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            import json
            analysis = json.loads(response_text)
            
            # Validate and clean up the response
            analysis = self._validate_content_analysis(analysis)
            
            logger.info(f"Content analysis completed for {image_path}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in content analysis: {e}")
            return self._get_fallback_content_analysis()
    
    async def analyze_media_authenticity(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze image for potential manipulation or AI generation indicators
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing authenticity analysis
        """
        if self.demo_mode:
            return self._get_demo_media_analysis()
        
        try:
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            prompt = """
            Analyze this image for potential authenticity issues and manipulation indicators.
            Look for signs that might suggest:
            1. Digital manipulation or editing
            2. AI generation artifacts
            3. Inconsistent lighting or shadows
            4. Unnatural text rendering
            5. Compression artifacts
            6. Color/quality inconsistencies
            
            IMPORTANT: Be conservative in your assessment. Only flag clear indicators.
            Do not make definitive claims about AI generation unless there are strong technical indicators.
            
            Return your analysis as JSON:
            {
                "authenticity_score": 0.8,  // 0.0 (definitely manipulated) to 1.0 (appears authentic)
                "indicators": [
                    {
                        "type": "text_rendering", 
                        "description": "Text appears naturally integrated",
                        "risk_level": "low",  // low, medium, high
                        "confidence": 0.7
                    }
                ],
                "explanation": "Overall assessment explanation",
                "method_used": "Visual analysis using AI",
                "limitations": "Cannot definitively prove authenticity without additional metadata analysis"
            }
            
            Be honest about limitations. Never claim 100% certainty.
            """
            
            response = self.model.generate_content([prompt, image])
            
            # Parse JSON response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            import json
            analysis = json.loads(response_text)
            
            # Validate the response
            analysis = self._validate_media_analysis(analysis)
            
            logger.info(f"Media authenticity analysis completed for {image_path}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in media analysis: {e}")
            return self._get_fallback_media_analysis()
    
    def _validate_content_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean content analysis response"""
        validated = {
            "extracted_text": analysis.get("extracted_text", ""),
            "content_type": analysis.get("content_type", "unknown"),
            "platform": analysis.get("platform", "unknown"),
            "category": analysis.get("category", "general"),
            "topics": analysis.get("topics", []),
            "entities": analysis.get("entities", []),
            "language": analysis.get("language", "en"),
            "visual_description": analysis.get("visual_description", ""),
            "text_regions": analysis.get("text_regions", [])
        }
        
        # Ensure lists are actually lists
        if not isinstance(validated["topics"], list):
            validated["topics"] = []
        if not isinstance(validated["entities"], list):
            validated["entities"] = []
        if not isinstance(validated["text_regions"], list):
            validated["text_regions"] = []
        
        return validated
    
    def _validate_media_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean media analysis response"""
        validated = {
            "authenticity_score": float(analysis.get("authenticity_score", 0.8)),
            "indicators": analysis.get("indicators", []),
            "explanation": analysis.get("explanation", "No specific concerns detected"),
            "method_used": analysis.get("method_used", "Visual AI analysis"),
            "limitations": analysis.get("limitations", "Analysis based on visual indicators only")
        }
        
        # Clamp authenticity score
        validated["authenticity_score"] = max(0.0, min(1.0, validated["authenticity_score"]))
        
        # Ensure indicators is a list
        if not isinstance(validated["indicators"], list):
            validated["indicators"] = []
        
        return validated
    
    def _get_demo_content_analysis(self) -> Dict[str, Any]:
        """Return demo content analysis"""
        return {
            "extracted_text": "iPhone 17 Pro available for ₹19,999. Limited time offer! Contact us now for exclusive deals. #iPhone #Apple #Deal",
            "content_type": "promotional_post",
            "platform": "instagram", 
            "category": "product_promotion",
            "topics": ["smartphone", "apple", "discount", "sale"],
            "entities": ["iPhone 17 Pro", "Apple", "₹19,999"],
            "language": "en",
            "visual_description": "Product image with promotional text overlay",
            "text_regions": [
                {
                    "text": "iPhone 17 Pro available for ₹19,999",
                    "position": "center_top",
                    "style": "bold_white_text"
                }
            ],
            "demo_data": True
        }
    
    def _get_demo_media_analysis(self) -> Dict[str, Any]:
        """Return demo media analysis"""
        return {
            "authenticity_score": 0.6,
            "indicators": [
                {
                    "type": "price_overlay",
                    "description": "Price text appears overlaid on product image",
                    "risk_level": "medium", 
                    "confidence": 0.8
                },
                {
                    "type": "promotional_styling",
                    "description": "Heavy promotional styling typical of advertisement",
                    "risk_level": "low",
                    "confidence": 0.9
                }
            ],
            "explanation": "Image shows typical promotional styling with overlaid text. No strong manipulation indicators detected, but promotional nature suggests commercial intent.",
            "method_used": "DEMO - Visual AI analysis simulation",
            "limitations": "DEMO DATA - Real analysis would include deeper technical assessment",
            "demo_data": True
        }
    
    def _get_fallback_content_analysis(self) -> Dict[str, Any]:
        """Return fallback content analysis when service fails"""
        return {
            "extracted_text": "OCR service temporarily unavailable",
            "content_type": "unknown",
            "platform": "unknown", 
            "category": "general",
            "topics": [],
            "entities": [],
            "language": "unknown",
            "visual_description": "Analysis unavailable",
            "text_regions": [],
            "error": "OCR service unavailable"
        }
    
    def _get_fallback_media_analysis(self) -> Dict[str, Any]:
        """Return fallback media analysis when service fails"""
        return {
            "authenticity_score": 0.5,
            "indicators": [],
            "explanation": "Media authenticity analysis temporarily unavailable",
            "method_used": "Fallback response",
            "limitations": "Analysis service unavailable",
            "error": "Media analysis service unavailable"
        }


# Global vision service instance
vision_service = VisionService()