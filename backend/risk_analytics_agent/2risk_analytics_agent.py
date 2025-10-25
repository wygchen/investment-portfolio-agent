"""
Risk Analytics Agent for comprehensive financial risk assessment.
Specializes in analyzing user assessment data and generating risk blueprints.
"""

import json
import logging
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import re
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ibm import ChatWatsonx

from .base_agent import BaseAgent, AgentContext, AgentStatus
from .utils.financial_ratios import FinancialRatioEngine


logger = logging.getLogger(__name__)


class RiskAnalyticsAgent(BaseAgent):
    """
    Specialized agent for risk analysis and blueprint generation.
    Combines personal financial data with market conditions to create comprehensive risk assessments. 
   """
    
    def __init__(self, llm: ChatWatsonx):
        """Initialize Risk Analytics Agent with specialized prompts and configuration."""
        
        system_prompt = """
You are the Risk Analysis Agent, a specialized AI financial advisor with expertise in quantitative risk assessment and portfolio management. Your role is to analyze personal financial data and create comprehensive risk blueprints that inform investment decisions.

CORE RESPONSIBILITIES:
1. Distinguish between Risk Capacity (objective financial ability), Risk Tolerance (psychological comfort), and Risk Requirement (level of risk needed for goals)
2. Calculate and interpret financial ratios: Debt-to-Asset, Savings Rate, Liquidity Ratio
3. Map time horizons into strategic bands (short-term <3y, medium 3-10y, long-term >10y)
4. Identify liquidity constraints and key financial milestones
5. Perform stress testing and scenario analysis
6. Generate quantitative risk scores and volatility targets
7. Use given tools and pre-written LLM functions for calculations and assessments

ANALYSIS METHODOLOGY:
- Use evidence-based financial planning principles
- Apply modern portfolio theory concepts
- Consider behavioral finance factors
- Incorporate Monte Carlo simulation concepts
- Provide clear rationale for all assessments

OUTPUT REQUIREMENTS:
- Professional, detailed analysis with clear explanations
- Structured JSON risk blueprint with all required fields
- Quantitative metrics with supporting calculations
- Actionable insights for portfolio construction

TONE: Professional, analytical, confident, and educational. Explain complex concepts clearly while maintaining technical accuracy.
"""
        
        super().__init__(
            name="RiskAnalyticsAgent",
            llm=llm,
            system_prompt=system_prompt,
            max_retries=3
        )
        
        # Initialize financial ratio engine
        self.ratio_engine = FinancialRatioEngine()
        
        # Risk analysis configuration
        self.risk_score_weights = {
            "age_factor": 0.2,
            "time_horizon_factor": 0.25,
            "risk_tolerance_factor": 0.3,
            "financial_capacity_factor": 0.25
        }
        
        # Volatility mapping (risk score to expected portfolio volatility)
        self.volatility_mapping = {
            (1, 20): 5.0,    # Very conservative
            (21, 35): 8.0,   # Conservative
            (36, 50): 12.0,  # Moderate conservative
            (51, 65): 16.0,  # Moderate
            (66, 80): 20.0,  # Moderate aggressive
            (81, 95): 25.0,  # Aggressive
            (96, 100): 30.0  # Very aggressive
        }
    
    async def _execute_agent_logic(self, context: AgentContext) -> Dict[str, Any]:
        """
        Execute comprehensive risk analysis logic.
        
        Args:
            context: Agent context with user assessment data
            
        Returns:
            Dictionary with risk analysis results
        """
        assessment = self._normalize_user_assessment(context.user_assessment)
        
        # Step 1: Calculate comprehensive financial ratios using the engine
        ratio_results = self.ratio_engine.calculate_all_ratios(assessment)
        financial_ratios = self._extract_key_ratios(ratio_results)
        ratio_summary = self.ratio_engine.generate_ratio_summary(ratio_results)
        
        # Step 2: Assess risk components using enhanced ratio data
        risk_capacity = self._assess_risk_capacity(assessment, financial_ratios, ratio_results)
        risk_tolerance = self._assess_risk_tolerance(assessment)
        risk_requirement = self._assess_risk_requirement(assessment)
        
        # Step 3: Calculate quantitative risk score using comprehensive data
        risk_score = self._calculate_enhanced_risk_score(assessment, financial_ratios, ratio_summary)
        
        # Step 4: Map to volatility target
        volatility_target = self._map_risk_to_volatility(risk_score)
        
        # Step 5: Analyze time horizon bands
        time_horizon_bands = self._analyze_time_horizon_bands(assessment)
        
        # Step 6: Assess liquidity constraints
        liquidity_constraints = self._assess_liquidity_constraints(assessment, financial_ratios)
        
        # Step 7: Generate AI-powered analysis with comprehensive ratio data
        ai_analysis = await self._generate_ai_analysis(
            assessment, financial_ratios, risk_capacity, 
            risk_tolerance, risk_requirement, risk_score, ratio_summary
        )
        
        # Step 8: Create structured risk blueprint
        risk_blueprint = self._create_risk_blueprint(
            risk_capacity, risk_tolerance, risk_requirement,
            liquidity_constraints, time_horizon_bands, risk_score,
            volatility_target, financial_ratios
        )
        
        return {
            "content": ai_analysis,
            "structured_data": {
                "risk_blueprint": risk_blueprint,
                "financial_ratios": financial_ratios,
                "comprehensive_ratios": ratio_results,
                "ratio_summary": ratio_summary,
                "risk_score": risk_score,
                "volatility_target": volatility_target,
                "analysis_components": {
                    "risk_capacity": risk_capacity,
                    "risk_tolerance": risk_tolerance,
                    "risk_requirement": risk_requirement
                }
            },
            "confidence": 0.92
        }
    
    def _extract_key_ratios(self, ratio_results: Dict[str, Any]) -> Dict[str, float]:
        """Extract key ratio values for backward compatibility."""
        key_ratios = {}
        
        # Extract the main ratios we use in other calculations
        if "savings_rate" in ratio_results:
            key_ratios["savings_rate"] = ratio_results["savings_rate"].value
        
        if "liquidity_ratio" in ratio_results:
            key_ratios["liquidity_ratio"] = ratio_results["liquidity_ratio"].value
            
        if "debt_to_asset" in ratio_results:
            key_ratios["debt_to_asset"] = ratio_results["debt_to_asset"].value
            
        if "debt_to_income" in ratio_results:
            key_ratios["debt_to_income"] = ratio_results["debt_to_income"].value
            
        if "net_worth_to_income" in ratio_results:
            key_ratios["net_worth_to_income"] = ratio_results["net_worth_to_income"].value
        
        return key_ratios
    
    
    
    async def _generate_ai_analysis(self, assessment: Dict[str, Any], ratios: Dict[str, float],
                                  risk_capacity: Dict[str, Any], risk_tolerance: Dict[str, Any],
                                  risk_requirement: Dict[str, Any], risk_score: int,
                                  ratio_summary: Optional[Dict[str, Any]] = None) -> str:
        """Generate AI-powered detailed risk analysis."""
        
        analysis_prompt = f"""
Provide a comprehensive risk analysis based on the following financial profile:

FINANCIAL PROFILE:
- Age: {assessment.get('age')} years
- Annual Income: ${assessment.get('income', 0):,}
- Net Worth: ${assessment.get('net_worth', 0):,}
- Dependents: {assessment.get('dependents', 0)}
- Time Horizon: {assessment.get('time_horizon')} years
- Target Amount: ${assessment.get('target_amount', 0):,}
- Monthly Contribution: ${assessment.get('monthly_contribution', 0):,}
- Risk Tolerance (1-10): {assessment.get('risk_tolerance')}

CALCULATED METRICS:
- Savings Rate: {ratios.get('savings_rate', 0):.1f}%
- Liquidity Ratio: {ratios.get('liquidity_ratio', 0):.1f} months
- Debt-to-Asset Ratio: {ratios.get('debt_to_asset', 0):.1f}%
- Overall Risk Score: {risk_score}/100

RISK ASSESSMENT RESULTS:
- Risk Capacity: {risk_capacity['level']} ({risk_capacity['score']}/100)
- Risk Tolerance: {risk_tolerance['level']} ({risk_tolerance['score']}/100)  
- Risk Requirement: {risk_requirement['level']} ({risk_requirement['score']}/100)

COMPREHENSIVE RATIO ANALYSIS:
{self._format_ratio_summary_for_ai(ratio_summary) if ratio_summary else "Standard ratio analysis applied"}

Please provide:
1. Executive summary of the risk profile
2. Detailed analysis of each risk component
3. Key insights and recommendations based on comprehensive financial ratios
4. Potential risk factors to monitor
5. Integration of quantitative ratio analysis with qualitative assessment

Format your response professionally with clear sections and actionable insights.
"""
        
        try:
            messages = self._create_messages(analysis_prompt, include_context=False)
            ai_response = await self._call_llm_with_retry(messages)
            return ai_response
        except Exception as e:
            logger.warning(f"AI analysis generation failed: {e}")
            return self._generate_fallback_analysis(assessment, ratios, risk_capacity, risk_tolerance, risk_requirement, risk_score)
    
    def _format_ratio_summary_for_ai(self, ratio_summary: Dict[str, Any]) -> str:
        """Format ratio summary for AI analysis prompt."""
        if not ratio_summary:
            return "No comprehensive ratio analysis available"
        
        summary_text = f"""
- Overall Financial Health Score: {ratio_summary.get('overall_score', 0):.1f}/100
- Health Status: {ratio_summary.get('health_status', 'Unknown')}
- Total Ratios Analyzed: {ratio_summary.get('total_ratios_calculated', 0)}

Key Recommendations from Ratio Analysis:
"""
        
        recommendations = ratio_summary.get('recommendations', [])
        for i, rec in enumerate(recommendations[:3], 1):  # Top 3 recommendations
            summary_text += f"{i}. {rec}\n"
        
        warnings = ratio_summary.get('key_warnings', [])
        if warnings:
            summary_text += f"\nKey Warning Flags:\n"
            for warning in warnings[:3]:  # Top 3 warnings
                summary_text += f"- {warning}\n"
        
        return summary_text.strip()
    
    def _generate_fallback_analysis(self, assessment: Dict[str, Any], ratios: Dict[str, float],
                                  risk_capacity: Dict[str, Any], risk_tolerance: Dict[str, Any],
                                  risk_requirement: Dict[str, Any], risk_score: int) -> str:
        """Generate fallback analysis when AI is unavailable."""
        
        age = assessment.get('age', 35)
        income = assessment.get('income', 0)
        net_worth = assessment.get('net_worth', 0)
        time_horizon = assessment.get('time_horizon', 10)
        
        return f"""
COMPREHENSIVE RISK ANALYSIS REPORT

EXECUTIVE SUMMARY:
Based on the financial assessment, this {age}-year-old investor presents a {risk_capacity['level']} risk capacity profile with {risk_tolerance['level']} psychological risk tolerance. The overall risk score of {risk_score}/100 suggests a {"conservative" if risk_score < 40 else "moderate" if risk_score < 70 else "aggressive"} investment approach is appropriate.

RISK CAPACITY ANALYSIS:
The objective financial capacity is rated as {risk_capacity['level']} based on:
- Income level of ${income:,} providing {"strong" if income > 100000 else "moderate" if income > 50000 else "limited"} earning power
- Net worth of ${net_worth:,} offering {"substantial" if net_worth > 500000 else "adequate" if net_worth > 100000 else "limited"} financial cushion
- Savings rate of {ratios['savings_rate']:.1f}% indicating {"excellent" if ratios['savings_rate'] > 20 else "good" if ratios['savings_rate'] > 10 else "needs improvement"} financial discipline
- Debt-to-asset ratio of {ratios['debt_to_asset']:.1f}% showing {"low" if ratios['debt_to_asset'] < 30 else "moderate" if ratios['debt_to_asset'] < 60 else "high"} leverage

RISK TOLERANCE ASSESSMENT:
The psychological comfort level is {risk_tolerance['level']}, indicating the investor {"is comfortable with significant market volatility" if risk_tolerance['level'] == 'high' else "can accept moderate fluctuations" if risk_tolerance['level'] == 'medium' else "prefers stability and capital preservation"}.

RISK REQUIREMENT EVALUATION:
Given the {time_horizon}-year investment timeline and financial goals, a {risk_requirement['level']} risk approach is needed. {"Aggressive growth strategies may be necessary" if risk_requirement['level'] == 'high' else "A balanced growth approach should suffice" if risk_requirement['level'] == 'medium' else "Conservative strategies can achieve the goals"} to reach the target objectives.

KEY RECOMMENDATIONS:
1. {"Focus on growth-oriented investments" if risk_score > 60 else "Maintain balanced allocation" if risk_score > 40 else "Prioritize capital preservation"}
2. Maintain emergency fund of {ratios['liquidity_ratio']:.1f} months expenses
3. {"Consider tax-advantaged accounts" if income > 75000 else "Build emergency fund first"}
4. {"Regular portfolio rebalancing recommended" if time_horizon > 5 else "Focus on short-term stability"}

RISK FACTORS TO MONITOR:
- Market volatility impact on {"growth-focused" if risk_score > 60 else "balanced"} portfolio
- {"Income stability given high savings rate" if ratios['savings_rate'] > 20 else "Savings rate improvement opportunities"}
- {"Debt management" if ratios['debt_to_asset'] > 40 else "Liquidity management"}
- Time horizon adjustments as goals approach
"""
    
    def _create_risk_blueprint(self, risk_capacity: Dict[str, Any], risk_tolerance: Dict[str, Any],
                             risk_requirement: Dict[str, Any], liquidity_constraints: Dict[str, Any],
                             time_horizon_bands: Dict[str, str], risk_score: int,
                             volatility_target: float, financial_ratios: Dict[str, float]) -> Dict[str, Any]:
        """Create structured risk blueprint JSON."""
        
        # Determine overall risk level
        risk_levels = [risk_capacity['level'], risk_tolerance['level'], risk_requirement['level']]
        risk_level_priority = {'low': 0, 'medium': 1, 'high': 2}
        
        # Use the most conservative (lowest) risk level for safety
        overall_risk_level = min(risk_levels, key=lambda x: risk_level_priority[x])
        
        return {
            # Keep original structure for main_agent.py compatibility
            "risk_capacity": risk_capacity,  # Keep as dict with 'level' key
            "risk_tolerance": risk_tolerance,  # Keep as dict with 'level' key  
            "risk_requirement": risk_requirement,  # Keep as dict with 'level' key
            "liquidity_constraints": liquidity_constraints,
            "time_horizon_bands": time_horizon_bands,
            "risk_level_summary": overall_risk_level,
            "risk_score": str(risk_score),
            "volatility_target": f"{volatility_target:.1f}%",
            "financial_ratios": {
                "savings_rate": f"{financial_ratios['savings_rate']:.1f}%",
                "liquidity_ratio": f"{financial_ratios['liquidity_ratio']:.1f} months",
                "debt_to_asset": f"{financial_ratios['debt_to_asset']:.1f}%"
            },
            # Add formatted versions for display
            "risk_capacity_display": f"{risk_capacity['level']} - {risk_capacity['description']}",
            "risk_tolerance_display": f"{risk_tolerance['level']} - {risk_tolerance['description']}",
            "risk_requirement_display": f"{risk_requirement['level']} - {risk_requirement['description']}",
            # Add sector and region data for equity selection agent
            "equity_selection_params": {
                "sectors": liquidity_constraints.get("sector_preferences", []) if isinstance(liquidity_constraints, dict) else [],
                "regions": liquidity_constraints.get("region_preferences", []) if isinstance(liquidity_constraints, dict) else [],
                "volatility_target": volatility_target,
                "risk_score": risk_score,
                "liquidity_score": liquidity_constraints.get("liquidity_score", 0) if isinstance(liquidity_constraints, dict) else 0,
                "age_factor": liquidity_constraints.get("age_factor", 35) if isinstance(liquidity_constraints, dict) else 35,
                "dependent_factor": liquidity_constraints.get("dependent_factor", 0) if isinstance(liquidity_constraints, dict) else 0
            }
        }
    




    