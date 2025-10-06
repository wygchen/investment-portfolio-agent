"""
Data Sharing Module for Agent Communication

This module provides simple file-based data sharing between agents.
Other team members can use this to retrieve user profile JSON data.
"""

import json
import os
import glob
from typing import Dict, List, Optional, Any
from datetime import datetime


class DataSharingManager:
    """
    Simple file-based data sharing system for agent communication
    """
    
    def __init__(self, shared_dir: str = "./shared_data"):
        self.shared_dir = shared_dir
        self.ensure_directory()
    
    def ensure_directory(self):
        """Ensure shared data directory exists"""
        if not os.path.exists(self.shared_dir):
            os.makedirs(self.shared_dir)
    
    def get_latest_profile(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve the most recent user profile JSON
        
        Returns:
            Dict containing user profile data or None if not found
        """
        latest_path = os.path.join(self.shared_dir, "latest_profile.json")
        
        if os.path.exists(latest_path):
            with open(latest_path, 'r') as f:
                return json.load(f)
        return None
    
    def get_profile_by_id(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific user profile by ID
        
        Args:
            profile_id: The unique profile identifier
            
        Returns:
            Dict containing user profile data or None if not found
        """
        filepath = os.path.join(self.shared_dir, f"{profile_id}.json")
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return None
    
    def list_all_profiles(self) -> List[str]:
        """
        Get list of all available profile IDs
        
        Returns:
            List of profile IDs
        """
        pattern = os.path.join(self.shared_dir, "profile_*.json")
        files = glob.glob(pattern)
        
        profile_ids = []
        for file in files:
            filename = os.path.basename(file)
            if filename != "latest_profile.json":
                profile_id = filename.replace('.json', '')
                profile_ids.append(profile_id)
        
        return sorted(profile_ids)
    
    def save_agent_output(self, agent_name: str, output_data: Dict[str, Any]) -> str:
        """
        Save output from any agent for other agents to consume
        
        Args:
            agent_name: Name of the agent (e.g., 'risk_analysis', 'portfolio_construction')
            output_data: Data to save
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{agent_name}_{timestamp}.json"
        filepath = os.path.join(self.shared_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        # Also save as latest output for this agent
        latest_filename = f"latest_{agent_name}.json"
        latest_filepath = os.path.join(self.shared_dir, latest_filename)
        with open(latest_filepath, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        return filepath
    
    def get_agent_output(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest output from a specific agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dict containing agent output or None if not found
        """
        latest_filepath = os.path.join(self.shared_dir, f"latest_{agent_name}.json")
        
        if os.path.exists(latest_filepath):
            with open(latest_filepath, 'r') as f:
                return json.load(f)
        return None


# Convenience functions for other team members to use
def get_user_profile_data() -> Optional[Dict[str, Any]]:
    """
    Quick function to get the latest user profile data
    
    Usage for other team members:
    from data_sharing import get_user_profile_data
    profile = get_user_profile_data()
    """
    manager = DataSharingManager()
    return manager.get_latest_profile()


def save_my_agent_results(agent_name: str, results: Dict[str, Any]) -> str:
    """
    Quick function for other agents to save their results
    
    Usage:
    from data_sharing import save_my_agent_results
    save_my_agent_results("risk_analysis", my_results)
    """
    manager = DataSharingManager()
    return manager.save_agent_output(agent_name, results)


def get_other_agent_results(agent_name: str) -> Optional[Dict[str, Any]]:
    """
    Quick function to get results from another agent
    
    Usage:
    from data_sharing import get_other_agent_results
    risk_data = get_other_agent_results("risk_analysis")
    """
    manager = DataSharingManager()
    return manager.get_agent_output(agent_name)


# Example usage for testing
if __name__ == "__main__":
    manager = DataSharingManager()
    
    # Test retrieving profile data
    profile = manager.get_latest_profile()
    if profile:
        print("Latest profile found:")
        print(json.dumps(profile, indent=2))
    else:
        print("No profile data found. Run the discovery agent first.")
    
    # Test saving sample agent output
    sample_risk_output = {
        "risk_score": 6.5,
        "risk_level": "moderate", 
        "recommendations": ["Diversify portfolio", "Consider bond allocation"],
        "timestamp": datetime.now().isoformat()
    }
    
    saved_path = manager.save_agent_output("risk_analysis", sample_risk_output)
    print(f"Sample risk analysis saved to: {saved_path}")date
