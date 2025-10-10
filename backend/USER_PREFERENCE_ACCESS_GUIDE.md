# User Asset & Stock Preference Access Guide

## Overview
This document shows exactly where and how other agents in the investment portfolio system can access user input on specific asset and stock preferences.

## Data Flow Architecture

```
Frontend Assessment → API Validation → Profile Processing → Agent Access
```

### 1. Frontend Data Structure
**File**: `frontend/app/assessment/values-step.tsx`

Users enter preferences in the Values Step:
```typescript
// User enters specific assets like: "AAPL, MSFT, Tesla, VTI, SPY"
profile.values.specificAssets: string[]
profile.values.avoidIndustries: string[]
profile.values.preferIndustries: string[]
profile.values.customConstraints: string
profile.esgPrioritization: boolean
profile.marketSelection: string[]
```

### 2. Backend API Processing
**File**: `backend/simple_main.py`

The Values Pydantic model now includes:
```python
class Values(BaseModel):
    avoidIndustries: List[str] = []
    preferIndustries: List[str] = []
    specificAssets: List[str] = []  # ← NEW: User-specified assets
    customConstraints: str = ""

class AssessmentData(BaseModel):
    values: Values = Values()
    esgPrioritization: bool = False
    marketSelection: List[str] = ["US"]
    # ... other fields
```

### 3. Profile Processing
**File**: `backend/profile_processor.py`

The `_extract_values()` function processes user preferences:
```python
def _extract_values(values_data: Dict) -> Dict[str, Any]:
    return {
        "esg_preferences": {
            "avoid_industries": values_data.get('avoidIndustries', []),
            "prefer_industries": values_data.get('preferIndustries', []),
            "specific_assets": values_data.get('specificAssets', []),  # ← NEW
            "custom_constraints": values_data.get('customConstraints', '')
        },
        "investment_themes": values_data.get('preferIndustries', []),
        "specific_assets": values_data.get('specificAssets', [])  # ← NEW
    }
```

## Agent Access Patterns

### 1. Selection Agent Access
**File**: `backend/main_agent.py` (Lines 490-520)

The Selection Agent can access user preferences via:
```python
def selection_node(self, state: MainAgentState) -> MainAgentState:
    # Extract user profile data
    user_profile = state.get("user_profile", {})
    personal_values = user_profile.personal_values if user_profile else {}
    esg_preferences = personal_values.get("esg_preferences", {})
    
    # ACCESS USER ASSET PREFERENCES HERE:
    specific_assets = esg_preferences.get("specific_assets", [])
    # Example: ["AAPL", "MSFT", "TESLA", "VTI", "SPY"]
    
    user_avoid_industries = esg_preferences.get("avoid_industries", [])
    # Example: ["tobacco", "weapons", "fossil-fuels"]
    
    sectors = esg_preferences.get("prefer_industries", [])
    # Example: ["technology", "renewable-energy", "healthcare"]
    
    custom_constraints = esg_preferences.get("custom_constraints", "")
    # Example: "Focus on dividend-paying stocks"
    
    # Use these preferences in selection logic
    selection_result = run_selection_agent(
        regions=regions,
        sectors=sectors,
        specific_assets=specific_assets,  # Pass to selection agent
        filtered_tickers=filtered_tickers,
        filtered_weights=filtered_weights
    )
```

### 2. Portfolio Construction Agent Access
**File**: `backend/portfolio_construction_and_market_sentiment/portfolio_construction.py`

```python
def construct_portfolio_with_user_preferences(user_profile):
    personal_values = user_profile.get("personal_values", {})
    esg_preferences = personal_values.get("esg_preferences", {})
    
    # ACCESS SPECIFIC ASSETS
    user_specified_assets = esg_preferences.get("specific_assets", [])
    avoid_industries = esg_preferences.get("avoid_industries", [])
    prefer_industries = esg_preferences.get("prefer_industries", [])
    
    # Apply preferences to portfolio construction
    if user_specified_assets:
        # Prioritize user-specified assets
        prioritized_tickers = validate_and_prioritize_assets(user_specified_assets)
        
    # Filter out avoided industries
    if avoid_industries:
        filtered_universe = filter_by_industry_exclusion(ticker_universe, avoid_industries)
```

### 3. Risk Analytics Agent Access
**File**: `backend/risk_analytics_agent/risk_analytics_agent.py`

```python
def analyze_risk_with_preferences(self, user_profile):
    personal_values = user_profile.get("personal_values", {})
    esg_preferences = personal_values.get("esg_preferences", {})
    
    # ACCESS USER PREFERENCES FOR RISK ANALYSIS
    specific_assets = esg_preferences.get("specific_assets", [])
    
    # Analyze risk of user-specified assets
    if specific_assets:
        user_asset_risks = self.analyze_specific_asset_risks(specific_assets)
        # Incorporate into overall risk assessment
```

### 4. Communication Agent Access
**File**: `backend/communication_agent.py`

```python
def generate_report_with_preferences(self, user_profile):
    personal_values = user_profile.get("personal_values", {})
    esg_preferences = personal_values.get("esg_preferences", {})
    
    # ACCESS FOR REPORT GENERATION
    specific_assets = esg_preferences.get("specific_assets", [])
    custom_constraints = esg_preferences.get("custom_constraints", "")
    
    # Include in report explanations
    if specific_assets:
        rationale += f"Per your request, we prioritized {', '.join(specific_assets)} in the analysis."
```

## State Management Access

### MainAgentState Structure
```python
class MainAgentState(TypedDict):
    user_profile: UserProfile  # Contains all preference data
    # ... other fields
```

### UserProfile Dataclass
```python
@dataclass
class UserProfile:
    personal_values: Dict[str, Any]  # Contains esg_preferences with specific_assets
    # ... other fields
```

## Practical Implementation Examples

### Example 1: Selection Agent Using Specific Assets
```python
# In selection_agent.py
def process_with_user_assets(specific_assets, portfolio_universe):
    validated_assets = []
    
    for asset in specific_assets:
        if validate_ticker(asset):  # Check if ticker is real and tradeable
            validated_assets.append(asset)
            logger.info(f"User-specified asset {asset} validated and prioritized")
        else:
            logger.warning(f"User-specified asset {asset} not found or not tradeable")
    
    # Prioritize validated user assets in portfolio construction
    priority_weights = calculate_priority_weights(validated_assets)
    return priority_weights
```

### Example 2: Portfolio Construction with Industry Filters
```python
# In portfolio_construction.py
def apply_esg_filters(ticker_universe, esg_preferences):
    avoid_industries = esg_preferences.get("avoid_industries", [])
    prefer_industries = esg_preferences.get("prefer_industries", [])
    specific_assets = esg_preferences.get("specific_assets", [])
    
    filtered_universe = ticker_universe.copy()
    
    # Remove tickers from avoided industries
    if avoid_industries:
        filtered_universe = exclude_by_industry(filtered_universe, avoid_industries)
    
    # Boost weight for preferred industries
    if prefer_industries:
        filtered_universe = boost_preferred_industries(filtered_universe, prefer_industries)
    
    # Ensure user-specified assets are included (if valid)
    if specific_assets:
        filtered_universe = ensure_user_assets_included(filtered_universe, specific_assets)
    
    return filtered_universe
```

## Testing Access Patterns

### Test User Profile with Specific Assets
```python
test_user_profile = {
    "personal_values": {
        "esg_preferences": {
            "specific_assets": ["AAPL", "MSFT", "VTI", "SPY"],
            "avoid_industries": ["tobacco", "weapons"],
            "prefer_industries": ["technology", "renewable-energy"],
            "custom_constraints": "Focus on dividend-paying stocks with strong ESG ratings"
        }
    }
}

# Any agent can access like this:
specific_assets = test_user_profile["personal_values"]["esg_preferences"]["specific_assets"]
# Result: ["AAPL", "MSFT", "VTI", "SPY"]
```

## Summary

**Where**: User preferences are stored in `user_profile.personal_values.esg_preferences`

**How**: All agents access via the `MainAgentState` passed through the workflow

**What's Available**:
- `specific_assets`: User-specified stock tickers/assets
- `avoid_industries`: Industries to exclude
- `prefer_industries`: Industries to prioritize  
- `custom_constraints`: Free-text investment constraints

**Key Files Updated**:
1. `backend/simple_main.py` - Added `specificAssets` to Values model
2. `backend/profile_processor.py` - Added specific assets extraction
3. `backend/main_agent.py` - Added specific assets access in Selection Agent node

This ensures that user asset and stock preferences flow seamlessly from frontend input through to all backend agents for personalized portfolio construction.