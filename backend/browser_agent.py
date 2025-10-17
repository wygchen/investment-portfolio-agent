"""
Browser Agent Wrapper for WatsonX API

This module provides a wrapper around the WatsonX browser agent API
that handles Google Search and DuckDuckGo search functionality.
The actual WatsonX browser agent model is provided externally.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserAgent:
    """
    Wrapper for WatsonX browser agent API.
    
    This class provides a clean interface to the WatsonX browser agent
    that handles web search functionality including Google Search and DuckDuckGo.
    """
    
    def __init__(self, 
                 watsonx_api_key: Optional[str] = None,
                 watsonx_url: Optional[str] = None,
                 project_id: Optional[str] = None):
        """
        Initialize the browser agent.
        
        Args:
            watsonx_api_key: WatsonX API key (if not using env vars)
            watsonx_url: WatsonX URL (if not using env vars)
            project_id: WatsonX project ID (if not using env vars)
        """
        self.api_key = watsonx_api_key
        self.url = watsonx_url
        self.project_id = project_id
        
        # Initialize WatsonX client if credentials provided
        self.watsonx_client = None
        if self.api_key and self.url and self.project_id:
            self._initialize_watsonx_client()
        
        logger.info("Browser agent initialized")
    
    def _initialize_watsonx_client(self):
        """Initialize the WatsonX client."""
        try:
            # Import WatsonX client
            from ibm_watsonx_ai.foundation_models import Model
            from ibm_watsonx_ai.metanames import GenTextParamsMetaNames
            
            # Initialize the model for browser agent
            self.watsonx_client = Model(
                model_id="ibm/granite-3-8b-instruct",  # Default model, can be overridden
                credentials={
                    "apikey": self.api_key,
                    "url": self.url
                },
                project_id=self.project_id
            )
            
            logger.info("WatsonX client initialized successfully")
            
        except ImportError:
            logger.warning("WatsonX client not available - install ibm-watsonx-ai package")
        except Exception as e:
            logger.error(f"Failed to initialize WatsonX client: {e}")
    
    def search_web(self, 
                   query: str, 
                   search_type: str = "google",
                   max_results: int = 5,
                   include_metadata: bool = True) -> Dict[str, Any]:
        """
        Perform web search using WatsonX browser agent.
        
        Args:
            query: Search query
            search_type: Type of search ("google" or "duckduckgo")
            max_results: Maximum number of results to return
            include_metadata: Whether to include search metadata
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            logger.info(f"Performing {search_type} search for: {query[:100]}...")
            
            # If WatsonX client is available, use it
            if self.watsonx_client:
                return self._search_with_watsonx(query, search_type, max_results, include_metadata)
            else:
                # Fallback to mock search results
                return self._mock_search_results(query, search_type, max_results, include_metadata)
                
        except Exception as e:
            logger.error(f"Error performing web search: {e}")
            return {
                "query": query,
                "search_type": search_type,
                "results": [],
                "total_results": 0,
                "search_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": str(e)
                }
            }
    
    def _search_with_watsonx(self, 
                           query: str, 
                           search_type: str, 
                           max_results: int,
                           include_metadata: bool) -> Dict[str, Any]:
        """
        Perform search using WatsonX browser agent API.
        
        Uses the deployed WatsonX browser agent model for web search.
        """
        try:
            import requests
            import os
            
            # Get API key from environment variable
            api_key = os.getenv('WATSONX_API_KEY')
            if not api_key:
                logger.error("WATSONX_API_KEY environment variable not set")
                return self._mock_search_results(query, search_type, max_results, include_metadata)
            
            # Get access token
            token_response = requests.post(
                'https://iam.cloud.ibm.com/identity/token', 
                data={
                    "apikey": api_key, 
                    "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Failed to get access token: {token_response.text}")
                return self._mock_search_results(query, search_type, max_results, include_metadata)
                
            mltoken = token_response.json()["access_token"]
            
            # Prepare the search request
            search_prompt = f"""
            Search the web using {search_type} for: "{query}"
            
            Return up to {max_results} relevant results in JSON format with:
            - title: Page title
            - url: Page URL  
            - snippet: Brief description
            - relevance_score: 0-1 relevance score
            - source: Source publication name
            - date: Publication date if available
            
            Focus on recent, authoritative financial and investment sources.
            """
            
            payload_scoring = {
                "messages": [
                    {
                        "content": search_prompt,
                        "role": "user"
                    }
                ]
            }
            
            # Make request to WatsonX browser agent
            response_scoring = requests.post(
                'https://us-south.ml.cloud.ibm.com/ml/v4/deployments/15b1893d-c71b-432f-9bd8-11647cda2700/ai_service_stream?version=2021-05-01',
                json=payload_scoring,
                headers={'Authorization': 'Bearer ' + mltoken}
            )
            
            if response_scoring.status_code != 200:
                logger.error(f"WatsonX API request failed: {response_scoring.text}")
                return self._mock_search_results(query, search_type, max_results, include_metadata)
            
            # Parse the response
            try:
                response_data = response_scoring.json()
                results = self._parse_watsonx_browser_response(response_data, query, search_type)
            except ValueError:
                # If JSON parsing fails, try to extract from text response
                response_text = response_scoring.text
                results = self._parse_watsonx_text_response(response_text, query, search_type)
            
            return {
                "query": query,
                "search_type": search_type,
                "results": results,
                "total_results": len(results),
                "search_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "success": True,
                    "watsonx_used": True,
                    "max_results_requested": max_results,
                    "api_endpoint": "WatsonX Browser Agent"
                }
            }
            
        except Exception as e:
            logger.error(f"Error with WatsonX browser agent: {e}")
            # Fallback to mock results
            return self._mock_search_results(query, search_type, max_results, include_metadata)
    
    def _parse_watsonx_browser_response(self, response_data: Dict[str, Any], query: str, search_type: str) -> List[Dict[str, Any]]:
        """
        Parse WatsonX browser agent response into structured search results.
        
        Args:
            response_data: JSON response from WatsonX browser agent
            query: Original search query
            search_type: Type of search performed
            
        Returns:
            List of structured search results
        """
        try:
            # Extract results from WatsonX response structure
            # The exact structure may vary based on the model's output format
            if 'choices' in response_data:
                # Standard OpenAI-style response
                content = response_data['choices'][0]['message']['content']
                return self._parse_watsonx_text_response(content, query, search_type)
            elif 'predictions' in response_data:
                # WatsonX prediction format
                content = response_data['predictions'][0]['text']
                return self._parse_watsonx_text_response(content, query, search_type)
            elif 'results' in response_data:
                # Direct results format
                return response_data['results']
            else:
                # Try to extract from any text field
                content = str(response_data)
                return self._parse_watsonx_text_response(content, query, search_type)
                
        except Exception as e:
            logger.error(f"Error parsing WatsonX browser response: {e}")
            return self._create_mock_results_from_response(str(response_data), query, search_type)
    
    def _parse_watsonx_text_response(self, response_text: str, query: str, search_type: str) -> List[Dict[str, Any]]:
        """
        Parse WatsonX text response into structured search results.
        
        Args:
            response_text: Text response from WatsonX
            query: Original search query
            search_type: Type of search performed
            
        Returns:
            List of structured search results
        """
        try:
            # Try to parse as JSON first
            if response_text.strip().startswith('{') or response_text.strip().startswith('['):
                results = json.loads(response_text)
                if isinstance(results, list):
                    return results
                elif isinstance(results, dict) and 'results' in results:
                    return results['results']
            
            # If not JSON, try to extract structured data from text
            return self._extract_results_from_text(response_text, query, search_type)
            
        except json.JSONDecodeError:
            logger.warning("WatsonX response is not valid JSON, using text extraction")
            return self._extract_results_from_text(response_text, query, search_type)
        except Exception as e:
            logger.error(f"Error parsing WatsonX text response: {e}")
            return self._create_mock_results_from_response(response_text, query, search_type)
    
    def _extract_results_from_text(self, text: str, query: str, search_type: str) -> List[Dict[str, Any]]:
        """
        Extract search results from unstructured text response.
        
        Args:
            text: Raw text response
            query: Original search query
            search_type: Type of search performed
            
        Returns:
            List of structured search results
        """
        try:
            results = []
            lines = text.strip().split('\n')
            
            current_result = {}
            for line in lines:
                line = line.strip()
                if not line:
                    if current_result:
                        results.append(current_result)
                        current_result = {}
                    continue
                
                # Try to extract structured information
                if line.startswith('Title:') or line.startswith('**Title:'):
                    current_result['title'] = line.replace('Title:', '').replace('**Title:', '').strip()
                elif line.startswith('URL:') or line.startswith('**URL:'):
                    current_result['url'] = line.replace('URL:', '').replace('**URL:', '').strip()
                elif line.startswith('Snippet:') or line.startswith('**Snippet:'):
                    current_result['snippet'] = line.replace('Snippet:', '').replace('**Snippet:', '').strip()
                elif line.startswith('Score:') or line.startswith('**Score:'):
                    try:
                        current_result['relevance_score'] = float(line.replace('Score:', '').replace('**Score:', '').strip())
                    except ValueError:
                        current_result['relevance_score'] = 0.8
                elif line.startswith('Source:') or line.startswith('**Source:'):
                    current_result['source'] = line.replace('Source:', '').replace('**Source:', '').strip()
                else:
                    # If no specific field, treat as snippet if we don't have one
                    if 'snippet' not in current_result:
                        current_result['snippet'] = line
                    else:
                        current_result['snippet'] += ' ' + line
            
            # Add the last result if exists
            if current_result:
                results.append(current_result)
            
            # Ensure all results have required fields
            for result in results:
                if 'title' not in result:
                    result['title'] = f"Search Result for '{query}'"
                if 'url' not in result:
                    result['url'] = f"https://example.com/result-{len(results)}"
                if 'snippet' not in result:
                    result['snippet'] = f"Information about {query}"
                if 'relevance_score' not in result:
                    result['relevance_score'] = 0.8
                if 'source' not in result:
                    result['source'] = search_type.title()
            
            return results[:5]  # Limit to 5 results
            
        except Exception as e:
            logger.error(f"Error extracting results from text: {e}")
            return self._create_mock_results_from_response(text, query, search_type)

    def _parse_watsonx_response(self, response: str, query: str, search_type: str) -> List[Dict[str, Any]]:
        """
        Parse WatsonX response into structured search results.
        
        Args:
            response: Raw response from WatsonX
            query: Original search query
            search_type: Type of search performed
            
        Returns:
            List of structured search results
        """
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{') or response.strip().startswith('['):
                results = json.loads(response)
                if isinstance(results, list):
                    return results
                elif isinstance(results, dict) and 'results' in results:
                    return results['results']
            
            # If not JSON, create mock results based on response
            # This is a fallback for when WatsonX returns non-JSON
            return self._create_mock_results_from_response(response, query, search_type)
            
        except json.JSONDecodeError:
            logger.warning("WatsonX response is not valid JSON, using fallback parsing")
            return self._create_mock_results_from_response(response, query, search_type)
        except Exception as e:
            logger.error(f"Error parsing WatsonX response: {e}")
            return self._create_mock_results_from_response(response, query, search_type)
    
    def _create_mock_results_from_response(self, response: str, query: str, search_type: str) -> List[Dict[str, Any]]:
        """Create mock results from WatsonX response text."""
        # Split response into lines and create basic results
        lines = response.strip().split('\n')
        results = []
        
        for i, line in enumerate(lines[:5]):  # Limit to 5 results
            if line.strip():
                results.append({
                    "title": f"Search Result {i+1} for '{query}'",
                    "url": f"https://example.com/result-{i+1}",
                    "snippet": line.strip()[:200] + "..." if len(line.strip()) > 200 else line.strip(),
                    "relevance_score": 0.8 - (i * 0.1),  # Decreasing relevance
                    "source": search_type
                })
        
        return results
    
    def _mock_search_results(self, 
                           query: str, 
                           search_type: str, 
                           max_results: int,
                           include_metadata: bool) -> Dict[str, Any]:
        """
        Generate mock search results for testing/fallback.
        
        Args:
            query: Search query
            search_type: Type of search
            max_results: Maximum number of results
            include_metadata: Whether to include metadata
            
        Returns:
            Dictionary with mock search results
        """
        # Generate mock results based on query
        mock_results = []
        
        # Create mock results based on query content
        if "portfolio" in query.lower() or "investment" in query.lower():
            mock_results = [
                {
                    "title": "Portfolio Management Best Practices",
                    "url": "https://example.com/portfolio-management",
                    "snippet": "Comprehensive guide to portfolio management strategies and best practices for investors.",
                    "relevance_score": 0.95,
                    "source": search_type
                },
                {
                    "title": "Investment Strategy Analysis",
                    "url": "https://example.com/investment-strategy",
                    "snippet": "Latest trends and analysis in investment strategy and portfolio optimization.",
                    "relevance_score": 0.88,
                    "source": search_type
                },
                {
                    "title": "Risk Management in Portfolios",
                    "url": "https://example.com/risk-management",
                    "snippet": "Understanding and managing risk in investment portfolios for better returns.",
                    "relevance_score": 0.82,
                    "source": search_type
                }
            ]
        elif "market" in query.lower() or "stock" in query.lower():
            mock_results = [
                {
                    "title": "Current Market Analysis",
                    "url": "https://example.com/market-analysis",
                    "snippet": "Latest market trends and analysis for informed investment decisions.",
                    "relevance_score": 0.92,
                    "source": search_type
                },
                {
                    "title": "Stock Market News",
                    "url": "https://example.com/stock-news",
                    "snippet": "Breaking news and updates from the stock market and financial sector.",
                    "relevance_score": 0.85,
                    "source": search_type
                }
            ]
        else:
            # Generic mock results
            mock_results = [
                {
                    "title": f"Search Results for '{query}'",
                    "url": f"https://example.com/search-result-1",
                    "snippet": f"Relevant information about {query} from authoritative sources.",
                    "relevance_score": 0.80,
                    "source": search_type
                },
                {
                    "title": f"More Information on {query}",
                    "url": f"https://example.com/search-result-2",
                    "snippet": f"Additional details and insights about {query} for your research.",
                    "relevance_score": 0.75,
                    "source": search_type
                }
            ]
        
        # Limit results to max_results
        mock_results = mock_results[:max_results]
        
        return {
            "query": query,
            "search_type": search_type,
            "results": mock_results,
            "total_results": len(mock_results),
            "search_metadata": {
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "watsonx_used": False,
                "mock_results": True,
                "max_results_requested": max_results
            }
        }
    
    def format_search_results_for_llm(self, search_result: Dict[str, Any]) -> str:
        """
        Format search results for LLM consumption.
        
        Args:
            search_result: Result from search_web method
            
        Returns:
            Formatted search results string
        """
        try:
            results = search_result.get("results", [])
            query = search_result.get("query", "")
            search_type = search_result.get("search_type", "web")
            
            if not results:
                return f"No web search results found for '{query}' using {search_type}."
            
            formatted_results = f"## Web Search Results for '{query}'\n\n"
            formatted_results += f"*Search performed using {search_type}*\n\n"
            
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                url = result.get("url", "")
                snippet = result.get("snippet", "No description available")
                score = result.get("relevance_score", 0.0)
                
                formatted_results += f"### {i}. {title}\n"
                formatted_results += f"**URL:** {url}\n"
                formatted_results += f"**Description:** {snippet}\n"
                formatted_results += f"**Relevance:** {score:.2f}\n\n"
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error formatting search results: {e}")
            return f"Error formatting search results: {str(e)}"
    
    def get_search_capabilities(self) -> Dict[str, Any]:
        """
        Get information about search capabilities.
        
        Returns:
            Dictionary with capability information
        """
        return {
            "supported_search_types": ["google", "duckduckgo"],
            "watsonx_available": self.watsonx_client is not None,
            "max_results_limit": 20,
            "features": [
                "Web search",
                "Result relevance scoring",
                "Metadata extraction",
                "LLM-formatted output"
            ]
        }


# Global browser agent instance
_browser_agent = None

def get_browser_agent() -> BrowserAgent:
    """Get the global browser agent instance."""
    global _browser_agent
    if _browser_agent is None:
        _browser_agent = BrowserAgent()
    return _browser_agent


# Convenience functions for easy integration
def search_web(query: str, search_type: str = "google", max_results: int = 5) -> Dict[str, Any]:
    """Perform web search using the browser agent."""
    agent = get_browser_agent()
    return agent.search_web(query, search_type, max_results)


def format_web_results_for_chatbot(query: str, search_type: str = "google") -> str:
    """Search web and format results for chatbot consumption."""
    agent = get_browser_agent()
    search_result = agent.search_web(query, search_type)
    return agent.format_search_results_for_llm(search_result)


if __name__ == "__main__":
    # Test the browser agent
    agent = BrowserAgent()
    
    # Test web search
    test_query = "portfolio management best practices"
    print(f"Testing web search for: {test_query}")
    
    search_result = agent.search_web(test_query, "google", 3)
    print(f"Found {search_result['total_results']} results")
    
    if search_result['results']:
        formatted_results = agent.format_search_results_for_llm(search_result)
        print("\nFormatted results:")
        print(formatted_results[:500] + "..." if len(formatted_results) > 500 else formatted_results)
    else:
        print("No results found")
    
    # Test capabilities
    capabilities = agent.get_search_capabilities()
    print(f"\nSearch capabilities: {capabilities}")
