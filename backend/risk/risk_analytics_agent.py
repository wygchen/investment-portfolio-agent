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
from ..utils.financial_ratios import FinancialRatioEngine


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
        assessment = context.user_assessment
        
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
    
    def _calculate_financial_ratios(self, assessment: Dict[str, Any]) -> Dict[str, float]:
        """Calculate key financial ratios from assessment data."""
        income = assessment.get('income', 0)
        net_worth = assessment.get('net_worth', 0)
        monthly_contribution = assessment.get('monthly_contribution', 0)
        
        # Estimate monthly expenses (simplified)
        estimated_monthly_expenses = max(3000, income * 0.06)  # Assume 6% of annual income per month
        
        # Calculate ratios
        savings_rate = (monthly_contribution * 12 / max(income, 1)) * 100 if income > 0 else 0
        liquidity_ratio = net_worth / (estimated_monthly_expenses * 6) if estimated_monthly_expenses > 0 else 0
        
        # Estimate debt (simplified - assume some debt based on age and income)
        age = assessment.get('age', 35)
        estimated_debt = max(0, income * 0.3 - (age - 25) * 1000) if age > 25 else income * 0.4
        debt_to_asset = (estimated_debt / max(net_worth + estimated_debt, 1)) * 100
        
        return {
            "savings_rate": min(50, max(0, savings_rate)),
            "liquidity_ratio": min(24, max(0.5, liquidity_ratio)),
            "debt_to_asset": min(80, max(0, debt_to_asset))
        }
    
    def _assess_risk_capacity(self, assessment: Dict[str, Any], ratios: Dict[str, float], 
                            ratio_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Assess objective financial risk capacity."""
        income = assessment.get('income', 0)
        net_worth = assessment.get('net_worth', 0)
        age = assessment.get('age', 35)
        dependents = assessment.get('dependents', 0)
        
        # Use enhanced ratio analysis if available
        if ratio_results and "financial_stability_score" in ratio_results:
            # Use the comprehensive financial stability score as base
            base_score = ratio_results["financial_stability_score"].value
            capacity_score = base_score
        else:
            # Fallback to original calculation
            income_score = min(40, (income / 100000) * 20)  # Up to 40 points for income
            net_worth_score = min(30, (net_worth / 500000) * 30)  # Up to 30 points for net worth
            savings_score = min(20, ratios.get('savings_rate', 0))  # Up to 20 points for savings rate
            debt_score = max(0, 10 - (ratios.get('debt_to_asset', 50) / 10))  # Up to 10 points (less debt = higher score)
            
            capacity_score = income_score + net_worth_score + savings_score + debt_score
        
        # Adjust for dependents and age
        dependent_penalty = dependents * 5
        age_adjustment = max(-10, min(10, (65 - age) / 5))  # Younger = higher capacity
        
        final_score = max(0, min(100, capacity_score - dependent_penalty + age_adjustment))
        
        # Categorize
        if final_score >= 70:
            level = "high"
            description = "Strong financial foundation with substantial ability to absorb losses"
        elif final_score >= 40:
            level = "medium"
            description = "Moderate financial capacity with some ability to handle volatility"
        else:
            level = "low"
            description = "Limited financial capacity requiring conservative approach"
        
        return {
            "level": level,
            "score": final_score,
            "description": description,
            "factors": {
                "income_contribution": income_score,
                "net_worth_contribution": net_worth_score,
                "savings_contribution": savings_score,
                "debt_impact": debt_score
            }
        }
    
    def _assess_risk_tolerance(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Assess psychological risk tolerance."""
        risk_tolerance = assessment.get('risk_tolerance', 5)
        market_reaction = assessment.get('market_reaction', 'hold_course')
        investment_style = assessment.get('investment_style', 'balanced')
        previous_experience = assessment.get('previous_experience', [])
        
        # Base score from stated risk tolerance
        base_score = risk_tolerance * 10
        
        # Adjust based on market reaction
        reaction_adjustments = {
            'buy_more': 15,
            'hold_course': 0,
            'sell_some': -10,
            'sell_all': -20
        }
        base_score += reaction_adjustments.get(market_reaction, 0)
        
        # Adjust based on investment style
        style_adjustments = {
            'aggressive': 10,
            'growth': 5,
            'balanced': 0,
            'conservative': -10,
            'income': -15
        }
        base_score += style_adjustments.get(investment_style, 0)
        
        # Adjust based on experience
        experience_bonus = min(15, len(previous_experience) * 3)
        base_score += experience_bonus
        
        final_score = max(0, min(100, base_score))
        
        # Categorize
        if final_score >= 70:
            level = "high"
            description = "Comfortable with significant market volatility and potential losses"
        elif final_score >= 40:
            level = "medium"
            description = "Moderate comfort with market fluctuations and temporary losses"
        else:
            level = "low"
            description = "Prefers stability and capital preservation over growth potential"
        
        return {
            "level": level,
            "score": final_score,
            "description": description,
            "stated_tolerance": risk_tolerance,
            "behavioral_indicators": {
                "market_reaction": market_reaction,
                "investment_style": investment_style,
                "experience_level": len(previous_experience)
            }
        }
    
    def _assess_risk_requirement(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Assess required risk level to achieve financial goals."""
        current_age = assessment.get('age', 35)
        time_horizon = assessment.get('time_horizon', 10)
        target_amount = assessment.get('target_amount', 500000)
        monthly_contribution = assessment.get('monthly_contribution', 1000)
        net_worth = assessment.get('net_worth', 100000)
        
        # Calculate required return to reach goal
        total_contributions = monthly_contribution * 12 * time_horizon
        starting_value = net_worth
        future_value_needed = target_amount
        
        # Simple future value calculation to determine required return
        if total_contributions > 0 and time_horizon > 0:
            # Using PMT formula approximation
            required_annual_return = self._calculate_required_return(
                starting_value, monthly_contribution * 12, time_horizon, future_value_needed
            )
        else:
            required_annual_return = 0.07  # Default 7% assumption
        
        # Map required return to risk requirement
        if required_annual_return >= 0.12:  # 12%+ return needed
            level = "high"
            description = "Aggressive growth required to achieve financial goals within timeframe"
            risk_score = 80
        elif required_annual_return >= 0.08:  # 8-12% return needed
            level = "medium"
            description = "Moderate growth strategy needed to reach financial objectives"
            risk_score = 50
        else:  # <8% return needed
            level = "low"
            description = "Conservative approach sufficient to achieve financial goals"
            risk_score = 25
        
        return {
            "level": level,
            "score": risk_score,
            "description": description,
            "required_return": required_annual_return,
            "goal_analysis": {
                "target_amount": target_amount,
                "time_horizon": time_horizon,
                "monthly_contribution": monthly_contribution,
                "starting_value": starting_value
            }
        }
    
    def _calculate_required_return(self, pv: float, pmt: float, n: float, fv: float) -> float:
        """Calculate required annual return using iterative approximation."""
        if n <= 0 or fv <= 0:
            return 0.07
        
        # Simple approximation for required return
        total_invested = pv + (pmt * n)
        if total_invested <= 0:
            return 0.07
        
        required_growth = fv / total_invested
        annual_return = (required_growth ** (1/n)) - 1
        
        return max(0.02, min(0.20, annual_return))  # Cap between 2% and 20%
    
    def _calculate_enhanced_risk_score(self, assessment: Dict[str, Any], ratios: Dict[str, float], 
                                     ratio_summary: Dict[str, Any]) -> int:
        """Calculate enhanced risk score using comprehensive ratio analysis."""
        
        # Use the overall financial health score as a major component
        financial_health_score = ratio_summary.get("overall_score", 50)
        
        # Original risk score calculation
        original_score = self._calculate_risk_score(assessment, ratios)
        
        # Combine scores with weighting
        # 60% from comprehensive analysis, 40% from original methodology
        enhanced_score = (financial_health_score * 0.6) + (original_score * 0.4)
        
        return int(max(1, min(100, enhanced_score)))
    
    def _calculate_risk_score(self, assessment: Dict[str, Any], ratios: Dict[str, float]) -> int:
        """Calculate overall quantitative risk score (1-100)."""
        age = assessment.get('age', 35)
        time_horizon = assessment.get('time_horizon', 10)
        risk_tolerance = assessment.get('risk_tolerance', 5)
        
        # Age factor (younger = higher risk capacity)
        age_score = max(0, min(100, 100 - (age - 20) * 1.5))
        
        # Time horizon factor
        horizon_score = min(100, time_horizon * 4)
        
        # Risk tolerance factor
        tolerance_score = risk_tolerance * 10
        
        # Financial capacity factor (based on ratios)
        capacity_score = (
            ratios['savings_rate'] * 1.5 +
            min(50, ratios['liquidity_ratio'] * 10) +
            max(0, 50 - ratios['debt_to_asset'])
        )
        
        # Weighted combination
        weights = self.risk_score_weights
        final_score = (
            age_score * weights['age_factor'] +
            horizon_score * weights['time_horizon_factor'] +
            tolerance_score * weights['risk_tolerance_factor'] +
            capacity_score * weights['financial_capacity_factor']
        )
        
        return int(max(1, min(100, final_score)))
    
    def _map_risk_to_volatility(self, risk_score: int) -> float:
        """Map risk score to expected portfolio volatility."""
        for (min_score, max_score), volatility in self.volatility_mapping.items():
            if min_score <= risk_score <= max_score:
                return volatility
        
        # Default fallback
        return 12.0
    
    def _analyze_time_horizon_bands(self, assessment: Dict[str, Any]) -> Dict[str, str]:
        """Analyze and allocate time horizon bands."""
        time_horizon = assessment.get('time_horizon', 10)
        age = assessment.get('age', 35)
        
        if time_horizon <= 3:
            return {
                "short_term": "70%",
                "medium_term": "25%", 
                "long_term": "5%"
            }
        elif time_horizon <= 10:
            return {
                "short_term": "20%",
                "medium_term": "60%",
                "long_term": "20%"
            }
        else:
            return {
                "short_term": "10%",
                "medium_term": "30%",
                "long_term": "60%"
            }
    
    def _assess_liquidity_constraints(self, assessment: Dict[str, Any], ratios: Dict[str, float]) -> Dict[str, Any]:
        """Assess liquidity needs and constraints with sector and region preferences."""
        dependents = assessment.get('dependents', 0)
        age = assessment.get('age', 35)
        liquidity_ratio = ratios['liquidity_ratio']
        
        # Extract sector and region preferences from assessment
        sector_preferences = assessment.get('sector_preferences', [])
        region_preferences = assessment.get('region_preferences', [])
        
        constraints = []
        
        if liquidity_ratio < 3:
            constraints.append("Maintain emergency fund of 6 months expenses")
        
        if dependents > 0:
            constraints.append(f"Consider education funding for {dependents} dependent(s)")
        
        if age > 50:
            constraints.append("Increase liquidity allocation approaching retirement")
        
        if not constraints:
            constraints.append("Standard liquidity needs - maintain 3-6 months emergency fund")
        
        # Return structured data including sector and region for equity selection
        return {
            "constraints_text": "; ".join(constraints),
            "sector_preferences": sector_preferences,
            "region_preferences": region_preferences,
            "liquidity_score": liquidity_ratio,
            "age_factor": age,
            "dependent_factor": dependents
        }
    
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
        """Create structured risk blueprint JSON with sector and region data for equity selection."""
        
        # Determine overall risk level
        risk_levels = [risk_capacity['level'], risk_tolerance['level'], risk_requirement['level']]
        risk_level_priority = {'low': 0, 'medium': 1, 'high': 2}
        
        # Use the most conservative (lowest) risk level for safety
        overall_risk_level = min(risk_levels, key=lambda x: risk_level_priority[x])
        
        return {
            "risk_capacity": f"{risk_capacity['level']} - {risk_capacity['description']}",
            "risk_tolerance": f"{risk_tolerance['level']} - {risk_tolerance['description']}",
            "risk_requirement": f"{risk_requirement['level']} - {risk_requirement['description']}",
            "liquidity_constraints": liquidity_constraints.get("constraints_text", "Standard liquidity needs"),
            "time_horizon_bands": time_horizon_bands,
            "risk_level_summary": overall_risk_level,
            "risk_score": str(risk_score),
            "volatility_target": f"{volatility_target:.1f}%",
            "financial_ratios": {
                "savings_rate": f"{financial_ratios['savings_rate']:.1f}%",
                "liquidity_ratio": f"{financial_ratios['liquidity_ratio']:.1f} months",
                "debt_to_asset": f"{financial_ratios['debt_to_asset']:.1f}%"
            },
            # Add sector and region data for equity selection agent
            "equity_selection_params": {
                "sectors": liquidity_constraints.get("sector_preferences", []),
                "regions": liquidity_constraints.get("region_preferences", []),
                "volatility_target": volatility_target,
                "risk_score": risk_score,
                "liquidity_score": liquidity_constraints.get("liquidity_score", 0),
                "age_factor": liquidity_constraints.get("age_factor", 35),
                "dependent_factor": liquidity_constraints.get("dependent_factor", 0)
            }
        }
    
    def _validate_input(self, context: AgentContext) -> Dict[str, Any]:
        """Validate input for risk analytics agent including sector and region preferences."""
        base_validation = super()._validate_input(context)
        if not base_validation["valid"]:
            return base_validation
        
        assessment = context.user_assessment
        required_fields = ['age', 'income', 'net_worth', 'risk_tolerance', 'time_horizon']
        
        for field in required_fields:
            if field not in assessment or assessment[field] is None:
                return {"valid": False, "error": f"Missing required field: {field}"}
        
        # Validate field ranges
        if not (18 <= assessment['age'] <= 100):
            return {"valid": False, "error": "Age must be between 18 and 100"}
        
        if not (1 <= assessment['risk_tolerance'] <= 10):
            return {"valid": False, "error": "Risk tolerance must be between 1 and 10"}
        
        if assessment['time_horizon'] < 1:
            return {"valid": False, "error": "Time horizon must be at least 1 year"}
        
        # Validate sector preferences if provided
        sector_preferences = assessment.get('sector_preferences', [])
        if sector_preferences:
            valid_sectors = [
                'Technology', 'Healthcare', 'Financial', 'Consumer Discretionary', 
                'Consumer Staples', 'Energy', 'Industrials', 'Materials', 
                'Real Estate', 'Utilities', 'Communication Services'
            ]
            invalid_sectors = [s for s in sector_preferences if s not in valid_sectors]
            if invalid_sectors:
                return {"valid": False, "error": f"Invalid sectors: {invalid_sectors}. Valid sectors: {valid_sectors}"}
        
        # Validate region preferences if provided
        region_preferences = assessment.get('region_preferences', [])
        if region_preferences:
            valid_regions = ['US', 'HK', 'EU', 'JP', 'CA', 'AU', 'UK', 'CN']
            invalid_regions = [r for r in region_preferences if r not in valid_regions]
            if invalid_regions:
                return {"valid": False, "error": f"Invalid regions: {invalid_regions}. Valid regions: {valid_regions}"}
        
        return {"valid": True} 10):
            return {"valid": False, "error": "Risk tolerance must be between 1 and 10"}
        
        if assessment['time_horizon'] < 1:
            return {"valid": False, "error": "Time horizon must be at least 1 year"}
        
        return {"valid": True}