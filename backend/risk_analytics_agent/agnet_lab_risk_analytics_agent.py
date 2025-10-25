import asyncio
import logging
from typing import Dict, Any
from langchain_ibm import ChatWatsonx  # Adjust import based on your setup
from .base_agent import AgentContext, BaseAgent  # Adjust import path
from .utils.financial_ratios import FinancialRatioEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('risk_analytics_agent.log')
    ]
)
logger = logging.getLogger(__name__)

logger.info("RiskAnalyticsAgent module loaded")


class RiskAnalyticsAgent(BaseAgent):
    def __init__(self, llm: ChatWatsonx):
        super().__init__(
            name="RiskAnalyticsAgent",
            llm=llm,
            system_prompt="You are the Risk Analysis Agent, a specialized AI financial advisor...",
            max_retries=3
        )

         # Initialize financial ratio engine
        self.ratio_engine = FinancialRatioEngine()
        self.llm = ChatWatsonx()
        

    async def _execute_agent_logic(self, context: AgentContext) -> Dict[str, Any]:
        """
        Execute comprehensive risk analysis logic using deployed LLM tools.

        Args:
            context: Agent context with user assessment data

        Returns:
            Dictionary with risk analysis results
        """
        logger.info("Starting risk analysis execution")
        
        # Normalize assessment data
        logger.info("Normalizing user assessment data")
        assessment = self._normalize_user_assessment(context.user_assessment)
        logger.debug("Normalized assessment: %s", assessment)

        # Step 1: Calculate financial ratios
        ratio_results = self.ratio_engine.calculate_all_ratios(assessment)

        financial_ratios = self._extract_key_ratios(ratio_results)
        ratio_summary = self.ratio_engine.generate_ratio_summary(ratio_results)


        # Step 2: Assess risk components
        logger.info("Starting risk component assessment")
        
        try:
            logger.info("Assessing risk capacity")
            risk_capacity = await self.llm.invoke_tool(
                "_assess_risk_capacity", {
                    "assessment": assessment,
                    "ratios": financial_ratios,
                    "ratio_results": ratio_results
                }
            )
            logger.debug("Risk capacity result: %s", risk_capacity)
            
            logger.info("Assessing risk tolerance")
            risk_tolerance = await self.llm.invoke_tool(
                "_assess_risk_tolerance", {"assessment": assessment}
            )
            logger.debug("Risk tolerance result: %s", risk_tolerance)
            
            logger.info("Assessing risk requirement")
            risk_requirement = await self.llm.invoke_tool(
                "_assess_risk_requirement", {"assessment": assessment}
            )
            logger.debug("Risk requirement result: %s", risk_requirement)
            
        except Exception as e:
            logger.error("Error during risk assessment: %s", str(e))
            raise

        # Step 3: Calculate enhanced risk score
        risk_score = await self.llm.invoke_tool(
            "_calculate_enhanced_risk_score", {
                "assessment": assessment,
                "ratios": financial_ratios,
                "ratio_summary": ratio_summary
            }
        )

        # Step 4: Map to volatility target
        volatility_target = await self.llm.invoke_tool(
            "_map_risk_to_volatility", {"risk_score": risk_score}
        )

        # Step 5: Analyze time horizon bands
        time_horizon_bands = await self.llm.invoke_tool(
            "_analyze_time_horizon_bands", {"assessment": assessment}
        )

        # Step 6: Assess liquidity constraints
        liquidity_constraints = await self.llm.invoke_tool(
            "_assess_liquidity_constraints", {
                "assessment": assessment,
                "ratios": financial_ratios
            }
        )

        # Step 7: Generate AI-powered analysis
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
- Savings Rate: {financial_ratios.get('savings_rate', 0):.1f}%
- Liquidity Ratio: {financial_ratios.get('liquidity_ratio', 0):.1f} months
- Debt-to-Asset Ratio: {financial_ratios.get('debt_to_asset', 0):.1f}%
- Overall Risk Score: {risk_score}/100

RISK ASSESSMENT RESULTS:
- Risk Capacity: {risk_capacity['level']} ({risk_capacity['score']}/100)
- Risk Tolerance: {risk_tolerance['level']} ({risk_tolerance['score']}/100)  
- Risk Requirement: {risk_requirement['level']} ({risk_requirement['score']}/100)

COMPREHENSIVE RATIO ANALYSIS:
{ratio_summary if ratio_summary else 'Standard ratio analysis applied'}

Please provide:
1. Executive summary of the risk profile
2. Detailed analysis of each risk component
3. Key insights and recommendations based on comprehensive financial ratios
4. Potential risk factors to monitor
5. Integration of quantitative ratio analysis with qualitative assessment

Format your response professionally with clear sections and actionable insights.
"""
        ai_analysis = await self.llm.invoke(analysis_prompt)

        # Step 8: Create structured risk blueprint (simplified, assuming LLM can't call _create_risk_blueprint directly)
        risk_blueprint = {
            "risk_capacity": risk_capacity,
            "risk_tolerance": risk_tolerance,
            "risk_requirement": risk_requirement,
            "liquidity_constraints": liquidity_constraints,
            "time_horizon_bands": time_horizon_bands,
            "risk_level_summary": min([risk_capacity['level'], risk_tolerance['level'], risk_requirement['level']],
                                   key=lambda x: {'low': 0, 'medium': 1, 'high': 2}[x]),
            "risk_score": str(risk_score),
            "volatility_target": f"{volatility_target:.1f}%",
            "financial_ratios": {
                "savings_rate": f"{financial_ratios.get('savings_rate', 0):.1f}%",
                "liquidity_ratio": f"{financial_ratios.get('liquidity_ratio', 0):.1f} months",
                "debt_to_asset": f"{financial_ratios.get('debt_to_asset', 0):.1f}%"
            }
        }

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


    def _normalize_user_assessment(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize various UserProfile shapes into the fields this agent expects."""
        normalized = dict(raw or {})
        if 'monthly_contribution' not in normalized:
            if 'savings_rate' in normalized:
                try:
                    normalized['monthly_contribution'] = float(normalized.get('savings_rate') or 0)
                except Exception:
                    normalized['monthly_contribution'] = 0.0
            else:
                normalized['monthly_contribution'] = 0.0
        normalized['income'] = float(normalized.get('income') or 0)
        if 'net_worth' not in normalized or normalized['net_worth'] is None:
            normalized['net_worth'] = 0
        if 'dependents' not in normalized or normalized['dependents'] is None:
            normalized['dependents'] = 0
        if 'target_amount' not in normalized or normalized['target_amount'] is None:
            normalized['target_amount'] = 0
        rt = normalized.get('risk_tolerance')
        if isinstance(rt, str):
            mapping = {'low': 3, 'medium': 5, 'moderate': 5, 'high': 8}
            normalized['risk_tolerance'] = mapping.get(rt.strip().lower(), 5)
        elif isinstance(rt, (int, float)):
            normalized['risk_tolerance'] = int(rt)
        else:
            normalized['risk_tolerance'] = 5
        try:
            normalized['time_horizon'] = int(normalized.get('time_horizon') or 10)
        except Exception:
            normalized['time_horizon'] = 10
        try:
            normalized['age'] = int(normalized.get('age') or 35)
        except Exception:
            normalized['age'] = 35
        return normalized