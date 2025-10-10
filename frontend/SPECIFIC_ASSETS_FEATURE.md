# Specific Assets Feature

## Overview
Added a new "Specific Assets & Stock Preferences" section to the Values Step in the investment assessment flow. This allows users to input specific assets they want considered for their portfolio.

## Changes Made

### 1. Updated UserProfile Type
**File:** `components/discovery-flow.tsx`
- Added `specificAssets: string[]` to the values object
- Initialized as empty array in the default profile state

### 2. Enhanced Values Step UI  
**File:** `app/assessment/values-step.tsx`
- Added new textarea input for specific assets
- Converts comma-separated input to uppercase array of asset symbols
- Added visual summary in the values overview with orange badges

### 3. Updated API Types
**File:** `lib/api.ts`
- Added `specific_assets?: string[]` to the esg_preferences interface

## User Experience

### Input Format
Users can enter assets in several formats:
- Individual tickers: `AAPL, MSFT, GOOGL`
- Mixed case (automatically converted to uppercase): `aapl, Tesla, btc`
- ETFs and other assets: `VTI, SPY, QQQ`
- Cryptocurrencies: `BTC, ETH`

### Example Data Output
When a user enters "aapl, msft, tesla, vti, spy" the system will store:
```json
{
  "values": {
    "specificAssets": ["AAPL", "MSFT", "TESLA", "VTI", "SPY"],
    "avoidIndustries": ["tobacco", "weapons"],
    "preferIndustries": ["renewable-energy", "technology"],
    "customConstraints": "Focus on dividend-paying stocks"
  }
}
```

## Selection Agent Integration
The selection agent can now access user-specified assets via:
```python
user_profile = request.json
specific_assets = user_profile.get("values", {}).get("specificAssets", [])
# specific_assets = ["AAPL", "MSFT", "TESLA", "VTI", "SPY"]

# Use this data to:
# 1. Prioritize these assets in portfolio construction
# 2. Research and validate the assets
# 3. Consider them alongside algorithmic recommendations
# 4. Ensure proper weighting and risk management
```

## Benefits for Portfolio Construction

1. **User Agency**: Users can specify must-have holdings
2. **Personalization**: Accommodates specific investment thesis or preferences  
3. **Flexibility**: Supports stocks, ETFs, crypto, or other asset types
4. **Selection Agent Enhancement**: Provides concrete starting points for portfolio construction
5. **Risk Management**: Selection agent can validate and properly weight user suggestions

## UI Features

- **Smart Input Processing**: Automatically uppercases and parses comma-separated values
- **Real-time Preview**: Shows parsed assets as badges in the summary
- **Visual Integration**: Orange badges distinguish user-specified assets from other preferences
- **Validation Ready**: Format prepared for backend validation and processing

## Next Steps for Backend Integration

The backend selection agent should:
1. Validate that specified tickers/assets are real and tradeable
2. Research fundamental data for user-specified assets  
3. Consider these assets as priority candidates in portfolio construction
4. Apply appropriate weighting and risk management
5. Provide rationale for inclusion/exclusion in final recommendations