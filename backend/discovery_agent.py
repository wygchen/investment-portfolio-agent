"""
Discovery Agent for Investment Portfolio Management

This agent structures user input data from the frontend assessment 
into a standardized User Profile JSON format for other agents to consume.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class UserProfileJSON(BaseModel):
    """Standardized User Profile JSON structure for agent communication"""
    
    # Core financial information
    goals: List[Dict[str, Any]] = Field(description="Investment goals with priorities")
    time_horizon: int = Field(description="Investment time horizon in years")
    risk_tolerance: str = Field(description="Risk tolerance level")
    
    # Financial capacity
    income: float = Field(description="Annual income")
    savings_rate: float = Field(description="Monthly savings amount") 
    liabilities: float = Field(description="Total debt/liabilities")
    liquidity_needs: str = Field(description="Emergency fund requirements")
    
    # Personal information
    personal_values: Dict[str, Any] = Field(description="ESG preferences and values")
    
    # Metadata
    timestamp: str = Field(description="When profile was created")
    profile_id: str = Field(description="Unique profile identifier")


class DiscoveryAgent:
    """
    Discovery Agent that converts frontend assessment data into structured JSON
    """
    
    def __init__(self, output_dir: str = "./shared_data"):
        """
        Initialize the Discovery Agent
        
        Args:
            output_dir: Directory to store generated JSON profiles
        """
        self.output_dir = output_dir
        self.ensure_output_directory()
    
    def ensure_output_directory(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def process_frontend_data(self, frontend_data: Dict[str, Any]) -> UserProfileJSON:
        """
        Convert frontend assessment data to User Profile JSON
        
        Args:
            frontend_data: Raw data from frontend DiscoveryFlow component
            
        Returns:
            UserProfileJSON: Structured profile data
        """
        
        # Generate unique profile ID
        profile_id = f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Extract and structure the data
        user_profile = UserProfileJSON(
            goals=self._extract_goals(frontend_data.get('goals', [])),
            time_horizon=frontend_data.get('timeHorizon', 10),
            risk_tolerance=self._map_risk_tolerance(frontend_data.get('riskTolerance', '')),
            income=float(frontend_data.get('annualIncome', 0)),
            savings_rate=float(frontend_data.get('monthlySavings', 0)),
            liabilities=float(frontend_data.get('totalDebt', 0)),
            liquidity_needs=self._map_liquidity_needs(frontend_data.get('emergencyFundMonths', '')),
            personal_values=self._extract_values(frontend_data.get('values', {})),
            timestamp=datetime.now().isoformat(),
            profile_id=profile_id
        )
        
        return user_profile
    
    def _extract_goals(self, goals_data: List[Dict]) -> List[Dict[str, Any]]:
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
    
    def _map_risk_tolerance(self, risk_tolerance: str) -> str:
        """Map frontend risk tolerance to standardized format"""
        risk_mapping = {
            "conservative": "low",
            "moderate": "medium", 
            "aggressive": "high",
            "": "medium"  # default
        }
        return risk_mapping.get(risk_tolerance.lower(), "medium")
    
    def _map_liquidity_needs(self, emergency_months: str) -> str:
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
    
    def _extract_values(self, values_data: Dict) -> Dict[str, Any]:
        """Extract personal values and ESG preferences"""
        return {
            "esg_preferences": {
                "avoid_industries": values_data.get('avoidIndustries', []),
                "prefer_industries": values_data.get('preferIndustries', []),
                "custom_constraints": values_data.get('customConstraints', '')
            },
            "investment_themes": values_data.get('preferIndustries', [])
        }
    
    def save_profile_json(self, user_profile: UserProfileJSON) -> str:
        """
        Save User Profile JSON to shared data directory
        
        Args:
            user_profile: The structured user profile
            
        Returns:
            str: Path to saved JSON file
        """
        
        filename = f"{user_profile.profile_id}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        # Save profile to JSON file
        with open(filepath, 'w') as f:
            json.dump(user_profile.dict(), f, indent=2)
        
        # Also save as latest profile for easy access
        latest_path = os.path.join(self.output_dir, "latest_profile.json")
        with open(latest_path, 'w') as f:
            json.dump(user_profile.dict(), f, indent=2)
        
        return filepath
    
    def generate_user_profile(self, frontend_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to process frontend data and generate User Profile JSON
        
        Args:
            frontend_data: Raw assessment data from frontend
            
        Returns:
            Dict containing the profile data and file path
        """
        
        # Process the data
        user_profile = self.process_frontend_data(frontend_data)
        
        # Save to file
        filepath = self.save_profile_json(user_profile)
        
        return {
            "profile_data": user_profile.dict(),
            "file_path": filepath,
            "status": "success",
            "message": f"User profile generated successfully: {user_profile.profile_id}"
        }


# Example usage and testing
if __name__ == "__main__":
    # Example frontend data (matching the DiscoveryFlow component structure)
    sample_frontend_data = {
        "goals": [
            {"id": "retirement", "label": "Retirement Planning", "priority": 1},
            {"id": "house", "label": "Buy a Home", "priority": 2}
        ],
        "timeHorizon": 15,
        "riskTolerance": "moderate",
        "annualIncome": 75000,
        "monthlySavings": 2000,
        "totalDebt": 25000,
        "emergencyFundMonths": "6 months",
        "values": {
            "avoidIndustries": ["tobacco", "weapons"],
            "preferIndustries": ["technology", "renewable_energy"],
            "customConstraints": "Focus on sustainable investments"
        }
    }
    
    # Test the discovery agent
    agent = DiscoveryAgent()
    result = agent.generate_user_profile(sample_frontend_data)
    
    print("Discovery Agent Test Result:")
    print(json.dumps(result, indent=2))
