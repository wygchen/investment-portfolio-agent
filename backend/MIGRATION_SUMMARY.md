# Migration Summary: specificAssets from List[str] to str

## Overview
Successfully migrated the `specificAssets` field from a list of strings (`List[str]`) to a single string (`str`) to enable better LLM parsing of natural language asset preferences.

## Motivation
The user requested this change to allow more natural input like "AAPL and TESLA" or "Apple, Microsoft, and some Bitcoin" instead of requiring structured array format. This makes it easier for LLM agents to parse and understand user asset preferences.

## Files Modified

### 1. **main.py**
- **Line 45**: Changed `specificAssets: List[str] = []` to `specificAssets: str = ""`
- **Purpose**: Primary API server data model update

### 2. **simple_main.py** 
- **Line 28**: Changed `specificAssets: List[str] = []` to `specificAssets: str = ""`
- **Purpose**: Alternative API server alignment with main server

### 3. **profile_processor.py**
- **Lines 126-127**: Updated `_extract_values()` function to handle string format
  - `"specific_assets": values_data.get('specificAssets', '')` (was `[]`)
  - Added comment: "# Now a string for LLM parsing"
- **Purpose**: Data transformation layer between frontend and agents

### 4. **main_agent.py**
- **Line 509**: Updated default value from `[]` to `""`
  - `specific_assets = esg_preferences.get("specific_assets", "")`
- **Added comment**: "# Extract user-specified specific assets (NEW!) - now as string for LLM parsing"
- **Lines 524-529**: Updated function call to pass `specific_assets` parameter
- **Purpose**: Main workflow coordinator passes user preferences to agents

### 5. **selection/selection_agent.py**
- **Line 63**: Added `specific_assets: Optional[str]` to `SelectionAgentState` TypedDict
- **Lines 476-481**: Updated `run_selection_agent()` function signature and docstring
- **Line 532**: Added `specific_assets` to initial workflow state
- **Lines 236-253**: Updated equity selection node to extract and log specific assets
- **Line 258**: Pass `specific_assets` to `run_equity_selection()` call
- **Purpose**: Selection workflow integration with user asset preferences

## Testing
Created and verified string format compatibility:
- ✅ Empty string defaults work
- ✅ Natural language input ("AAPL and TESLA") works
- ✅ Complex sentences work
- ✅ JSON serialization/deserialization works

## Impact
- **Frontend**: May need to be updated to send string instead of array (frontend compatibility check recommended)
- **LLM Agents**: Can now parse flexible natural language asset preferences
- **Data Flow**: Complete end-to-end string format support from API → Profile Processing → Agent Access
- **Backward Compatibility**: Breaking change - any existing array-based inputs will need migration

## Example Usage
```json
{
  "specificAssets": "AAPL and TESLA"
}
```

Instead of:
```json
{
  "specificAssets": ["AAPL", "TSLA"]  
}
```

## Next Steps
1. ✅ **Backend Migration**: Complete
2. 🔄 **Frontend Update**: May need to update frontend to send string format
3. 🔄 **Agent Enhancement**: LLM agents can now parse natural language asset input
4. 🔄 **Testing**: Full end-to-end testing with real user input recommended

## Benefits
- **User Experience**: More natural input for asset preferences
- **LLM Compatible**: Easier for AI agents to parse and understand user intent
- **Flexible**: Supports various natural language formats
- **Scalable**: Can handle complex user expressions about investment preferences