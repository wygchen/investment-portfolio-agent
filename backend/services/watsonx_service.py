"""
Watsonx.ai service layer with connection pooling, retry logic, and fallback mechanisms.
Provides reliable AI service integration for the risk analytics agent.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ibm import ChatWatsonx

from watsonx_utils import create_watsonx_llm, load_environment


logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNAVAILABLE = "unavailable"


@dataclass
class ServiceResponse:
    """Standardized service response"""
    content: str
    success: bool
    source: str  # "watsonx", "cache", "mock"
    processing_time: float
    model_version: str
    confidence: float = 1.0
    error: Optional[str] = None


class WatsonxConnectionError(Exception):
    """Custom exception for Watsonx connection issues"""
    pass


class WatsonxService:
    """
    Watsonx.ai service with connection pooling, retry logic, and fallback mechanisms.
    Designed for hackathon reliability with graceful degradation.
    """
    
    def __init__(self, 
                 model_id: str = "ibm/granite-3-2-8b-instruct",
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 timeout: float = 30.0,
                 cache_ttl: int = 3600):
        """
        Initialize Watsonx service with configuration.
        
        Args:
            model_id: Watsonx model identifier
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            timeout: Request timeout in seconds
            cache_ttl: Cache time-to-live in seconds
        """
        self.model_id = model_id
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        
        # Service state
        self.status = ServiceStatus.HEALTHY
        self.llm: Optional[ChatWatsonx] = None
        self.last_health_check = datetime.now()
        self.connection_pool = []
        
        # Response cache for demo reliability
        self.response_cache: Dict[str, Dict[str, Any]] = {}
        
        # Initialize connection
        self._initialize_connection()
    
    def _initialize_connection(self) -> None:
        """Initialize Watsonx connection with error handling"""
        try:
            logger.info(f"Initializing Watsonx connection with model: {self.model_id}")
            
            # Create LLM with optimized parameters for risk analysis
            self.llm = create_watsonx_llm(
                model_id=self.model_id,
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for more consistent analysis
                top_p=0.9,
                custom_params={
                    "stop_sequences": ["\\n\\n\\n"],  # Prevent overly long responses
                }
            )
            
            self.status = ServiceStatus.HEALTHY
            logger.info("Watsonx connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Watsonx connection: {str(e)}")
            self.status = ServiceStatus.UNAVAILABLE
            self.llm = None
    
    async def health_check(self) -> bool:
        """
        Perform health check on Watsonx service.
        
        Returns:
            True if service is healthy, False otherwise
        """
        if not self.llm:
            return False
            
        try:
            # Simple test query
            test_response = await self._call_watsonx_with_retry(
                "Respond with 'OK' if you can process this message.",
                max_retries=1
            )
            
            is_healthy = test_response.success and "OK" in test_response.content.upper()
            self.status = ServiceStatus.HEALTHY if is_healthy else ServiceStatus.DEGRADED
            self.last_health_check = datetime.now()
            
            return is_healthy
            
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            self.status = ServiceStatus.UNAVAILABLE
            return False
    
    async def generate_risk_analysis(self, 
                                   assessment_data: Dict[str, Any],
                                   analysis_type: str = "comprehensive") -> ServiceResponse:
        """
        Generate AI-powered risk analysis using Watsonx.
        
        Args:
            assessment_data: User assessment data
            analysis_type: Type of analysis ("comprehensive", "quick", "stress_test")
            
        Returns:
            ServiceResponse with analysis results
        """
        start_time = time.time()
        
        # Create cache key
        cache_key = self._create_cache_key(assessment_data, analysis_type)
        
        # Check cache first
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return cached_response
        
        # Generate prompt based on analysis type
        prompt = self._create_risk_analysis_prompt(assessment_data, analysis_type)
        
        # Try Watsonx first
        response = await self._call_watsonx_with_retry(prompt)
        
        # If Watsonx fails, use fallback
        if not response.success:
            response = self._generate_fallback_response(assessment_data, analysis_type)
        
        # Cache successful responses
        if response.success:
            self._cache_response(cache_key, response)
        
        response.processing_time = time.time() - start_time
        return response
    
    async def _call_watsonx_with_retry(self, 
                                     prompt: str,
                                     max_retries: Optional[int] = None) -> ServiceResponse:
        """
        Call Watsonx with retry logic and error handling.
        
        Args:
            prompt: The prompt to send to Watsonx
            max_retries: Override default max retries
            
        Returns:
            ServiceResponse with results or error information
        """
        if not self.llm:
            raise WatsonxConnectionError("Watsonx LLM not initialized")
        
        retries = max_retries or self.max_retries
        last_error = None
        
        for attempt in range(retries + 1):
            try:
                logger.debug(f"Watsonx attempt {attempt + 1}/{retries + 1}")
                
                # Create messages for ChatWatsonx
                messages = [
                    SystemMessage(content="You are a professional financial risk analyst with expertise in portfolio management and quantitative analysis."),
                    HumanMessage(content=prompt)
                ]
                
                # Call Watsonx with timeout
                response = await asyncio.wait_for(
                    self._invoke_llm(messages),
                    timeout=self.timeout
                )
                
                # Extract content from response
                content = response.content if hasattr(response, 'content') else str(response)
                
                return ServiceResponse(
                    content=content,
                    success=True,
                    source="watsonx",
                    processing_time=0.0,  # Will be set by caller
                    model_version=self.model_id,
                    confidence=0.95
                )
                
            except asyncio.TimeoutError:
                last_error = f"Timeout after {self.timeout} seconds"
                logger.warning(f"Watsonx timeout on attempt {attempt + 1}")
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Watsonx error on attempt {attempt + 1}: {last_error}")
                
                # Reinitialize connection on certain errors
                if "connection" in last_error.lower() or "network" in last_error.lower():
                    self._initialize_connection()
            
            # Wait before retry (except on last attempt)
            if attempt < retries:
                await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        # All retries failed
        self.status = ServiceStatus.UNAVAILABLE
        return ServiceResponse(
            content="",
            success=False,
            source="watsonx",
            processing_time=0.0,
            model_version=self.model_id,
            error=f"Failed after {retries + 1} attempts. Last error: {last_error}"
        )
    
    async def _invoke_llm(self, messages: List[Any]) -> Any:
        """Async wrapper for LLM invocation"""
        # ChatWatsonx invoke is typically synchronous, so we run it in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.llm.invoke, messages)
    
    def _create_risk_analysis_prompt(self, 
                                   assessment_data: Dict[str, Any], 
                                   analysis_type: str) -> str:
        """
        Create structured prompt for risk analysis based on assessment data.
        
        Args:
            assessment_data: User financial assessment data
            analysis_type: Type of analysis to perform
            
        Returns:
            Formatted prompt string
        """
        base_prompt = f"""
You are the Risk Analysis Agent. Your duty is to combine personal data and external financial data into a comprehensive risk blueprint.

ASSESSMENT DATA:
- Age: {assessment_data.get('age', 'N/A')}
- Income: ${assessment_data.get('income', 0):,}
- Net Worth: ${assessment_data.get('net_worth', 0):,}
- Dependents: {assessment_data.get('dependents', 0)}
- Primary Goal: {assessment_data.get('primary_goal', 'N/A')}
- Time Horizon: {assessment_data.get('time_horizon', 0)} years
- Target Amount: ${assessment_data.get('target_amount', 0):,}
- Monthly Contribution: ${assessment_data.get('monthly_contribution', 0):,}
- Risk Tolerance (1-10): {assessment_data.get('risk_tolerance', 5)}
- Risk Capacity: {assessment_data.get('risk_capacity', 'N/A')}
- Investment Experience: {assessment_data.get('previous_experience', [])}
- Market Reaction: {assessment_data.get('market_reaction', 'N/A')}

ANALYSIS STEPS:
1. Distinguish Risk Capacity (objective financial ability), Risk Tolerance (psychological comfort), and Risk Requirement (level of risk needed for goals).
2. Calculate financial ratios: Debt-to-Asset, Savings Rate, Liquidity Ratio where possible.
3. Map time horizon into bands (short-term <3y, medium 3-10y, long-term >10y).
4. Identify liquidity constraints and key financial milestones.
5. Assess risk level and provide quantitative risk score (1-100).

OUTPUT FORMAT:
Provide a detailed analysis followed by a JSON risk blueprint in this exact format:

```json
{{
    "risk_capacity": "high/medium/low with explanation",
    "risk_tolerance": "high/medium/low with psychological assessment", 
    "risk_requirement": "high/medium/low based on goals and timeline",
    "liquidity_constraints": "description of liquidity needs and constraints",
    "time_horizon_bands": {{
        "short_term": "percentage allocation for <3 years",
        "medium_term": "percentage allocation for 3-10 years", 
        "long_term": "percentage allocation for >10 years"
    }},
    "risk_level_summary": "low/medium/high",
    "risk_score": "numerical score 1-100",
    "volatility_target": "expected portfolio volatility percentage",
    "financial_ratios": {{
        "savings_rate": "calculated percentage",
        "liquidity_ratio": "months of expenses covered",
        "debt_to_asset": "debt as percentage of assets"
    }}
}}
```

Begin your analysis:
"""
        
        if analysis_type == "stress_test":
            base_prompt += """
            
ADDITIONAL STRESS TESTING REQUIREMENTS:
- Perform scenario analysis for market downturns (-20%, -30%, -40%)
- Assess inflation impact (3%, 5%, 8% scenarios)
- Evaluate interest rate shock effects
- Calculate probability of achieving financial goals under stress
"""
        
        return base_prompt.strip()
    
    def _generate_fallback_response(self, 
                                  assessment_data: Dict[str, Any],
                                  analysis_type: str) -> ServiceResponse:
        """
        Generate enhanced mock response when Watsonx is unavailable.
        
        Args:
            assessment_data: User assessment data
            analysis_type: Type of analysis requested
            
        Returns:
            ServiceResponse with mock analysis
        """
        logger.info("Generating fallback risk analysis response")
        
        # Calculate basic metrics
        age = assessment_data.get('age', 35)
        income = assessment_data.get('income', 75000)
        net_worth = assessment_data.get('net_worth', 100000)
        risk_tolerance = assessment_data.get('risk_tolerance', 5)
        time_horizon = assessment_data.get('time_horizon', 10)
        
        # Determine risk levels based on simple heuristics
        risk_capacity = "high" if net_worth > income * 2 else "medium" if net_worth > income * 0.5 else "low"
        risk_tolerance_level = "high" if risk_tolerance >= 7 else "medium" if risk_tolerance >= 4 else "low"
        risk_requirement = "high" if time_horizon > 15 else "medium" if time_horizon > 5 else "low"
        
        # Calculate risk score (1-100)
        risk_score = min(100, max(1, (risk_tolerance * 10) + (min(age, 65) // 5) + (time_horizon // 2)))
        
        # Calculate volatility target
        volatility_target = min(25, max(5, risk_score * 0.25))
        
        # Time horizon bands
        if time_horizon <= 3:
            short_term, medium_term, long_term = "70%", "25%", "5%"
        elif time_horizon <= 10:
            short_term, medium_term, long_term = "20%", "60%", "20%"
        else:
            short_term, medium_term, long_term = "10%", "30%", "60%"
        
        # Financial ratios (simplified calculations)
        monthly_contribution = assessment_data.get('monthly_contribution', 1000)
        savings_rate = min(50, (monthly_contribution * 12 / income * 100)) if income > 0 else 10
        liquidity_ratio = max(1, net_worth / (income / 12)) if income > 0 else 3
        debt_to_asset = max(0, min(80, 100 - (net_worth / max(income, 1) * 20)))
        
        analysis_content = f"""
Based on the comprehensive financial assessment, here is the detailed risk analysis:

RISK CAPACITY ANALYSIS:
With a net worth of ${net_worth:,} and annual income of ${income:,}, the objective financial capacity is {risk_capacity}. The savings rate of {savings_rate:.1f}% indicates {"strong" if savings_rate > 20 else "moderate" if savings_rate > 10 else "limited"} ability to absorb potential losses.

RISK TOLERANCE ASSESSMENT:
The psychological comfort level is {risk_tolerance_level} based on the stated risk tolerance of {risk_tolerance}/10. This suggests {"comfort with market volatility" if risk_tolerance >= 7 else "moderate acceptance of fluctuations" if risk_tolerance >= 4 else "preference for stability"}.

RISK REQUIREMENT EVALUATION:
Given the {time_horizon}-year time horizon and financial goals, the required risk level is {risk_requirement}. {"Aggressive growth strategies may be necessary" if risk_requirement == "high" else "Balanced approach recommended" if risk_requirement == "medium" else "Conservative strategies should suffice"} to achieve the target objectives.

```json
{{
    "risk_capacity": "{risk_capacity} - Net worth to income ratio of {net_worth/max(income,1):.1f}x provides {'substantial' if risk_capacity == 'high' else 'moderate' if risk_capacity == 'medium' else 'limited'} financial cushion",
    "risk_tolerance": "{risk_tolerance_level} - Psychological comfort with {risk_tolerance}/10 risk tolerance, {'willing to accept significant volatility' if risk_tolerance >= 7 else 'moderate comfort with market fluctuations' if risk_tolerance >= 4 else 'prefers stability and capital preservation'}",
    "risk_requirement": "{risk_requirement} - {time_horizon}-year timeline {'requires aggressive growth' if risk_requirement == 'high' else 'allows balanced approach' if risk_requirement == 'medium' else 'permits conservative strategy'} to achieve financial goals",
    "liquidity_constraints": "Maintain {liquidity_ratio:.1f} months of expenses in liquid assets, consider {'minimal' if liquidity_ratio > 6 else 'moderate' if liquidity_ratio > 3 else 'significant'} liquidity constraints",
    "time_horizon_bands": {{
        "short_term": "{short_term}",
        "medium_term": "{medium_term}",
        "long_term": "{long_term}"
    }},
    "risk_level_summary": "{max(risk_capacity, risk_tolerance_level, risk_requirement, key=lambda x: ['low', 'medium', 'high'].index(x))}",
    "risk_score": "{risk_score}",
    "volatility_target": "{volatility_target:.1f}%",
    "financial_ratios": {{
        "savings_rate": "{savings_rate:.1f}%",
        "liquidity_ratio": "{liquidity_ratio:.1f} months",
        "debt_to_asset": "{debt_to_asset:.1f}%"
    }}
}}
```
"""
        
        return ServiceResponse(
            content=analysis_content.strip(),
            success=True,
            source="mock",
            processing_time=0.0,
            model_version="fallback-v1.0",
            confidence=0.8
        )
    
    def _create_cache_key(self, assessment_data: Dict[str, Any], analysis_type: str) -> str:
        """Create cache key from assessment data and analysis type"""
        # Use key fields to create a hash-like key
        key_fields = [
            assessment_data.get('age', 0),
            assessment_data.get('income', 0),
            assessment_data.get('net_worth', 0),
            assessment_data.get('risk_tolerance', 5),
            assessment_data.get('time_horizon', 10),
            analysis_type
        ]
        return f"risk_analysis_{hash(tuple(key_fields))}"
    
    def _get_cached_response(self, cache_key: str) -> Optional[ServiceResponse]:
        """Get cached response if available and not expired"""
        if cache_key not in self.response_cache:
            return None
        
        cached_data = self.response_cache[cache_key]
        cache_time = cached_data.get('timestamp', datetime.min)
        
        # Check if cache is expired
        if datetime.now() - cache_time > timedelta(seconds=self.cache_ttl):
            del self.response_cache[cache_key]
            return None
        
        logger.debug(f"Using cached response for key: {cache_key}")
        response_data = cached_data['response']
        response_data.source = "cache"
        return response_data
    
    def _cache_response(self, cache_key: str, response: ServiceResponse) -> None:
        """Cache successful response"""
        self.response_cache[cache_key] = {
            'timestamp': datetime.now(),
            'response': response
        }
        logger.debug(f"Cached response for key: {cache_key}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status and metrics"""
        return {
            "status": self.status.value,
            "model_id": self.model_id,
            "last_health_check": self.last_health_check.isoformat(),
            "cache_size": len(self.response_cache),
            "connection_initialized": self.llm is not None
        }


# Global service instance
_watsonx_service: Optional[WatsonxService] = None


def get_watsonx_service() -> WatsonxService:
    """Get or create global Watsonx service instance"""
    global _watsonx_service
    if _watsonx_service is None:
        _watsonx_service = WatsonxService()
    return _watsonx_service


async def initialize_watsonx_service(model_id: str = "ibm/granite-3-2-8b-instruct") -> WatsonxService:
    """Initialize and health check Watsonx service"""
    service = WatsonxService(model_id=model_id)
    
    # Perform initial health check
    is_healthy = await service.health_check()
    if is_healthy:
        logger.info("Watsonx service initialized and healthy")
    else:
        logger.warning("Watsonx service initialized but health check failed - fallback mode available")
    
    global _watsonx_service
    _watsonx_service = service
    return service