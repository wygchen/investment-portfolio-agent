import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Import the FastAPI app
from main import app, assessments_db, portfolios_db

# Create test client
client = TestClient(app)

# Test fixtures
@pytest.fixture
def sample_assessment_data() -> Dict[str, Any]:
    """Sample assessment data for testing"""
    return {
        "age": 35,
        "income": 75000,
        "net_worth": 150000,
        "dependents": 2,
        "primary_goal": "retirement",
        "time_horizon": 25,
        "target_amount": 1000000,
        "monthly_contribution": 2000,
        "risk_tolerance": 6,
        "risk_capacity": "moderate",
        "previous_experience": ["stocks", "bonds"],
        "market_reaction": "hold_steady",
        "investment_style": "long_term",
        "rebalancing_frequency": "quarterly",
        "esg_preferences": True,
        "special_circumstances": "Planning for children's education"
    }

@pytest.fixture
def invalid_assessment_data() -> Dict[str, Any]:
    """Invalid assessment data for testing validation"""
    return {
        "age": 150,  # Invalid: too old
        "income": -5000,  # Invalid: negative income
        "net_worth": -10000,  # Invalid: negative net worth
        "dependents": -1,  # Invalid: negative dependents
        "primary_goal": "",  # Invalid: empty string
        "time_horizon": 0,  # Invalid: zero time horizon
        "target_amount": -1000,  # Invalid: negative target
        "monthly_contribution": -500,  # Invalid: negative contribution
        "risk_tolerance": 15,  # Invalid: out of range
        "risk_capacity": "invalid",
        "previous_experience": [],
        "market_reaction": "",
        "investment_style": "",
        "rebalancing_frequency": "",
        "esg_preferences": "not_boolean"  # Invalid: not boolean
    }

@pytest.fixture(autouse=True)
def clear_databases():
    """Clear in-memory databases before each test"""
    assessments_db.clear()
    portfolios_db.clear()
    yield
    assessments_db.clear()
    portfolios_db.clear()

class TestBasicEndpoints:
    """Test basic API endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns correct information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "PortfolioAI API"
        assert data["status"] == "running"
        assert data["version"] == "1.0.0"
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

class TestAssessmentEndpoints:
    """Test assessment-related endpoints"""
    
    def test_submit_valid_assessment(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test submitting valid assessment data"""
        response = client.post("/api/assessment", json=sample_assessment_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "user_id" in data
        assert "assessment_id" in data
        assert data["message"] == "Assessment data received successfully"
    
    def test_submit_invalid_assessment(self, invalid_assessment_data: Dict[str, Any]) -> None:
        """Test submitting invalid assessment data returns validation error"""
        response = client.post("/api/assessment", json=invalid_assessment_data)
        assert response.status_code == 422  # Validation error
    
    def test_submit_incomplete_assessment(self) -> None:
        """Test submitting incomplete assessment data"""
        incomplete_data = {"age": 30, "income": 50000}  # Missing required fields
        response = client.post("/api/assessment", json=incomplete_data)
        assert response.status_code == 422
    
    def test_get_existing_assessment(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test retrieving existing assessment data"""
        # First submit an assessment
        submit_response = client.post("/api/assessment", json=sample_assessment_data)
        user_id = submit_response.json()["user_id"]
        
        # Then retrieve it
        response = client.get(f"/api/assessment/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["age"] == sample_assessment_data["age"]
        assert data["income"] == sample_assessment_data["income"]
    
    def test_get_nonexistent_assessment(self) -> None:
        """Test retrieving non-existent assessment returns 404"""
        response = client.get("/api/assessment/nonexistent_user")
        assert response.status_code == 404
        assert "Assessment not found" in response.json()["detail"]

class TestPortfolioEndpoints:
    """Test portfolio generation and retrieval endpoints"""
    
    def test_generate_portfolio_valid_data(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test generating portfolio with valid assessment data"""
        response = client.post("/api/portfolio/generate", json=sample_assessment_data)
        assert response.status_code == 200
        data = response.json()
        
        # Verify portfolio structure
        assert "allocation" in data
        assert "expected_return" in data
        assert "volatility" in data
        assert "sharpe_ratio" in data
        assert "risk_score" in data
        assert "confidence" in data
        
        # Verify allocations sum to 100%
        total_percentage = sum(alloc["percentage"] for alloc in data["allocation"])
        assert abs(total_percentage - 100.0) < 0.1  # Allow for small rounding errors
        
        # Verify confidence is within valid range
        assert 0 <= data["confidence"] <= 100
    
    def test_generate_portfolio_invalid_data(self, invalid_assessment_data: Dict[str, Any]) -> None:
        """Test generating portfolio with invalid assessment data"""
        response = client.post("/api/portfolio/generate", json=invalid_assessment_data)
        assert response.status_code == 422
    
    def test_get_existing_portfolio(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test retrieving existing portfolio"""
        # Generate a portfolio first
        generate_response = client.post("/api/portfolio/generate", json=sample_assessment_data)
        
        # Create a user_id and store portfolio
        user_id = "test_user_1"
        portfolios_db[user_id] = generate_response.json()
        
        # Retrieve the portfolio
        response = client.get(f"/api/portfolio/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert "allocation" in data
    
    def test_get_nonexistent_portfolio(self):
        """Test retrieving non-existent portfolio returns 404"""
        response = client.get("/api/portfolio/nonexistent_user")
        assert response.status_code == 404
        assert "Portfolio not found" in response.json()["detail"]

class TestMarketDataEndpoints:
    """Test market data endpoints"""
    
    def test_market_overview(self):
        """Test market overview endpoint"""
        response = client.get("/api/market-data/overview")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required sections
        assert "market_indices" in data
        assert "sector_performance" in data
        assert "economic_indicators" in data
        assert "last_updated" in data
        
        # Verify market indices structure
        assert len(data["market_indices"]) > 0
        for index in data["market_indices"]:
            assert "name" in index
            assert "value" in index
            assert "change" in index
            assert "change_percent" in index
    
    def test_asset_performance(self):
        """Test asset performance endpoint"""
        asset_class = "equities"
        response = client.get(f"/api/market-data/assets/{asset_class}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["asset_class"] == asset_class
        assert "current_price" in data
        assert "change_24h" in data
        assert "change_percent_24h" in data
        assert "historical_data" in data
        assert "volatility" in data
        
        # Verify historical data structure
        assert len(data["historical_data"]) > 0
        for datapoint in data["historical_data"]:
            assert "date" in datapoint
            assert "price" in datapoint
            assert "volume" in datapoint

class TestRiskAnalyticsEndpoints:
    """Test risk analytics endpoints"""
    
    def test_portfolio_risk_metrics_existing_portfolio(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test risk metrics for existing portfolio"""
        # Create a portfolio first
        user_id = "test_user_1"
        generate_response = client.post("/api/portfolio/generate", json=sample_assessment_data)
        portfolios_db[user_id] = generate_response.json()
        
        response = client.get(f"/api/risk-analytics/portfolio/{user_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify risk metrics structure
        assert "risk_metrics" in data
        assert "stress_test_scenarios" in data
        assert "monte_carlo_projections" in data
        assert "risk_alerts" in data
        
        # Verify risk metrics values
        risk_metrics = data["risk_metrics"]
        assert "var_95" in risk_metrics
        assert "cvar_95" in risk_metrics
        assert "maximum_drawdown" in risk_metrics
        assert "beta" in risk_metrics
    
    def test_portfolio_risk_metrics_nonexistent_portfolio(self):
        """Test risk metrics for non-existent portfolio"""
        response = client.get("/api/risk-analytics/portfolio/nonexistent_user")
        assert response.status_code == 404
        assert "Portfolio not found" in response.json()["detail"]
    
    def test_market_risk_conditions(self):
        """Test market risk conditions endpoint"""
        response = client.get("/api/risk-analytics/market-conditions")
        assert response.status_code == 200
        data = response.json()
        
        assert "volatility_regime" in data
        assert "market_stress_level" in data
        assert "correlation_environment" in data
        assert "liquidity_conditions" in data
        assert "risk_indicators" in data
        assert "regime_probabilities" in data

class TestDashboardEndpoints:
    """Test dashboard endpoints"""
    
    def test_dashboard_overview_existing_portfolio(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test dashboard overview for existing portfolio"""
        # Create a portfolio first
        user_id = "test_user_1"
        generate_response = client.post("/api/portfolio/generate", json=sample_assessment_data)
        portfolios_db[user_id] = generate_response.json()
        
        response = client.get(f"/api/dashboard/overview/{user_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify dashboard structure
        assert "portfolio_value" in data
        assert "total_return" in data
        assert "total_return_amount" in data
        assert "performance_data" in data
        assert "allocation" in data
        assert "rebalancing_recommendations" in data
        assert "recent_trades" in data
    
    def test_dashboard_overview_nonexistent_portfolio(self):
        """Test dashboard overview for non-existent portfolio"""
        response = client.get("/api/dashboard/overview/nonexistent_user")
        assert response.status_code == 404
        assert "Portfolio not found" in response.json()["detail"]
    
    def test_performance_analytics_existing_portfolio(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test performance analytics for existing portfolio"""
        # Create a portfolio first
        user_id = "test_user_1"
        generate_response = client.post("/api/portfolio/generate", json=sample_assessment_data)
        portfolios_db[user_id] = generate_response.json()
        
        response = client.get(f"/api/dashboard/performance/{user_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert "period" in data
        assert "total_return" in data
        assert "annualized_return" in data
        assert "volatility" in data
        assert "sharpe_ratio" in data
        assert "benchmark_comparison" in data
        assert "attribution_analysis" in data
    
    def test_performance_analytics_with_period_parameter(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test performance analytics with different period parameter"""
        # Create a portfolio first
        user_id = "test_user_1"
        generate_response = client.post("/api/portfolio/generate", json=sample_assessment_data)
        portfolios_db[user_id] = generate_response.json()
        
        response = client.get(f"/api/dashboard/performance/{user_id}?period=6m")
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "6m"

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_invalid_json_request(self) -> None:
        """Test handling of invalid JSON in request body"""
        response = client.post(
            "/api/assessment",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_content_type(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test handling of missing content type"""
        response = client.post("/api/assessment", content=json.dumps(sample_assessment_data))
        # Should still work as FastAPI handles this gracefully
        assert response.status_code in [200, 422]
    
    @patch('main._generate_mock_portfolio')
    def test_portfolio_generation_error_handling(self, mock_generate: MagicMock, sample_assessment_data: Dict[str, Any]) -> None:
        """Test error handling in portfolio generation"""
        mock_generate.side_effect = Exception("Simulated error")
        
        response = client.post("/api/portfolio/generate", json=sample_assessment_data)
        assert response.status_code == 500
        assert "Failed to generate portfolio" in response.json()["detail"]

class TestDataValidation:
    """Test data validation and edge cases"""
    
    def test_age_boundary_values(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test age boundary value validation"""
        # Test minimum valid age
        sample_assessment_data["age"] = 18
        response = client.post("/api/assessment", json=sample_assessment_data)
        assert response.status_code == 200
        
        # Test maximum valid age
        sample_assessment_data["age"] = 100
        response = client.post("/api/assessment", json=sample_assessment_data)
        assert response.status_code == 200
        
        # Test invalid ages
        sample_assessment_data["age"] = 17
        response = client.post("/api/assessment", json=sample_assessment_data)
        assert response.status_code == 422
        
        sample_assessment_data["age"] = 101
        response = client.post("/api/assessment", json=sample_assessment_data)
        assert response.status_code == 422
    
    def test_risk_tolerance_validation(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test risk tolerance validation"""
        # Test valid range
        for risk_level in range(1, 11):
            sample_assessment_data["risk_tolerance"] = risk_level
            response = client.post("/api/assessment", json=sample_assessment_data)
            assert response.status_code == 200
        
        # Test invalid values
        sample_assessment_data["risk_tolerance"] = 0
        response = client.post("/api/assessment", json=sample_assessment_data)
        assert response.status_code == 422
        
        sample_assessment_data["risk_tolerance"] = 11
        response = client.post("/api/assessment", json=sample_assessment_data)
        assert response.status_code == 422
    
    def test_negative_financial_values(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test handling of negative financial values"""
        # Test negative income
        sample_assessment_data["income"] = -1000
        response = client.post("/api/assessment", json=sample_assessment_data)
        assert response.status_code == 422
        
        # Test negative net worth
        sample_assessment_data["income"] = 50000  # Reset to valid
        sample_assessment_data["net_worth"] = -5000
        response = client.post("/api/assessment", json=sample_assessment_data)
        assert response.status_code == 422

class TestPortfolioLogic:
    """Test portfolio generation logic"""
    
    def test_conservative_portfolio_allocation(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test conservative portfolio allocation for low risk tolerance"""
        sample_assessment_data["risk_tolerance"] = 2
        response = client.post("/api/portfolio/generate", json=sample_assessment_data)
        assert response.status_code == 200
        data = response.json()
        
        # Conservative portfolios should have higher bond allocation
        bond_allocation = next((alloc for alloc in data["allocation"] if "Bond" in alloc["name"]), None)
        assert bond_allocation is not None
        assert bond_allocation["percentage"] >= 30  # Conservative should have significant bonds
    
    def test_aggressive_portfolio_allocation(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test aggressive portfolio allocation for high risk tolerance"""
        sample_assessment_data["risk_tolerance"] = 9
        response = client.post("/api/portfolio/generate", json=sample_assessment_data)
        assert response.status_code == 200
        data = response.json()
        
        # Aggressive portfolios should have higher equity allocation
        equity_allocations = [alloc for alloc in data["allocation"] if "Equit" in alloc["name"]]
        total_equity = sum(alloc["percentage"] for alloc in equity_allocations)
        assert total_equity >= 60  # Aggressive should have majority in equities
    
    def test_portfolio_allocation_sums_to_100(self, sample_assessment_data: Dict[str, Any]) -> None:
        """Test that portfolio allocations always sum to 100%"""
        for risk_level in [2, 5, 8]:
            sample_assessment_data["risk_tolerance"] = risk_level
            response = client.post("/api/portfolio/generate", json=sample_assessment_data)
            assert response.status_code == 200
            data = response.json()
            
            total_percentage = sum(alloc["percentage"] for alloc in data["allocation"])
            assert abs(total_percentage - 100.0) < 0.01  # Allow tiny rounding errors

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])