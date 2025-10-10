# Streaming API Implementation Guide

## Overview

This implementation provides a two-endpoint streaming solution for the Investment Portfolio Advisor API:

1. **`POST /api/validate-assessment`** - Quick validation endpoint
2. **`POST /api/generate-report/stream`** - Streaming workflow execution

## Architecture

```
Frontend Assessment Data
        ↓
POST /api/validate-assessment (< 100ms)
        ↓ (if valid)
POST /api/generate-report/stream (10-30s with real-time updates)
        ↓
Server-Sent Events Stream:
- profile_generated (20%)
- risk_analysis_started (30%)
- risk_analysis_complete (50%)
- portfolio_construction_started (60%)
- portfolio_construction_complete (75%)
- selection_started (80%)
- selection_complete (90%)
- communication_started (95%)
- final_report_complete (100%)
```

## API Endpoints

### 1. POST /api/validate-assessment

**Purpose**: Quick validation of assessment data without processing

**Request Body**:
```json
{
  "goals": [...],
  "timeHorizon": 15,
  "riskTolerance": "medium",
  "annualIncome": 75000,
  "monthlySavings": 2000,
  "totalDebt": 25000,
  "emergencyFundMonths": "6-12",
  "values": {...},
  "esgPrioritization": true,
  "marketSelection": ["US"]
}
```

**Success Response (200)**:
```json
{
  "status": "success",
  "message": "Assessment data is valid and ready for processing"
}
```

**Error Response (400)**:
```json
{
  "detail": {
    "message": "Validation failed",
    "errors": [
      "Risk tolerance is required",
      "Annual income must be greater than 0"
    ]
  }
}
```

### 2. POST /api/generate-report/stream

**Purpose**: Execute complete workflow with real-time streaming updates

**Request Body**: Same as validate-assessment

**Response**: Server-Sent Events (SSE) stream

**Event Format**:
```
data: {
  "event": "risk_analysis_complete",
  "timestamp": "2025-10-09T14:30:22Z",
  "data": {
    "progress": 50,
    "message": "Risk analysis completed successfully",
    "risk_blueprint": {...}
  }
}

```

## Stream Events

| Event | Progress | Description |
|-------|----------|-------------|
| `profile_generated` | 20% | User profile created |
| `risk_analysis_started` | 30% | Risk analysis begins |
| `risk_analysis_complete` | 50% | Risk analysis finished |
| `portfolio_construction_started` | 60% | Portfolio optimization begins |
| `portfolio_construction_complete` | 75% | Portfolio optimization finished |
| `selection_started` | 80% | Security selection begins |
| `selection_complete` | 90% | Security selection finished |
| `communication_started` | 95% | Final report generation begins |
| `final_report_complete` | 100% | Complete workflow finished |

## Error Handling

### Validation Errors (400)
- Missing required fields
- Invalid data types
- Negative values where not allowed

### Workflow Errors (500)
- MainAgent execution failures
- Agent dependency issues
- Timeout errors

### Stream Events for Errors
```json
{
  "event": "workflow_error",
  "data": {
    "message": "Risk analysis failed: ...",
    "type": "workflow_error"
  }
}
```

## Frontend Integration

### JavaScript EventSource Example

```javascript
async function generateReport(assessmentData) {
    // Step 1: Validate
    const validateResponse = await fetch('/api/validate-assessment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(assessmentData)
    });
    
    if (!validateResponse.ok) {
        throw new Error('Validation failed');
    }
    
    // Step 2: Stream workflow
    const streamResponse = await fetch('/api/generate-report/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(assessmentData)
    });
    
    const reader = streamResponse.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const eventData = JSON.parse(line.substring(6));
                handleStreamEvent(eventData);
            }
        }
    }
}

function handleStreamEvent(eventData) {
    const { event, data } = eventData;
    const progress = data.progress || 0;
    
    updateProgressBar(progress);
    
    switch (event) {
        case 'final_report_complete':
            displayReport(data.final_report);
            break;
        case 'error':
            showError(data.message);
            break;
        // Handle other events...
    }
}
```

## Testing

### 1. Python Test Script
```bash
cd backend
python test_streaming_api.py
```

### 2. HTML Test Interface
Open `test_streaming_frontend.html` in browser with backend running

### 3. Manual cURL Testing

Validate assessment:
```bash
curl -X POST http://localhost:8003/api/validate-assessment \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

Stream report:
```bash
curl -X POST http://localhost:8003/api/generate-report/stream \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

## Key Implementation Features

### 1. Server-Sent Events (SSE)
- Uses `FastAPI.StreamingResponse`
- Proper CORS headers for browser compatibility
- JSON-formatted event data

### 2. Workflow Streaming
- Simulated streaming for current MainAgent implementation
- Progress tracking with percentage completion
- Graceful error handling with fallback reports

### 3. Error Recovery
- Validation errors return immediately
- Workflow errors trigger fallback report generation
- All errors include descriptive messages

### 4. Future Enhancement Points
- True LangGraph astream integration when available
- Real-time agent state streaming
- WebSocket alternative for bi-directional communication
- Progress persistence for long-running workflows

## Performance Characteristics

- **Validation**: ~50-100ms
- **Profile Generation**: ~200-500ms
- **Complete Workflow**: ~10-30 seconds
- **Fallback Mode**: ~1-2 seconds
- **Memory Usage**: Minimal (streaming prevents large response buffering)

## Security Considerations

- Input validation on all endpoints
- CORS configuration for frontend access
- Error message sanitization
- Rate limiting recommended for production

## Production Deployment Notes

1. Add rate limiting for streaming endpoints
2. Implement request timeout handling
3. Add authentication/authorization
4. Monitor stream connection counts
5. Consider WebSocket upgrade for heavy usage
6. Add metrics collection for workflow performance