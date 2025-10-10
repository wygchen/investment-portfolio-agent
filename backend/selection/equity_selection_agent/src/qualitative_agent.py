"""
LangGraph-based Qualitative Analysis Agent for Equity Selection

This module implements a LangGraph agent that performs qualitative business analysis
for investment screening, replacing the mock QualitativeIntegrator with a real
LLM-powered workflow.

Classes:
- QualitativeAnalysisAgent: LangGraph-based agent for company qualitative analysis
"""

import logging
import json
from typing import Dict, List, Optional, Tuple, Any, TypedDict
from dataclasses import dataclass

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import StateGraph, END

from .config import Config

# Set up logging
logger = logging.getLogger(__name__)

# Import watsonx utilities if available
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
    from watsonx_utils import create_watsonx_llm
except ImportError:
    logger.warning("watsonx_utils not available - LLM functionality will be limited")
    create_watsonx_llm = None


@dataclass
class QualitativeScore:
    """Structure for qualitative analysis results"""
    ticker: str
    qual_score: float  # 0-10 scale
    management_integrity: Optional[str] = None
    competitive_advantage: Optional[str] = None
    growth_potential: Optional[str] = None
    overall_assessment: Optional[str] = None
    confidence: Optional[float] = None


class AnalysisOutput(BaseModel):
    """Structured output for company analysis"""
    qual_score: float = Field(description="Overall qualitative score from 0-10", ge=0, le=10)
    management_integrity: str = Field(description="Assessment of management integrity: Excellent, Good, Fair, Poor")
    competitive_advantage: str = Field(description="Competitive advantage assessment: Strong, Moderate, Weak")
    growth_potential: str = Field(description="Growth potential: High, Moderate, Low")
    overall_assessment: str = Field(description="Brief overall assessment summary")
    confidence: float = Field(description="Confidence in analysis from 0-1", ge=0, le=1)
    reasoning: str = Field(description="Key reasoning behind the scores")


class AgentState(TypedDict):
    """State for the qualitative analysis agent"""
    ticker: str
    business_summary: str
    financial_metrics: Dict[str, Any]
    messages: List[BaseMessage]
    analysis_result: Optional[AnalysisOutput]
    error: Optional[str]


def analyze_financial_health(roe: Optional[float], debt_to_equity: Optional[float], pe_ratio: Optional[float]) -> str:
    """
    Analyze financial health metrics and provide interpretation.
    
    Args:
        roe: Return on Equity ratio
        debt_to_equity: Debt to Equity ratio  
        pe_ratio: Price to Earnings ratio
        
    Returns:
        Financial health assessment string
    """
    assessment = []
    
    if roe is not None:
        if roe > 0.20:
            assessment.append(f"Excellent ROE of {roe:.1%} indicates strong profitability")
        elif roe > 0.15:
            assessment.append(f"Good ROE of {roe:.1%} shows solid profitability")
        elif roe > 0.10:
            assessment.append(f"Moderate ROE of {roe:.1%} indicates average profitability")
        else:
            assessment.append(f"Low ROE of {roe:.1%} suggests weak profitability")
    
    if debt_to_equity is not None:
        if debt_to_equity < 0.3:
            assessment.append(f"Conservative debt level (D/E: {debt_to_equity:.2f}) indicates low financial risk")
        elif debt_to_equity < 1.0:
            assessment.append(f"Moderate debt level (D/E: {debt_to_equity:.2f}) shows balanced capital structure")
        elif debt_to_equity < 2.0:
            assessment.append(f"High debt level (D/E: {debt_to_equity:.2f}) suggests elevated financial risk")
        else:
            assessment.append(f"Very high debt level (D/E: {debt_to_equity:.2f}) indicates significant financial risk")
    
    if pe_ratio is not None:
        if pe_ratio < 15:
            assessment.append(f"Low P/E ratio ({pe_ratio:.1f}) suggests undervaluation or low growth expectations")
        elif pe_ratio < 25:
            assessment.append(f"Moderate P/E ratio ({pe_ratio:.1f}) indicates reasonable valuation")
        else:
            assessment.append(f"High P/E ratio ({pe_ratio:.1f}) suggests high growth expectations or overvaluation")
    
    return "; ".join(assessment) if assessment else "Limited financial data available for analysis"


def extract_business_insights(news_data: str, llm=None) -> str:
    """
    Extract key business insights from company news data using LLM.
    
    Args:
        news_data: Company news data (JSON string containing news articles)
        llm: LLM instance for analysis (optional, falls back to heuristics if not provided)
        
    Returns:
        Key business insights and competitive factors from news analysis
    """
    if not news_data or len(news_data.strip()) < 20:
        return "Insufficient news data for meaningful analysis"
    
    # Try LLM-powered analysis first
    if llm is not None:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert business analyst. Analyze the given company news data and extract key business insights.
                
Focus on identifying:
                1. Market position and competitive standing
                2. Innovation and technology focus
                3. Growth indicators and expansion plans
                4. Business challenges or risks
                5. Competitive advantages or differentiators
                6. Recent developments and strategic initiatives
                
Provide a concise analysis highlighting the most important factors for investment evaluation.
                Keep your response focused and under 200 words."""),
                ("human", "Please analyze this company news data and extract key business insights:\n\n{news_data}")
            ])
            
            chain = prompt | llm
            response = chain.invoke({"news_data": news_data})
            
            # Extract content from response
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            logger.warning(f"LLM analysis failed, falling back to heuristics: {e}")
    
    # Fallback to heuristic analysis
    try:
        # Try to parse news data as JSON
        import json
        news_items = json.loads(news_data) if news_data.startswith('[') else []
        
        # Extract text from news items for analysis
        combined_text = ""
        for item in news_items:
            if isinstance(item, dict):
                combined_text += item.get('title', '') + " " + item.get('summary', '') + " "
        
        analysis_text = combined_text.lower() if combined_text else news_data.lower()
    except:
        # If not JSON, treat as plain text
        analysis_text = news_data.lower()
    
    insights = []
    
    # Market position indicators
    leadership_words = ['leading', 'leader', 'largest', 'dominant', 'premier', 'top', 'market share']
    if any(word in analysis_text for word in leadership_words):
        insights.append("Recent news indicates strong market position")
    
    # Innovation indicators
    innovation_words = ['innovative', 'technology', 'research', 'development', 'patent', 'breakthrough', 'launch']
    if any(word in analysis_text for word in innovation_words):
        insights.append("News shows focus on innovation and technology")
    
    # Growth indicators
    growth_words = ['expansion', 'growing', 'growth', 'increasing', 'scaling', 'revenue', 'profit']
    if any(word in analysis_text for word in growth_words):
        insights.append("Recent news indicates growth trajectory")
    
    # Risk indicators
    risk_words = ['challenging', 'declining', 'uncertainty', 'volatile', 'pressure', 'competition', 'lawsuit']
    if any(word in analysis_text for word in risk_words):
        insights.append("Some business challenges or risks mentioned in news")
    
    # Competitive advantage indicators
    advantage_words = ['unique', 'proprietary', 'exclusive', 'specialized', 'differentiated', 'partnership']
    if any(word in analysis_text for word in advantage_words):
        insights.append("News indicates potential competitive advantages")
    
    return "; ".join(insights) if insights else "Limited insights from available news data"


class QualitativeAnalysisAgent:
    """
    LangGraph-based agent for qualitative company analysis.
    Replaces the mock QualitativeIntegrator with real LLM analysis.
    """
    
    def __init__(self, config: Config, llm=None):
        self.config = config
        self.enabled = False
        
        # Initialize LLM (try to create Watsonx LLM if none provided)
        self.llm = llm
        if self.llm is None and create_watsonx_llm is not None:
            try:
                # Try to create Watsonx LLM with conservative parameters for analysis
                self.llm = create_watsonx_llm(
                    model_id="ibm/granite-3-2-8b-instruct",
                    max_tokens=500,  # Shorter responses for insights
                    temperature=0.3,  # Lower temperature for more consistent analysis
                    top_p=0.9
                )
                logger.info("Initialized QualitativeAnalysisAgent with Watsonx LLM")
            except Exception as e:
                logger.warning(f"Failed to initialize Watsonx LLM: {e}. Using mock mode.")
                self.llm = None
        
        if self.llm is None:
            logger.warning("No LLM provided to QualitativeAnalysisAgent, using mock mode")
            
        # Create the analysis workflow
        self.workflow = self._create_workflow()
        
    def _create_workflow(self):
        """Create the LangGraph workflow for qualitative analysis"""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("extract_insights", self._extract_insights_node)
        workflow.add_node("analyze_financials", self._analyze_financials_node)
        workflow.add_node("synthesize_analysis", self._synthesize_analysis_node)
        workflow.add_node("format_output", self._format_output_node)
        
        # Define the workflow edges
        workflow.set_entry_point("extract_insights")
        workflow.add_edge("extract_insights", "analyze_financials")
        workflow.add_edge("analyze_financials", "synthesize_analysis")
        workflow.add_edge("synthesize_analysis", "format_output")
        workflow.add_edge("format_output", END)
        
        return workflow.compile()
    
    def _extract_insights_node(self, state: AgentState) -> AgentState:
        """Extract business insights from company news data"""
        try:
            news_insights = extract_business_insights(state["business_summary"], llm=self.llm)
            
            message = HumanMessage(content=f"News insights for {state['ticker']}: {news_insights}")
            state["messages"].append(message)
            
            return state
        except Exception as e:
            logger.error(f"Error in extract_insights_node: {e}")
            state["error"] = f"Failed to extract news insights: {str(e)}"
            return state
    
    def _analyze_financials_node(self, state: AgentState) -> AgentState:
        """Analyze financial metrics"""
        try:
            metrics = state["financial_metrics"]
            financial_analysis = analyze_financial_health(
                metrics.get("roe"),
                metrics.get("debt_to_equity"),
                metrics.get("pe_ratio")
            )
            
            message = HumanMessage(content=f"Financial analysis for {state['ticker']}: {financial_analysis}")
            state["messages"].append(message)
            
            return state
        except Exception as e:
            logger.error(f"Error in analyze_financials_node: {e}")
            state["error"] = f"Failed to analyze financials: {str(e)}"
            return state
    
    def _synthesize_analysis_node(self, state: AgentState) -> AgentState:
        """Synthesize insights using LLM"""
        try:
            if self.llm is None:
                # Fallback to mock analysis
                return self._mock_synthesis(state)
            
            # Create synthesis prompt with explicit JSON formatting
            synthesis_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert investment analyst performing qualitative analysis of companies.

                Based on the business description and financial metrics provided, analyze the company across these dimensions:
                1. Management integrity and corporate governance
                2. Competitive advantage and market position  
                3. Growth potential and business prospects
                
                You MUST respond with a valid JSON object containing exactly these fields:
                - qual_score: number from 0-10 (overall qualitative score)
                - management_integrity: string ("Excellent", "Good", "Fair", or "Poor")
                - competitive_advantage: string ("Strong", "Moderate", or "Weak")
                - growth_potential: string ("High", "Moderate", or "Low")
                - overall_assessment: string (brief summary)
                - confidence: number from 0-1 (confidence in analysis)
                - reasoning: string (key reasoning for scores)
                
                Example format:
                {{
                  "qual_score": 7.5,
                  "management_integrity": "Good",
                  "competitive_advantage": "Strong",
                  "growth_potential": "High",
                  "overall_assessment": "Strong company with good fundamentals",
                  "confidence": 0.8,
                  "reasoning": "Strong market position and financial metrics"
                }}"""),
                MessagesPlaceholder(variable_name="messages"),
                ("human", """Please provide a comprehensive qualitative analysis for {ticker}.
                
                News Data: {business_summary}
                
                Based on the news insights and financial analysis above, provide your analysis as a JSON object with the required fields.""")
            ])
            
            # Create the chain without JSON parser initially
            chain = synthesis_prompt | self.llm
            
            # Invoke the chain
            response = chain.invoke({
                "ticker": state["ticker"],
                "business_summary": state["business_summary"],
                "messages": state["messages"]
            })
            
            # Extract content from response
            if hasattr(response, 'content'):
                if isinstance(response.content, str):
                    response_text = response.content.strip()
                elif isinstance(response.content, list) and len(response.content) > 0:
                    # Handle list responses by joining them
                    response_text = ' '.join(str(item) for item in response.content).strip()
                else:
                    response_text = str(response.content).strip()
            else:
                response_text = str(response).strip()
            
            # Try to parse JSON from the response
            try:
                # Look for JSON content between braces
                import re
                json_match = re.search(r'\\{.*\\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    result_dict = json.loads(json_str)
                else:
                    # If no JSON found, try to parse the whole response
                    result_dict = json.loads(response_text)
                
                # Validate required fields and create AnalysisOutput
                state["analysis_result"] = AnalysisOutput(
                    qual_score=float(result_dict.get('qual_score', 5.0)),
                    management_integrity=str(result_dict.get('management_integrity', 'Fair')),
                    competitive_advantage=str(result_dict.get('competitive_advantage', 'Moderate')),
                    growth_potential=str(result_dict.get('growth_potential', 'Moderate')),
                    overall_assessment=str(result_dict.get('overall_assessment', 'LLM analysis completed')),
                    confidence=float(result_dict.get('confidence', 0.7)),
                    reasoning=str(result_dict.get('reasoning', 'Analysis based on LLM evaluation'))
                )
                
                logger.info(f"Successfully parsed LLM analysis for {state['ticker']}")
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to parse LLM JSON response for {state['ticker']}: {e}")
                logger.debug(f"LLM response was: {response_text}")
                # Fall back to mock analysis
                return self._mock_synthesis(state)
            
            return state
            
        except Exception as e:
            logger.error(f"Error in synthesize_analysis_node: {e}")
            state["error"] = f"Failed to synthesize analysis: {str(e)}"
            return self._mock_synthesis(state)
    
    def _mock_synthesis(self, state: AgentState) -> AgentState:
        """Fallback mock synthesis when LLM is not available"""
        try:
            # Extract insights from messages for mock scoring
            news_insights = ""
            financial_insights = ""
            
            for msg in state["messages"]:
                if "News insights" in msg.content:
                    news_insights = msg.content
                elif "Financial analysis" in msg.content:
                    financial_insights = msg.content
            
            # Simple heuristic scoring based on extracted insights
            base_score = 5.0
            
            # Adjust based on news insights
            if "strong market position" in news_insights:
                base_score += 1.0
            if "innovation and technology" in news_insights:
                base_score += 0.5
            if "growth trajectory" in news_insights:
                base_score += 0.5
            if "business challenges" in news_insights:
                base_score -= 0.5
            if "competitive advantages" in news_insights:
                base_score += 1.0
            
            # Adjust based on financial health
            metrics = state["financial_metrics"]
            if metrics.get("roe", 0) > 0.15:
                base_score += 0.5
            if metrics.get("debt_to_equity", 10) < 1.0:
                base_score += 0.5
            if metrics.get("pe_ratio", 100) < 20:
                base_score += 0.3
            
            final_score = max(0, min(10, base_score))
            
            # Create mock analysis result
            state["analysis_result"] = AnalysisOutput(
                qual_score=final_score,
                management_integrity="Good" if final_score > 6 else "Fair",
                competitive_advantage="Strong" if "competitive advantages" in news_insights else "Moderate",
                growth_potential="High" if "growth trajectory" in news_insights else "Moderate",
                overall_assessment=f"Qualitative score: {final_score:.1f}/10 based on news analysis",
                confidence=0.7,
                reasoning="Analysis based on news data keywords and financial metrics heuristics"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error in mock synthesis: {e}")
            state["error"] = f"Failed to complete mock analysis: {str(e)}"
            return state
    
    def _format_output_node(self, state: AgentState) -> AgentState:
        """Format the final output"""
        try:
            if state.get("error"):
                # Return default neutral score on error
                state["analysis_result"] = AnalysisOutput(
                    qual_score=5.0,
                    management_integrity="Fair",
                    competitive_advantage="Moderate", 
                    growth_potential="Moderate",
                    overall_assessment="Analysis failed - using neutral score",
                    confidence=0.1,
                    reasoning=f"Error occurred: {state['error']}"
                )
            
            return state
            
        except Exception as e:
            logger.error(f"Error in format_output_node: {e}")
            state["error"] = f"Failed to format output: {str(e)}"
            return state
    
    def enable_qualitative_analysis(self, enable: bool = True):
        """Enable or disable qualitative analysis"""
        self.enabled = enable
        logger.info(f"Qualitative analysis {'enabled' if enable else 'disabled'}")
    
    def analyze_company(self, ticker: str, news_data: str, 
                       financial_metrics: Dict[str, Any]) -> Optional[QualitativeScore]:
        """
        Analyze a company's qualitative factors using the LangGraph agent.
        
        Args:
            ticker: Stock ticker symbol
            news_data: Company news data (JSON string or text)
            financial_metrics: Relevant financial metrics for context
            
        Returns:
            QualitativeScore object or None if analysis fails
        """
        if not self.enabled:
            return None
        
        if not news_data or len(news_data.strip()) < 20:
            logger.warning(f"Insufficient news data for {ticker}")
            return None
        
        try:
            # Create initial state
            initial_state = AgentState(
                ticker=ticker,
                business_summary=news_data,  # Reusing the field name for news data
                financial_metrics=financial_metrics,
                messages=[],
                analysis_result=None,
                error=None
            )
            
            # Run the workflow
            final_state = self.workflow.invoke(initial_state)
            
            # Convert to QualitativeScore
            if final_state["analysis_result"]:
                result = final_state["analysis_result"]
                return QualitativeScore(
                    ticker=ticker,
                    qual_score=result.qual_score,
                    management_integrity=result.management_integrity,
                    competitive_advantage=result.competitive_advantage,
                    growth_potential=result.growth_potential,
                    overall_assessment=result.overall_assessment,
                    confidence=result.confidence
                )
            else:
                logger.error(f"No analysis result for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error in qualitative analysis for {ticker}: {e}")
            return None
    
    def batch_analyze(self, companies_data: Dict[str, Dict[str, Any]]) -> Dict[str, QualitativeScore]:
        """
        Analyze multiple companies in batch.
        
        Args:
            companies_data: Dictionary with ticker as key and company data as value
            
        Returns:
            Dictionary of qualitative scores by ticker
        """
        if not self.enabled:
            return {}
        
        results = {}
        
        for ticker, data in companies_data.items():
            news_data = data.get('news', '')
            financial_metrics = {
                'roe': data.get('roe'),
                'debt_to_equity': data.get('debt_to_equity'),
                'pe_ratio': data.get('pe_ratio')
            }
            
            qual_score = self.analyze_company(ticker, news_data, financial_metrics)
            if qual_score:
                results[ticker] = qual_score
        
        logger.info(f"Completed qualitative analysis for {len(results)} companies")
        return results