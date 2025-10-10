"""
Profile Processing Functions for Investment Portfolio Management

This module provides functions to structure user input data from the frontend assessment 
into a standardized User Profile dataclass for other agents to consume.

Main functions:
- process_frontend_data(): Convert frontend data to UserProfile dataclass
- generate_user_profile(): Main entry point for profile generation
"""

from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

@dataclass
class UserProfile:
    """Standardized User Profile dataclass for agent communication"""
    
    # Core financial information
    goals: List[Dict[str, Any]]
    time_horizon: int
    risk_tolerance: str
    
    # Financial capacity
    income: float
    savings_rate: float
    liabilities: float
    liquidity_needs: str
    
    # Personal information
    personal_values: Dict[str, Any]
    
    # Investment preferences
    esg_prioritization: bool
    market_selection: List[str]
    
    # Metadata
    timestamp: str
    profile_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary"""
        return asdict(self)

def process_frontend_data(frontend_data: Dict[str, Any]) -> UserProfile:
    """
    Convert frontend assessment data to UserProfile dataclass
    
    Args:
        frontend_data: Raw data from frontend assessment component
        
    Returns:
        UserProfile: Structured profile data
    """
    
    # Generate unique profile ID
    profile_id = f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    # TODO: Add more robust unique ID generation if needed to support profile update function and use PostgreSQL to store profiles.
    
    # Create and return UserProfile dataclass
    user_profile = UserProfile(
        goals=_extract_goals(frontend_data.get('goals', [])),
        time_horizon=frontend_data.get('timeHorizon', 10),
        risk_tolerance=_map_risk_tolerance(frontend_data.get('riskTolerance', '')),
        income=float(frontend_data.get('annualIncome', 0)),
        savings_rate=float(frontend_data.get('monthlySavings', 0)),
        liabilities=float(frontend_data.get('totalDebt', 0)),
        liquidity_needs=_map_liquidity_needs(frontend_data.get('emergencyFundMonths', '')),
        personal_values=_extract_values(frontend_data.get('values', {})),
        esg_prioritization=frontend_data.get('esgPrioritization', False),
        market_selection=frontend_data.get('marketSelection', []),
        timestamp=datetime.now().isoformat(),
        profile_id=profile_id
    )
    
    return user_profile


def _extract_goals(goals_data: List[Dict]) -> List[Dict[str, Any]]:
    """Extract and format investment goals"""
    return [
        {
            "goal_type": goal.get('id', ''),
            "description": goal.get('label', ''),
            "priority": goal.get('priority', 999),
            "target_date": None  # Could be calculated from milestones if needed
        }
        for goal in goals_data
    ]


def _map_risk_tolerance(risk_tolerance: str) -> str:
    """Map frontend risk tolerance to standardized format"""
    risk_mapping = {
        "conservative": "low",
        "moderate": "medium", 
        "aggressive": "high",
        "": "medium"  # default
    }
    return risk_mapping.get(risk_tolerance.lower(), "medium")


def _map_liquidity_needs(emergency_months: str) -> str:
    """Map emergency fund months to liquidity needs"""
    if not emergency_months:
        return "medium"
    
    try:
        months = int(emergency_months.split()[0]) if emergency_months else 6
        if months <= 3:
            return "high"
        elif months <= 6:
            return "medium"
        else:
            return "low"
    except (ValueError, IndexError):
        return "medium"


def _extract_values(values_data: Dict) -> Dict[str, Any]:
    """Extract personal values and ESG preferences"""
    return {
        "esg_preferences": {
            "avoid_industries": values_data.get('avoidIndustries', []),
            "prefer_industries": values_data.get('preferIndustries', []),
            "specific_assets": values_data.get('specificAssets', ''),  # Now a string for LLM parsing
            "custom_constraints": values_data.get('customConstraints', '')
        },
        "investment_themes": values_data.get('preferIndustries', []),
        "specific_assets": values_data.get('specificAssets', '')  # String format for natural language input
    }


def generate_user_profile(frontend_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to process frontend data and generate UserProfile dataclass
    
    Args:
        frontend_data: Raw assessment data from frontend
        
    Returns:
        Dict containing the profile data and status
    """
    
    # Process the data
    user_profile = process_frontend_data(frontend_data)
    
    return {
        "profile_data": user_profile.to_dict(),
        "profile_object": user_profile,
        "status": "success"
    }
