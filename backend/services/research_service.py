"""
Research service for claim verification using web search
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
import httpx
from urllib.parse import quote_plus
import google.generativeai as genai

logger = logging.getLogger(__name__)


class ResearchService:
    """Web research service for claim verification"""
    
    def __init__(self):
        self.search_api_key = os.getenv("SEARCH_API_KEY")
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        self.model = None
        
        # Initialize Gemini for content analysis
        if not self.demo_mode and os.getenv("GEMINI_API_KEY"):
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        logger.info(f"Research service initialized (demo_mode: {self.demo_mode})")
    
    async def research_claim(self, claim: str, entities: List[str] = None) -> Dict[str, Any]:
        """
        Research a claim using web search and return evidence
        
        Args:
            claim: The main claim to research
            entities: List of entities mentioned in the claim
            
        Returns:
            Dictionary containing research results
        """
        if self.demo_mode:
            return self._get_demo_research_results(claim)
        
        if not claim or not claim.strip():
            return {
                "total_sources": 0,
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "neutral_evidence": [],
                "sources": [],
                "research_summary": "No claim provided for research",
                "limitations": "No claim to research"
            }
        
        try:
            # Generate search queries
            queries = await self._generate_search_queries(claim, entities or [])
            
            # Perform searches
            all_results = []
            for query in queries[:3]:  # Limit to 3 queries to avoid rate limits
                results = await self._web_search(query)
                all_results.extend(results)
            
            # Deduplicate by URL
            unique_results = {}
            for result in all_results:
                url = result.get("url", "")
                if url and url not in unique_results:
                    unique_results[url] = result
            
            search_results = list(unique_results.values())
            
            # Analyze results for evidence
            evidence = await self._analyze_evidence(claim, search_results)
            
            logger.info(f"Research completed: {len(search_results)} sources, "
                       f"{len(evidence['supporting_evidence'])} supporting, "
                       f"{len(evidence['contradicting_evidence'])} contradicting")
            
            return evidence
            
        except Exception as e:
            logger.error(f"Error in research: {e}")
            return self._get_fallback_research_results()
    
    async def _generate_search_queries(self, claim: str, entities: List[str]) -> List[str]:
        """Generate effective search queries for the claim"""
        
        if not self.model:
            # Fallback query generation
            queries = [claim]
            
            # Add entity-specific queries
            for entity in entities[:2]:  # Limit to 2 entities
                queries.append(f"{entity} official information")
                queries.append(f"{entity} price verification")
            
            return queries
        
        try:
            prompt = f"""
            Generate 3-4 effective web search queries to research this claim:
            "{claim}"
            
            Entities mentioned: {', '.join(entities) if entities else 'None'}
            
            Focus on:
            1. Official sources (company websites, government sites)
            2. Fact-checking organizations  
            3. News organizations
            4. Product/service verification
            5. Known scam or fraud reports
            
            Return queries as a JSON array:
            ["query 1", "query 2", "query 3"]
            
            Make queries specific and factual, not opiniated.
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            queries = json.loads(response_text)
            
            if isinstance(queries, list) and len(queries) > 0:
                return queries[:4]  # Limit to 4 queries
            else:
                return [claim]
                
        except Exception as e:
            logger.error(f"Error generating queries: {e}")
            return [claim, f"{claim} verification", f"{claim} official"]
    
    async def _web_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform web search using available search API"""
        
        if not self.search_api_key:
            logger.warning("No search API key available, using mock results")
            return self._get_mock_search_results(query)
        
        try:
            # Use a generic search API format (would need to be adapted for specific providers)
            # This is a placeholder for services like Serper, Bing, or custom search APIs
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Example using a hypothetical search API
                # In practice, you would use services like:
                # - Bing Search API
                # - Google Custom Search API  
                # - Serper API
                # - SerpAPI
                
                params = {
                    "q": query,
                    "num": 5,  # Limit results
                }
                
                # This is a placeholder - replace with actual search API
                response = await client.get(
                    "https://api.search-provider.com/search",
                    params=params,
                    headers={"Authorization": f"Bearer {self.search_api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_search_results(data)
                else:
                    logger.warning(f"Search API error: {response.status_code}")
                    return self._get_mock_search_results(query)
                    
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return self._get_mock_search_results(query)
    
    def _parse_search_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse search API results into standard format"""
        results = []
        
        # This would be adapted based on the actual search API response format
        for item in data.get("results", [])[:5]:  # Limit to 5 results
            result = {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("url", ""),
                "source": item.get("source", ""),
                "date": item.get("date", "")
            }
            results.append(result)
        
        return results
    
    def _get_mock_search_results(self, query: str) -> List[Dict[str, Any]]:
        """Generate mock search results when API is unavailable"""
        return [
            {
                "title": "Official Product Information - Apple",
                "snippet": "Official pricing and product details from manufacturer",
                "url": "https://apple.com/iphone",
                "source": "apple.com",
                "date": "2024-01-15"
            },
            {
                "title": "Price Comparison - TechReview",
                "snippet": "Comprehensive price analysis and market comparison",
                "url": "https://techreview.com/iphone-pricing",
                "source": "techreview.com", 
                "date": "2024-01-10"
            }
        ]
    
    async def _analyze_evidence(self, claim: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze search results to categorize evidence"""
        
        if not self.model:
            return self._get_simple_evidence_analysis(claim, search_results)
        
        try:
            # Prepare search results for analysis
            results_text = ""
            for i, result in enumerate(search_results[:10]):  # Limit to 10 results
                results_text += f"Result {i+1}:\n"
                results_text += f"Title: {result.get('title', '')}\n"
                results_text += f"Snippet: {result.get('snippet', '')}\n"
                results_text += f"Source: {result.get('source', '')}\n\n"
            
            prompt = f"""
            Analyze these search results to determine if they support, contradict, or are neutral regarding this claim:
            
            CLAIM: "{claim}"
            
            SEARCH RESULTS:
            {results_text}
            
            Categorize each relevant result and provide analysis:
            
            {{
                "total_sources": {len(search_results)},
                "supporting_evidence": [
                    {{
                        "title": "Result title",
                        "summary": "How this supports the claim",
                        "url": "result url",
                        "source": "source domain",
                        "reliability_score": 0.8
                    }}
                ],
                "contradicting_evidence": [
                    {{
                        "title": "Result title", 
                        "summary": "How this contradicts the claim",
                        "url": "result url",
                        "source": "source domain",
                        "reliability_score": 0.9
                    }}
                ],
                "neutral_evidence": [],
                "sources": [all search results],
                "research_summary": "Overall findings summary",
                "limitations": "Research limitations and caveats"
            }}
            
            Reliability scoring guidelines:
            - Official sources (gov, companies): 0.8-0.9
            - Established news/fact-checkers: 0.7-0.8  
            - Academic/research: 0.8-0.9
            - Forums/blogs: 0.3-0.5
            - Unknown sources: 0.2-0.4
            
            Be objective and conservative. Only include clear supporting/contradicting evidence.
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            evidence = json.loads(response_text)
            
            # Validate the response
            evidence = self._validate_evidence_analysis(evidence, search_results)
            
            return evidence
            
        except Exception as e:
            logger.error(f"Error analyzing evidence: {e}")
            return self._get_simple_evidence_analysis(claim, search_results)
    
    def _validate_evidence_analysis(self, evidence: Dict[str, Any], 
                                  search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate and clean evidence analysis"""
        
        validated = {
            "total_sources": evidence.get("total_sources", len(search_results)),
            "supporting_evidence": evidence.get("supporting_evidence", []),
            "contradicting_evidence": evidence.get("contradicting_evidence", []),
            "neutral_evidence": evidence.get("neutral_evidence", []),
            "sources": search_results,  # Use original search results
            "research_summary": evidence.get("research_summary", "Analysis completed"),
            "limitations": evidence.get("limitations", "Limited to available web sources")
        }
        
        # Ensure lists are actually lists
        for key in ["supporting_evidence", "contradicting_evidence", "neutral_evidence"]:
            if not isinstance(validated[key], list):
                validated[key] = []
        
        return validated
    
    def _get_simple_evidence_analysis(self, claim: str, 
                                    search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple evidence analysis when AI is unavailable"""
        
        # Simple keyword-based analysis
        claim_lower = claim.lower()
        supporting = []
        contradicting = []
        neutral = []
        
        for result in search_results:
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            content = f"{title} {snippet}"
            
            # Very basic classification
            if any(word in content for word in ["official", "confirmed", "available", "true"]):
                supporting.append({
                    "title": result.get("title", ""),
                    "summary": "Contains supportive language",
                    "url": result.get("url", ""),
                    "source": result.get("source", ""),
                    "reliability_score": 0.6
                })
            elif any(word in content for word in ["false", "scam", "fake", "not available", "debunked"]):
                contradicting.append({
                    "title": result.get("title", ""),
                    "summary": "Contains contradicting language", 
                    "url": result.get("url", ""),
                    "source": result.get("source", ""),
                    "reliability_score": 0.6
                })
            else:
                neutral.append({
                    "title": result.get("title", ""),
                    "summary": "Neutral or unclear relevance",
                    "url": result.get("url", ""),
                    "source": result.get("source", ""),
                    "reliability_score": 0.4
                })
        
        return {
            "total_sources": len(search_results),
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
            "neutral_evidence": neutral,
            "sources": search_results,
            "research_summary": "Basic keyword-based analysis completed",
            "limitations": "Simplified analysis due to service limitations"
        }
    
    def _get_demo_research_results(self, claim: str) -> Dict[str, Any]:
        """Return demo research results"""
        return {
            "total_sources": 5,
            "supporting_evidence": [
                {
                    "title": "DEMO - Official Apple iPhone Pricing",
                    "summary": "Official retail pricing shows significantly higher prices than claimed offer",
                    "url": "https://apple.com/iphone",
                    "source": "apple.com",
                    "reliability_score": 0.95,
                    "date_published": "2024-01-15"
                }
            ],
            "contradicting_evidence": [
                {
                    "title": "DEMO - Consumer Warning: iPhone Pricing Scams",
                    "summary": "Warning about fraudulent offers significantly below market price",
                    "url": "https://consumer-protection.gov/warnings", 
                    "source": "consumer-protection.gov",
                    "reliability_score": 0.9,
                    "date_published": "2024-01-12"
                },
                {
                    "title": "DEMO - Tech News: No Such Pricing Available",
                    "summary": "Report confirms no authorized retailers offering iPhone at claimed price",
                    "url": "https://technews.com/iphone-pricing",
                    "source": "technews.com", 
                    "reliability_score": 0.75,
                    "date_published": "2024-01-10"
                }
            ],
            "neutral_evidence": [],
            "sources": [
                {
                    "title": "DEMO - Official Apple iPhone Pricing",
                    "snippet": "Find official pricing for all iPhone models",
                    "url": "https://apple.com/iphone",
                    "source": "apple.com"
                },
                {
                    "title": "DEMO - Consumer Warning: iPhone Pricing Scams", 
                    "snippet": "Be aware of fraudulent pricing offers",
                    "url": "https://consumer-protection.gov/warnings",
                    "source": "consumer-protection.gov"
                }
            ],
            "research_summary": "DEMO - Research indicates the claimed pricing is significantly below official retail prices and matches patterns of known fraudulent offers.",
            "limitations": "DEMO DATA - Real research would include more comprehensive source verification and cross-referencing",
            "demo_data": True
        }
    
    def _get_fallback_research_results(self) -> Dict[str, Any]:
        """Return fallback research results when service fails"""
        return {
            "total_sources": 0,
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "neutral_evidence": [],
            "sources": [],
            "research_summary": "External research service temporarily unavailable",
            "limitations": "Unable to access web search services",
            "error": "Research service unavailable"
        }


# Global research service instance
research_service = ResearchService()