# Discovery Agent Integration Guide

## Overview

This document explains how to integrate with the Discovery Agent and access user profile data for the Investment Portfolio Management system. The Discovery Agent processes user assessment data from the frontend and outputs structured JSON data that other agents can consume.

The Discovery Agent:
1. Takes user input from frontend assessment flow
2. Structures data into standardized User Profile JSON format
3. Saves data to shared file system
4. Provides APIs for other agents to access data

## Files to Include in GitHub Repository

### Core Discovery Agent Files (Wilson's Components)
```
backend/
├── discovery_agent.py          # Main discovery agent implementation
├── data_sharing.py            # Data sharing utilities for team members
├── simple_server.py           # Updated API server with discovery endpoints
└── shared_data/               # Directory for JSON data exchange
    ├── latest_profile.json    # Most recent user profile (auto-generated)
    └── profile_*.json         # Individual profile files (auto-generated)

frontend/components/
└── discovery-flow.tsx         # Updated to call discovery agent API
```

### Required Dependencies
Add to `backend/requirements.txt`:
```
fastapi
uvicorn
pydantic
python-dotenv
```

## User Profile JSON Format

The Discovery Agent outputs user profile data in this standardized format:

```json
{
  "goals": [
    {
      "goal_type": "retirement",
      "description": "Retirement Planning", 
      "priority": 1,
      "target_date": null
    }
  ],
  "time_horizon": 15,
  "risk_tolerance": "medium",
  "income": 75000.0,
  "savings_rate": 2000.0,
  "liabilities": 25000.0,
  "liquidity_needs": "medium",
  "personal_values": {
    "esg_preferences": {
      "avoid_industries": ["tobacco", "weapons"],
      "prefer_industries": ["technology", "renewable_energy"],
      "custom_constraints": "Focus on sustainable investments"
    },
    "investment_themes": ["technology", "renewable_energy"]
  },
  "timestamp": "2025-10-06T12:00:00.000000",
  "profile_id": "profile_20251006_120000"
}
```

## How to Access User Profile Data (For Teammates)

### Method 1: Direct File Access (Simplest)

```python
import json
import os

def get_latest_user_profile():
    """Get the most recent user profile data"""
    try:
        with open('./shared_data/latest_profile.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# Usage in your agent:
profile_data = get_latest_user_profile()
if profile_data:
    user_risk_tolerance = profile_data['risk_tolerance']
    user_goals = profile_data['goals']
    # Process data for your agent...
```

### Method 2: Using Data Sharing Utilities

```python
# Import the data sharing module
from data_sharing import get_user_profile_data, save_my_agent_results

# Get user profile data
profile = get_user_profile_data()

# Your agent processing...
my_analysis_results = {
    "risk_score": 7.2,
    "recommendations": ["Increase equity allocation", "Consider growth funds"],
    "analysis_timestamp": "2025-10-06T12:30:00"
}

# Save your results for other agents
save_my_agent_results("risk_analysis", my_analysis_results)
```

### Method 3: API Endpoints

The Discovery Agent provides REST API endpoints:

```python
import requests

# Get latest profile via API
response = requests.get('http://localhost:8000/api/profile/latest')
if response.status_code == 200:
    profile_data = response.json()['profile']

# List all available profiles
response = requests.get('http://localhost:8000/api/profiles/list')
profiles = response.json()['profiles']

# Get specific profile by ID
response = requests.get(f'http://localhost:8000/api/profile/{profile_id}')
```

## Running the Discovery Agent

### 1. Start the Backend Server

```bash
cd backend
python simple_server.py
```

The server will start on `http://localhost:8000`

### 2. Start the Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 3. Test the Flow

1. Go to `http://localhost:3000/assessment`
2. Complete the user assessment
3. Check `backend/shared_data/latest_profile.json` for generated data

## Data Flow Example

1. **User completes assessment** → Frontend collects data
2. **Frontend submits to discovery agent** → `POST /api/process-assessment`
3. **Discovery agent processes data** → Creates structured JSON
4. **Data saved to shared directory** → `shared_data/latest_profile.json`
5. **Other agents access data** → Use file system or API endpoints

## Integration for Risk Analysis Agent (Tiffany)

```python
# Example integration for Tiffany's risk analysis agent
from data_sharing import get_user_profile_data, save_my_agent_results

def run_risk_analysis():
    # Get user profile from discovery agent
    profile = get_user_profile_data()
    
    if not profile:
        print("No user profile data available")
        return
    
    # Extract relevant data for risk analysis
    risk_tolerance = profile['risk_tolerance']  # 'low', 'medium', 'high'
    income = profile['income']
    liabilities = profile['liabilities']
    time_horizon = profile['time_horizon']
    
    # Your risk analysis logic here...
    risk_analysis_results = {
        "risk_capacity": calculate_risk_capacity(income, liabilities),
        "risk_score": calculate_risk_score(risk_tolerance, time_horizon),
        "recommendations": generate_recommendations(),
        "timestamp": datetime.now().isoformat()
    }
    
    # Save results for other agents to use
    save_my_agent_results("risk_analysis", risk_analysis_results)
    
    return risk_analysis_results
```

## Integration for Other Agents

### Portfolio Construction Agent (KX)
```python
from data_sharing import get_user_profile_data, get_other_agent_results

# Get user profile AND risk analysis results
profile = get_user_profile_data()
risk_data = get_other_agent_results("risk_analysis")

# Use both datasets for portfolio construction
```

### Selection Agent (Grace)
```python
from data_sharing import get_other_agent_results

# Get portfolio allocation from construction agent
portfolio_data = get_other_agent_results("portfolio_construction")
```

## API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/process-assessment` | Main discovery agent endpoint |
| GET | `/api/profile/latest` | Get most recent user profile |
| GET | `/api/profile/{profile_id}` | Get specific profile by ID |
| GET | `/api/profiles/list` | List all available profiles |
| POST | `/api/agent-output/{agent_name}` | Save agent results |
| GET | `/api/agent-output/{agent_name}` | Get agent results |

## Testing

### Test the Discovery Agent
```bash
cd backend
python discovery_agent.py
```

### Test Data Sharing
```bash
cd backend  
python data_sharing.py
```

### Test API Server
```bash
curl http://localhost:8000/api/profile/latest
```

## Troubleshooting

### Common Issues

1. **No profile data found**: Make sure to complete the frontend assessment first
2. **Server connection errors**: Ensure backend server is running on port 8000
3. **File not found errors**: Check that `shared_data` directory exists and has proper permissions

### Debug Mode

Enable debug logging in your agent:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Minimal Changes Summary

This implementation requires minimal changes to the existing structure:

✅ **Added Files** (Wilson's responsibility):
- `backend/discovery_agent.py` 
- `backend/data_sharing.py`
- `backend/shared_data/` directory

✅ **Modified Files** (Wilson's responsibility):
- `backend/simple_server.py` (updated to use discovery agent)
- `frontend/components/discovery-flow.tsx` (updated API call)

✅ **No changes needed** to other existing files

This approach allows each team member to focus on their specific agent while having a clean interface to access user profile data.
