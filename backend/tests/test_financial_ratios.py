"""
Unit tests for Financial Ratio Calculation Engine.
Tests all ratio calculations, validation, and edge cases.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.financial_ratios import FinancialRatioEngine, FinancialProfile, RatioCategory


class TestFinancialRatioEngine:
    """Test suite for Financial Ratio Engine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FinancialRatioEngine()
        
        # Standard test profile
        self.standard_assessment = {
            "age": 35,
            "income": 75000,
            "net_worth": 150000,
            "monthly_contribution": 1000,
            "dependents": 1,
            "time_horizon": 25,
            "target_amount": 1000000
        }
        
        # High-income profile
        self.high_income_assessment = {
            "age": 45,
            "income": 150000,
            "net_worth": 500000,
            "monthly_contribution": 3000,
            "dependents": 2,
            "time_horizon": 20,
            "target_amount": 2000000
        }
        
        # Low-income profile
        self.low_income_assessment = {
            "age": 28,
            "income": 35000,
            "net_worth": 15000,
            "monthly_contribution": 200,
            "dependents": 0,
            "time_horizon": 35,
            "target_amount": 500000
        }
    
    def test_engine_initialization(self):
        """Test engine initializes with proper benchmarks"""
        assert self.engine is not None
        assert "savings_rate" in self.engine.benchmarks
        assert "liquidity_ratio" in self.engine.benchmarks
        assert "debt_to_income" in self.engine.benchmarks
    
    def test_calculate_all_ratios_standard_profile(self):
        """Test ratio calculation for standard profile"""
        ratios = self.engine.calculate_all_ratios(self.standard_assessment)
        
        # Check that key ratios are calculated
        expected_ratios = [
            "savings_rate", "liquidity_ratio", "debt_to_income", 
            "debt_to_asset", "net_worth_to_income", "investment_rate"
        ]
        
        for ratio_name in expected_ratios:
            assert ratio_name in ratios
            assert ratios[ratio_name].value >= 0
            assert ratios[ratio_name].quality_score >= 0
    
    def test_savings_rate_calculation(self):
        """Test savings rate calculation accuracy"""
        ratios = self.engine.calculate_all_ratios(self.standard_assessment)
        savings_rate = ratios["savings_rate"]
        
        # Expected: (1000 * 12) / 75000 * 100 = 16%
        expected_rate = (1000 * 12 / 75000) * 100
        assert abs(savings_rate.value - expected_rate) < 0.1
        assert savings_rate.category == RatioCategory.EFFICIENCY
    
    def test_liquidity_ratio_calculation(self):
        """Test liquidity ratio calculation"""
        ratios = self.engine.calculate_all_ratios(self.standard_assessment)
        liquidity_ratio = ratios["liquidity_ratio"]
        
        assert liquidity_ratio.value > 0
        assert liquidity_ratio.category == RatioCategory.LIQUIDITY
        assert "months" in liquidity_ratio.calculation_method.lower()
    
    def test_debt_ratios_calculation(self):
        """Test debt-related ratio calculations"""
        ratios = self.engine.calculate_all_ratios(self.standard_assessment)
        
        debt_to_income = ratios["debt_to_income"]
        debt_to_asset = ratios["debt_to_asset"]
        
        assert debt_to_income.category == RatioCategory.SOLVENCY
        assert debt_to_asset.category == RatioCategory.SOLVENCY
        assert debt_to_income.value >= 0
        assert debt_to_asset.value >= 0
    
    def test_net_worth_to_income_ratio(self):
        """Test net worth to income multiple calculation"""
        ratios = self.engine.calculate_all_ratios(self.standard_assessment)
        nw_ratio = ratios["net_worth_to_income"]
        
        # Expected: 150000 / 75000 = 2.0
        expected_multiple = 150000 / 75000
        assert abs(nw_ratio.value - expected_multiple) < 0.1
        assert nw_ratio.category == RatioCategory.PROFITABILITY
    
    def test_high_income_profile(self):
        """Test calculations for high-income profile"""
        ratios = self.engine.calculate_all_ratios(self.high_income_assessment)
        
        # High income should generally result in better ratios
        savings_rate = ratios["savings_rate"]
        net_worth_ratio = ratios["net_worth_to_income"]
        
        # Savings rate: (3000 * 12) / 150000 * 100 = 24%
        expected_savings = (3000 * 12 / 150000) * 100
        assert abs(savings_rate.value - expected_savings) < 0.1
        
        # Net worth multiple: 500000 / 150000 = 3.33
        expected_nw_multiple = 500000 / 150000
        assert abs(net_worth_ratio.value - expected_nw_multiple) < 0.1
    
    def test_low_income_profile(self):
        """Test calculations for low-income profile"""
        ratios = self.engine.calculate_all_ratios(self.low_income_assessment)
        
        # Should still calculate all ratios
        assert len(ratios) >= 8
        
        # Check savings rate
        savings_rate = ratios["savings_rate"]
        expected_savings = (200 * 12 / 35000) * 100  # ~6.86%
        assert abs(savings_rate.value - expected_savings) < 0.1
    
    def test_edge_case_zero_income(self):
        """Test handling of zero income edge case"""
        zero_income_assessment = self.standard_assessment.copy()
        zero_income_assessment["income"] = 0
        
        ratios = self.engine.calculate_all_ratios(zero_income_assessment)
        
        # Should handle gracefully with error ratios
        savings_rate = ratios["savings_rate"]
        assert "error" in savings_rate.interpretation.lower() or savings_rate.quality_score == 0
    
    def test_edge_case_negative_net_worth(self):
        """Test handling of negative net worth"""
        negative_nw_assessment = self.standard_assessment.copy()
        negative_nw_assessment["net_worth"] = -50000
        
        ratios = self.engine.calculate_all_ratios(negative_nw_assessment)
        
        # Should still calculate ratios
        nw_ratio = ratios["net_worth_to_income"]
        assert nw_ratio.value < 0  # Should reflect negative net worth
    
    def test_financial_profile_creation(self):
        """Test financial profile creation from assessment data"""
        profile = self.engine._create_financial_profile(self.standard_assessment)
        
        assert isinstance(profile, FinancialProfile)
        assert profile.age == 35
        assert profile.annual_income == 75000
        assert profile.net_worth == 150000
        assert profile.monthly_contribution == 1000
        assert profile.monthly_expenses > 0  # Should be estimated
        assert profile.liquid_assets > 0  # Should be estimated
    
    def test_profile_validation(self):
        """Test financial profile validation"""
        profile = self.engine._create_financial_profile(self.standard_assessment)
        validation = self.engine._validate_profile(profile)
        
        assert "valid" in validation
        assert "warnings" in validation
        assert isinstance(validation["warnings"], list)
    
    def test_profile_validation_warnings(self):
        """Test profile validation catches issues"""
        invalid_assessment = {
            "age": 150,  # Invalid age
            "income": -1000,  # Negative income
            "net_worth": 50000,
            "monthly_contribution": 10000,  # Unrealistic contribution
            "dependents": 0,
            "time_horizon": 10,
            "target_amount": 100000
        }
        
        profile = self.engine._create_financial_profile(invalid_assessment)
        validation = self.engine._validate_profile(profile)
        
        assert len(validation["warnings"]) > 0
    
    def test_ratio_interpretation(self):
        """Test ratio interpretation against benchmarks"""
        # Test excellent savings rate
        interpretation, score = self.engine._interpret_ratio("savings_rate", 25)
        assert "excellent" in interpretation.lower()
        assert score >= 85
        
        # Test poor savings rate
        interpretation, score = self.engine._interpret_ratio("savings_rate", 5)
        assert "poor" in interpretation.lower()
        assert score <= 30
    
    def test_goal_feasibility_calculation(self):
        """Test goal feasibility ratio calculation"""
        ratios = self.engine.calculate_all_ratios(self.standard_assessment)
        goal_ratio = ratios["goal_feasibility_ratio"]
        
        assert goal_ratio.category == RatioCategory.RISK
        assert goal_ratio.value >= 0
        assert "goal" in goal_ratio.name.lower()
    
    def test_financial_stability_score(self):
        """Test financial stability score calculation"""
        ratios = self.engine.calculate_all_ratios(self.standard_assessment)
        stability = ratios["financial_stability_score"]
        
        assert stability.category == RatioCategory.RISK
        assert 0 <= stability.value <= 100
        assert stability.quality_score > 0
    
    def test_ratio_summary_generation(self):
        """Test ratio summary generation"""
        ratios = self.engine.calculate_all_ratios(self.standard_assessment)
        summary = self.engine.generate_ratio_summary(ratios)
        
        assert "overall_score" in summary
        assert "health_status" in summary
        assert "total_ratios_calculated" in summary
        assert "categorized_ratios" in summary
        assert "recommendations" in summary
        
        assert 0 <= summary["overall_score"] <= 100
        assert summary["total_ratios_calculated"] > 0
        assert isinstance(summary["recommendations"], list)
    
    def test_categorized_ratios_in_summary(self):
        """Test that ratios are properly categorized in summary"""
        ratios = self.engine.calculate_all_ratios(self.standard_assessment)
        summary = self.engine.generate_ratio_summary(ratios)
        
        categorized = summary["categorized_ratios"]
        
        # Check that all categories are present
        for category in RatioCategory:
            assert category.value in categorized
            assert isinstance(categorized[category.value], list)
    
    def test_recommendations_generation(self):
        """Test recommendation generation based on ratios"""
        # Create a profile with poor ratios
        poor_assessment = {
            "age": 35,
            "income": 50000,
            "net_worth": 5000,  # Very low net worth
            "monthly_contribution": 100,  # Low savings
            "dependents": 2,
            "time_horizon": 10,
            "target_amount": 500000  # Ambitious goal
        }
        
        ratios = self.engine.calculate_all_ratios(poor_assessment)
        summary = self.engine.generate_ratio_summary(ratios)
        
        # Should generate multiple recommendations
        assert len(summary["recommendations"]) > 0
        
        # Check for common recommendations
        recommendations_text = " ".join(summary["recommendations"]).lower()
        assert any(keyword in recommendations_text for keyword in 
                  ["savings", "emergency", "debt", "goal"])
    
    def test_expense_ratio_calculation(self):
        """Test expense ratio calculation"""
        ratios = self.engine.calculate_all_ratios(self.standard_assessment)
        expense_ratio = ratios["expense_ratio"]
        
        assert expense_ratio.category == RatioCategory.EFFICIENCY
        assert expense_ratio.value > 0
        assert expense_ratio.value <= 100  # Should be percentage
    
    def test_investment_rate_age_adjustment(self):
        """Test investment rate calculation with age adjustment"""
        # Test young investor
        young_assessment = self.standard_assessment.copy()
        young_assessment["age"] = 25
        
        young_ratios = self.engine.calculate_all_ratios(young_assessment)
        young_investment = young_ratios["investment_rate"]
        
        # Test older investor
        older_assessment = self.standard_assessment.copy()
        older_assessment["age"] = 55
        
        older_ratios = self.engine.calculate_all_ratios(older_assessment)
        older_investment = older_ratios["investment_rate"]
        
        # Both should calculate successfully
        assert young_investment.value >= 0
        assert older_investment.value >= 0
        
        # Check that age affects the benchmark (mentioned in interpretation)
        assert "target" in young_investment.interpretation.lower()
        assert "target" in older_investment.interpretation.lower()


if __name__ == "__main__":
    # Run tests if executed directly
    import unittest
    
    # Convert pytest class to unittest
    suite = unittest.TestSuite()
    
    test_class = TestFinancialRatioEngine()
    test_class.setup_method()
    
    # Add test methods
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    for method_name in test_methods:
        suite.addTest(unittest.FunctionTestCase(getattr(test_class, method_name)))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ All financial ratio tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        for failure in result.failures:
            print(f"FAIL: {failure[0]}")
        for error in result.errors:
            print(f"ERROR: {error[0]}")