"""
Financial Ratio Calculation Engine for Risk Analytics.
Provides comprehensive financial ratio calculations with validation and documentation.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np


logger = logging.getLogger(__name__)


class RatioCategory(Enum):
    """Categories of financial ratios"""
    LIQUIDITY = "liquidity"
    SOLVENCY = "solvency"
    EFFICIENCY = "efficiency"
    PROFITABILITY = "profitability"
    RISK = "risk"


@dataclass
class RatioResult:
    """Result of a financial ratio calculation"""
    name: str
    value: float
    category: RatioCategory
    interpretation: str
    benchmark_range: Tuple[float, float]
    quality_score: int  # 1-100 scale
    warning_flags: List[str]
    calculation_method: str


@dataclass
class FinancialProfile:
    """Structured financial profile for ratio calculations"""
    # Basic financial data
    age: int
    annual_income: float
    net_worth: float
    liquid_assets: Optional[float] = None
    total_assets: Optional[float] = None
    total_debt: Optional[float] = None
    monthly_expenses: Optional[float] = None
    
    # Investment and savings data
    monthly_contribution: float = 0
    emergency_fund: Optional[float] = None
    retirement_savings: Optional[float] = None
    
    # Family and lifestyle
    dependents: int = 0
    housing_cost: Optional[float] = None
    
    # Goals and timeline
    time_horizon: int = 10
    target_amount: float = 0
    
    # Additional context
    employment_stability: str = "stable"  # stable, unstable, self_employed
    industry: Optional[str] = None


class FinancialRatioEngine:
    """
    Comprehensive financial ratio calculation engine.
    Calculates key financial health metrics with validation and interpretation.
    """
    
    def __init__(self):
        """Initialize the financial ratio engine with benchmarks and standards."""
        
        # Industry benchmarks for ratio interpretation
        self.benchmarks = {
            "savings_rate": {
                "excellent": (20, 100),
                "good": (15, 20),
                "fair": (10, 15),
                "poor": (0, 10)
            },
            "liquidity_ratio": {
                "excellent": (6, 12),
                "good": (3, 6),
                "fair": (1, 3),
                "poor": (0, 1)
            },
            "debt_to_income": {
                "excellent": (0, 20),
                "good": (20, 36),
                "fair": (36, 50),
                "poor": (50, 100)
            },
            "debt_to_asset": {
                "excellent": (0, 20),
                "good": (20, 40),
                "fair": (40, 60),
                "poor": (60, 100)
            },
            "net_worth_to_income": {
                "excellent": (5, 20),
                "good": (2, 5),
                "fair": (1, 2),
                "poor": (0, 1)
            }
        }
        
        logger.info("Financial Ratio Engine initialized with industry benchmarks")
    
    def calculate_all_ratios(self, assessment_data: Dict[str, Any]) -> Dict[str, RatioResult]:
        """
        Calculate all relevant financial ratios from assessment data.
        
        Args:
            assessment_data: User assessment data dictionary
            
        Returns:
            Dictionary of ratio names to RatioResult objects
        """
        # Convert assessment data to structured profile
        profile = self._create_financial_profile(assessment_data)
        
        # Validate profile data
        validation_result = self._validate_profile(profile)
        if not validation_result["valid"]:
            logger.warning(f"Profile validation issues: {validation_result['warnings']}")
        
        # Calculate individual ratios
        ratios = {}
        
        try:
            # Liquidity ratios
            ratios["savings_rate"] = self._calculate_savings_rate(profile)
            ratios["liquidity_ratio"] = self._calculate_liquidity_ratio(profile)
            ratios["emergency_fund_ratio"] = self._calculate_emergency_fund_ratio(profile)
            
            # Solvency ratios
            ratios["debt_to_income"] = self._calculate_debt_to_income_ratio(profile)
            ratios["debt_to_asset"] = self._calculate_debt_to_asset_ratio(profile)
            ratios["net_worth_to_income"] = self._calculate_net_worth_to_income_ratio(profile)
            
            # Efficiency ratios
            ratios["investment_rate"] = self._calculate_investment_rate(profile)
            ratios["expense_ratio"] = self._calculate_expense_ratio(profile)
            
            # Risk ratios
            ratios["financial_stability_score"] = self._calculate_financial_stability_score(profile)
            ratios["goal_feasibility_ratio"] = self._calculate_goal_feasibility_ratio(profile)
            
            logger.info(f"Successfully calculated {len(ratios)} financial ratios")
            
        except Exception as e:
            logger.error(f"Error calculating financial ratios: {e}")
            # Return partial results if some calculations failed
        
        return ratios
    
    def _create_financial_profile(self, assessment_data: Dict[str, Any]) -> FinancialProfile:
        """Convert assessment data to structured financial profile."""
        
        # Extract basic data
        age = assessment_data.get('age', 35)
        annual_income = assessment_data.get('income', 0)
        net_worth = assessment_data.get('net_worth', 0)
        monthly_contribution = assessment_data.get('monthly_contribution', 0)
        dependents = assessment_data.get('dependents', 0)
        time_horizon = assessment_data.get('time_horizon', 10)
        target_amount = assessment_data.get('target_amount', 0)
        
        # Estimate missing values using heuristics
        estimated_monthly_expenses = self._estimate_monthly_expenses(annual_income, dependents, age)
        estimated_liquid_assets = self._estimate_liquid_assets(net_worth, annual_income)
        estimated_total_debt = self._estimate_total_debt(annual_income, net_worth, age)
        estimated_total_assets = net_worth + estimated_total_debt
        
        return FinancialProfile(
            age=age,
            annual_income=annual_income,
            net_worth=net_worth,
            liquid_assets=estimated_liquid_assets,
            total_assets=estimated_total_assets,
            total_debt=estimated_total_debt,
            monthly_expenses=estimated_monthly_expenses,
            monthly_contribution=monthly_contribution,
            dependents=dependents,
            time_horizon=time_horizon,
            target_amount=target_amount
        )
    
    def _estimate_monthly_expenses(self, annual_income: float, dependents: int, age: int) -> float:
        """Estimate monthly expenses based on income, dependents, and age."""
        if annual_income <= 0:
            return 3000  # Minimum assumption
        
        # Base expense ratio (percentage of income)
        base_ratio = 0.70  # 70% of income for expenses
        
        # Adjust for dependents
        dependent_adjustment = dependents * 0.15  # 15% more per dependent
        
        # Adjust for age (older people might have higher healthcare costs)
        age_adjustment = max(0, (age - 50) * 0.002)  # 0.2% more per year after 50
        
        total_ratio = min(0.95, base_ratio + dependent_adjustment + age_adjustment)
        
        return (annual_income * total_ratio) / 12
    
    def _estimate_liquid_assets(self, net_worth: float, annual_income: float) -> float:
        """Estimate liquid assets as portion of net worth."""
        if net_worth <= 0:
            return max(0, annual_income * 0.1)  # 10% of income if no net worth
        
        # Assume 30-60% of net worth is liquid depending on total net worth
        if net_worth < 100000:
            liquidity_ratio = 0.6  # Higher liquidity for smaller net worth
        elif net_worth < 500000:
            liquidity_ratio = 0.4
        else:
            liquidity_ratio = 0.3  # Lower liquidity for higher net worth (more investments)
        
        return net_worth * liquidity_ratio
    
    def _estimate_total_debt(self, annual_income: float, net_worth: float, age: int) -> float:
        """Estimate total debt based on income, net worth, and age."""
        if annual_income <= 0:
            return 0
        
        # Younger people typically have more debt (student loans, mortgages)
        if age < 30:
            debt_to_income_ratio = 0.4  # 40% of income
        elif age < 45:
            debt_to_income_ratio = 0.3  # 30% of income
        else:
            debt_to_income_ratio = 0.2  # 20% of income
        
        estimated_debt = annual_income * debt_to_income_ratio
        
        # Ensure debt doesn't exceed reasonable bounds relative to net worth
        max_reasonable_debt = max(annual_income * 0.5, net_worth * 0.3)
        
        return min(estimated_debt, max_reasonable_debt)
    
    def _validate_profile(self, profile: FinancialProfile) -> Dict[str, Any]:
        """Validate financial profile data for consistency and reasonableness."""
        warnings = []
        
        # Check for negative values
        if profile.annual_income < 0:
            warnings.append("Negative annual income")
        if profile.net_worth < -profile.annual_income * 2:
            warnings.append("Extremely negative net worth")
        
        # Check for unrealistic ratios
        if profile.monthly_contribution > profile.annual_income / 12 * 0.8:
            warnings.append("Monthly contribution exceeds 80% of monthly income")
        
        if profile.total_debt and profile.total_debt > profile.annual_income * 5:
            warnings.append("Total debt exceeds 5x annual income")
        
        # Check age-related consistency
        if profile.age < 18 or profile.age > 100:
            warnings.append("Age outside reasonable range")
        
        return {
            "valid": len(warnings) == 0,
            "warnings": warnings
        }
    
    def _calculate_savings_rate(self, profile: FinancialProfile) -> RatioResult:
        """Calculate savings rate as percentage of income."""
        if profile.annual_income <= 0:
            return self._create_error_ratio("savings_rate", "No income data")
        
        annual_savings = profile.monthly_contribution * 12
        savings_rate = (annual_savings / profile.annual_income) * 100
        
        # Interpretation
        interpretation, quality_score = self._interpret_ratio("savings_rate", savings_rate)
        
        warnings = []
        if savings_rate > 50:
            warnings.append("Extremely high savings rate - verify sustainability")
        elif savings_rate < 5:
            warnings.append("Very low savings rate - consider increasing contributions")
        
        return RatioResult(
            name="Savings Rate",
            value=savings_rate,
            category=RatioCategory.EFFICIENCY,
            interpretation=interpretation,
            benchmark_range=self.benchmarks["savings_rate"]["good"],
            quality_score=quality_score,
            warning_flags=warnings,
            calculation_method="(Monthly Contribution × 12) / Annual Income × 100"
        )
    
    def _calculate_liquidity_ratio(self, profile: FinancialProfile) -> RatioResult:
        """Calculate liquidity ratio in months of expenses covered."""
        if not profile.monthly_expenses or profile.monthly_expenses <= 0:
            return self._create_error_ratio("liquidity_ratio", "No expense data")
        
        liquid_assets = profile.liquid_assets or 0
        liquidity_months = liquid_assets / profile.monthly_expenses
        
        interpretation, quality_score = self._interpret_ratio("liquidity_ratio", liquidity_months)
        
        warnings = []
        if liquidity_months < 3:
            warnings.append("Insufficient emergency fund - aim for 3-6 months expenses")
        elif liquidity_months > 12:
            warnings.append("Excess liquidity - consider investing surplus funds")
        
        return RatioResult(
            name="Liquidity Ratio",
            value=liquidity_months,
            category=RatioCategory.LIQUIDITY,
            interpretation=interpretation,
            benchmark_range=self.benchmarks["liquidity_ratio"]["good"],
            quality_score=quality_score,
            warning_flags=warnings,
            calculation_method="Liquid Assets / Monthly Expenses"
        )
    
    def _calculate_emergency_fund_ratio(self, profile: FinancialProfile) -> RatioResult:
        """Calculate emergency fund adequacy ratio."""
        if not profile.monthly_expenses or profile.monthly_expenses <= 0:
            return self._create_error_ratio("emergency_fund_ratio", "No expense data")
        
        # Use liquid assets as proxy for emergency fund
        emergency_fund = profile.liquid_assets or 0
        target_emergency_fund = profile.monthly_expenses * 6  # 6 months target
        
        adequacy_ratio = (emergency_fund / target_emergency_fund) * 100
        
        if adequacy_ratio >= 100:
            interpretation = "Adequate emergency fund"
            quality_score = 90
        elif adequacy_ratio >= 75:
            interpretation = "Nearly adequate emergency fund"
            quality_score = 75
        elif adequacy_ratio >= 50:
            interpretation = "Partial emergency fund"
            quality_score = 50
        else:
            interpretation = "Insufficient emergency fund"
            quality_score = 25
        
        warnings = []
        if adequacy_ratio < 50:
            warnings.append("Priority: Build emergency fund to 6 months expenses")
        
        return RatioResult(
            name="Emergency Fund Adequacy",
            value=adequacy_ratio,
            category=RatioCategory.LIQUIDITY,
            interpretation=interpretation,
            benchmark_range=(75, 125),
            quality_score=quality_score,
            warning_flags=warnings,
            calculation_method="Emergency Fund / (Monthly Expenses × 6) × 100"
        )
    
    def _calculate_debt_to_income_ratio(self, profile: FinancialProfile) -> RatioResult:
        """Calculate debt-to-income ratio."""
        if profile.annual_income <= 0:
            return self._create_error_ratio("debt_to_income", "No income data")
        
        total_debt = profile.total_debt or 0
        debt_to_income = (total_debt / profile.annual_income) * 100
        
        interpretation, quality_score = self._interpret_ratio("debt_to_income", debt_to_income)
        
        warnings = []
        if debt_to_income > 50:
            warnings.append("High debt burden - consider debt reduction strategy")
        elif debt_to_income > 36:
            warnings.append("Moderate debt burden - monitor carefully")
        
        return RatioResult(
            name="Debt-to-Income Ratio",
            value=debt_to_income,
            category=RatioCategory.SOLVENCY,
            interpretation=interpretation,
            benchmark_range=self.benchmarks["debt_to_income"]["good"],
            quality_score=quality_score,
            warning_flags=warnings,
            calculation_method="Total Debt / Annual Income × 100"
        )
    
    def _calculate_debt_to_asset_ratio(self, profile: FinancialProfile) -> RatioResult:
        """Calculate debt-to-asset ratio."""
        total_assets = profile.total_assets or profile.net_worth
        if total_assets <= 0:
            return self._create_error_ratio("debt_to_asset", "No asset data")
        
        total_debt = profile.total_debt or 0
        debt_to_asset = (total_debt / total_assets) * 100
        
        interpretation, quality_score = self._interpret_ratio("debt_to_asset", debt_to_asset)
        
        warnings = []
        if debt_to_asset > 60:
            warnings.append("High leverage - significant financial risk")
        elif debt_to_asset > 40:
            warnings.append("Moderate leverage - monitor debt levels")
        
        return RatioResult(
            name="Debt-to-Asset Ratio",
            value=debt_to_asset,
            category=RatioCategory.SOLVENCY,
            interpretation=interpretation,
            benchmark_range=self.benchmarks["debt_to_asset"]["good"],
            quality_score=quality_score,
            warning_flags=warnings,
            calculation_method="Total Debt / Total Assets × 100"
        )
    
    def _calculate_net_worth_to_income_ratio(self, profile: FinancialProfile) -> RatioResult:
        """Calculate net worth to income ratio."""
        if profile.annual_income <= 0:
            return self._create_error_ratio("net_worth_to_income", "No income data")
        
        net_worth_multiple = profile.net_worth / profile.annual_income
        
        interpretation, quality_score = self._interpret_ratio("net_worth_to_income", net_worth_multiple)
        
        warnings = []
        if net_worth_multiple < 0:
            warnings.append("Negative net worth - focus on debt reduction")
        elif net_worth_multiple < 1:
            warnings.append("Low net worth accumulation - increase savings")
        
        return RatioResult(
            name="Net Worth to Income Multiple",
            value=net_worth_multiple,
            category=RatioCategory.PROFITABILITY,
            interpretation=interpretation,
            benchmark_range=self.benchmarks["net_worth_to_income"]["good"],
            quality_score=quality_score,
            warning_flags=warnings,
            calculation_method="Net Worth / Annual Income"
        )
    
    def _calculate_investment_rate(self, profile: FinancialProfile) -> RatioResult:
        """Calculate investment rate as percentage of income."""
        if profile.annual_income <= 0:
            return self._create_error_ratio("investment_rate", "No income data")
        
        annual_investment = profile.monthly_contribution * 12
        investment_rate = (annual_investment / profile.annual_income) * 100
        
        # Age-adjusted benchmarks
        age_factor = min(65, profile.age)
        recommended_rate = max(10, 100 - age_factor)  # Rule of thumb: 100 - age
        
        if investment_rate >= recommended_rate:
            interpretation = f"Excellent investment rate (target: {recommended_rate:.0f}%)"
            quality_score = 90
        elif investment_rate >= recommended_rate * 0.75:
            interpretation = f"Good investment rate (target: {recommended_rate:.0f}%)"
            quality_score = 75
        elif investment_rate >= recommended_rate * 0.5:
            interpretation = f"Moderate investment rate (target: {recommended_rate:.0f}%)"
            quality_score = 50
        else:
            interpretation = f"Low investment rate (target: {recommended_rate:.0f}%)"
            quality_score = 25
        
        warnings = []
        if investment_rate < 10:
            warnings.append("Consider increasing investment contributions")
        
        return RatioResult(
            name="Investment Rate",
            value=investment_rate,
            category=RatioCategory.EFFICIENCY,
            interpretation=interpretation,
            benchmark_range=(recommended_rate * 0.75, recommended_rate * 1.25),
            quality_score=quality_score,
            warning_flags=warnings,
            calculation_method="Annual Investment / Annual Income × 100"
        )
    
    def _calculate_expense_ratio(self, profile: FinancialProfile) -> RatioResult:
        """Calculate expense ratio as percentage of income."""
        if profile.annual_income <= 0 or not profile.monthly_expenses:
            return self._create_error_ratio("expense_ratio", "Insufficient data")
        
        annual_expenses = profile.monthly_expenses * 12
        expense_ratio = (annual_expenses / profile.annual_income) * 100
        
        if expense_ratio <= 60:
            interpretation = "Excellent expense control"
            quality_score = 90
        elif expense_ratio <= 75:
            interpretation = "Good expense management"
            quality_score = 75
        elif expense_ratio <= 90:
            interpretation = "Moderate expense levels"
            quality_score = 50
        else:
            interpretation = "High expense ratio"
            quality_score = 25
        
        warnings = []
        if expense_ratio > 90:
            warnings.append("High expenses limit savings capacity")
        
        return RatioResult(
            name="Expense Ratio",
            value=expense_ratio,
            category=RatioCategory.EFFICIENCY,
            interpretation=interpretation,
            benchmark_range=(60, 75),
            quality_score=quality_score,
            warning_flags=warnings,
            calculation_method="Annual Expenses / Annual Income × 100"
        )
    
    def _calculate_financial_stability_score(self, profile: FinancialProfile) -> RatioResult:
        """Calculate overall financial stability score."""
        
        # Component scores (0-100 each)
        scores = []
        
        # Income stability (based on age and employment)
        if profile.age >= 30:
            income_score = 80
        elif profile.age >= 25:
            income_score = 60
        else:
            income_score = 40
        scores.append(income_score)
        
        # Debt burden score
        if profile.total_debt and profile.annual_income > 0:
            debt_ratio = (profile.total_debt / profile.annual_income) * 100
            debt_score = max(0, 100 - debt_ratio * 2)  # Penalty for high debt
        else:
            debt_score = 80
        scores.append(debt_score)
        
        # Liquidity score
        if profile.liquid_assets and profile.monthly_expenses:
            liquidity_months = profile.liquid_assets / profile.monthly_expenses
            liquidity_score = min(100, liquidity_months * 20)  # 20 points per month
        else:
            liquidity_score = 30
        scores.append(liquidity_score)
        
        # Savings score
        if profile.annual_income > 0:
            savings_rate = (profile.monthly_contribution * 12 / profile.annual_income) * 100
            savings_score = min(100, savings_rate * 5)  # 5 points per percent
        else:
            savings_score = 0
        scores.append(savings_score)
        
        # Calculate weighted average
        stability_score = np.mean(scores)
        
        if stability_score >= 80:
            interpretation = "Excellent financial stability"
            quality_score = 90
        elif stability_score >= 60:
            interpretation = "Good financial stability"
            quality_score = 75
        elif stability_score >= 40:
            interpretation = "Moderate financial stability"
            quality_score = 50
        else:
            interpretation = "Low financial stability"
            quality_score = 25
        
        warnings = []
        if stability_score < 50:
            warnings.append("Focus on building financial foundation")
        
        return RatioResult(
            name="Financial Stability Score",
            value=stability_score,
            category=RatioCategory.RISK,
            interpretation=interpretation,
            benchmark_range=(60, 80),
            quality_score=quality_score,
            warning_flags=warnings,
            calculation_method="Weighted average of income, debt, liquidity, and savings scores"
        )
    
    def _calculate_goal_feasibility_ratio(self, profile: FinancialProfile) -> RatioResult:
        """Calculate feasibility of achieving financial goals."""
        
        if profile.target_amount <= 0 or profile.time_horizon <= 0:
            return self._create_error_ratio("goal_feasibility", "No goal data")
        
        # Calculate required monthly savings to reach goal
        current_value = max(0, profile.net_worth)
        future_value_needed = profile.target_amount
        months = profile.time_horizon * 12
        
        # Assume 7% annual return (conservative)
        monthly_return = 0.07 / 12
        
        # Calculate required monthly payment using PMT formula
        if monthly_return > 0:
            # Future value of current investments
            fv_current = current_value * ((1 + monthly_return) ** months)
            # Remaining amount needed from contributions
            remaining_needed = future_value_needed - fv_current
            
            if remaining_needed > 0:
                # Required monthly contribution
                required_monthly = remaining_needed / (((1 + monthly_return) ** months - 1) / monthly_return)
            else:
                required_monthly = 0
        else:
            required_monthly = (future_value_needed - current_value) / months
        
        # Compare with current contribution
        current_monthly = profile.monthly_contribution
        feasibility_ratio = (current_monthly / max(required_monthly, 1)) * 100
        
        if feasibility_ratio >= 100:
            interpretation = "Goal is achievable with current savings"
            quality_score = 90
        elif feasibility_ratio >= 75:
            interpretation = "Goal is likely achievable with minor adjustments"
            quality_score = 75
        elif feasibility_ratio >= 50:
            interpretation = "Goal requires significant increase in savings"
            quality_score = 50
        else:
            interpretation = "Goal may not be achievable without major changes"
            quality_score = 25
        
        warnings = []
        if feasibility_ratio < 75:
            warnings.append(f"Consider increasing monthly contribution to ${required_monthly:.0f}")
        
        return RatioResult(
            name="Goal Feasibility Ratio",
            value=feasibility_ratio,
            category=RatioCategory.RISK,
            interpretation=interpretation,
            benchmark_range=(75, 125),
            quality_score=quality_score,
            warning_flags=warnings,
            calculation_method="Current Monthly Savings / Required Monthly Savings × 100"
        )
    
    def _interpret_ratio(self, ratio_name: str, value: float) -> Tuple[str, int]:
        """Interpret ratio value against benchmarks."""
        if ratio_name not in self.benchmarks:
            return "No benchmark available", 50
        
        benchmarks = self.benchmarks[ratio_name]
        
        for quality, (min_val, max_val) in benchmarks.items():
            if min_val <= value <= max_val:
                quality_scores = {
                    "excellent": 90,
                    "good": 75,
                    "fair": 50,
                    "poor": 25
                }
                return f"{quality.title()} range", quality_scores[quality]
        
        # Value outside all ranges
        if value > max(range_vals[1] for range_vals in benchmarks.values()):
            return "Above excellent range", 95
        else:
            return "Below poor range", 10
    
    def _create_error_ratio(self, ratio_name: str, error_msg: str) -> RatioResult:
        """Create error ratio result for failed calculations."""
        return RatioResult(
            name=ratio_name.replace("_", " ").title(),
            value=0.0,
            category=RatioCategory.RISK,
            interpretation=f"Calculation error: {error_msg}",
            benchmark_range=(0, 0),
            quality_score=0,
            warning_flags=[error_msg],
            calculation_method="Error in calculation"
        )
    
    def generate_ratio_summary(self, ratios: Dict[str, RatioResult]) -> Dict[str, Any]:
        """Generate summary of all calculated ratios."""
        
        # Calculate overall financial health score
        valid_ratios = [r for r in ratios.values() if r.quality_score > 0]
        if valid_ratios:
            overall_score = np.mean([r.quality_score for r in valid_ratios])
        else:
            overall_score = 0
        
        # Categorize ratios
        categorized_ratios = {}
        for category in RatioCategory:
            categorized_ratios[category.value] = [
                r for r in ratios.values() if r.category == category
            ]
        
        # Collect all warnings
        all_warnings = []
        for ratio in ratios.values():
            all_warnings.extend(ratio.warning_flags)
        
        # Determine overall financial health
        if overall_score >= 80:
            health_status = "Excellent"
        elif overall_score >= 60:
            health_status = "Good"
        elif overall_score >= 40:
            health_status = "Fair"
        else:
            health_status = "Needs Improvement"
        
        return {
            "overall_score": overall_score,
            "health_status": health_status,
            "total_ratios_calculated": len(ratios),
            "valid_ratios": len(valid_ratios),
            "categorized_ratios": categorized_ratios,
            "key_warnings": list(set(all_warnings)),  # Remove duplicates
            "recommendations": self._generate_recommendations(ratios, overall_score)
        }
    
    def _generate_recommendations(self, ratios: Dict[str, RatioResult], overall_score: float) -> List[str]:
        """Generate actionable recommendations based on ratio analysis."""
        recommendations = []
        
        # Check savings rate
        if "savings_rate" in ratios and ratios["savings_rate"].quality_score < 50:
            recommendations.append("Increase monthly savings contributions to improve financial security")
        
        # Check liquidity
        if "liquidity_ratio" in ratios and ratios["liquidity_ratio"].quality_score < 50:
            recommendations.append("Build emergency fund to cover 3-6 months of expenses")
        
        # Check debt levels
        if "debt_to_income" in ratios and ratios["debt_to_income"].quality_score < 50:
            recommendations.append("Focus on debt reduction to improve financial flexibility")
        
        # Check goal feasibility
        if "goal_feasibility_ratio" in ratios and ratios["goal_feasibility_ratio"].quality_score < 75:
            recommendations.append("Adjust financial goals or increase savings rate to improve achievability")
        
        # Overall recommendations
        if overall_score < 40:
            recommendations.append("Consider consulting with a financial advisor for comprehensive planning")
        elif overall_score < 60:
            recommendations.append("Focus on strengthening financial foundation before aggressive investing")
        
        return recommendations[:5]  # Limit to top 5 recommendations