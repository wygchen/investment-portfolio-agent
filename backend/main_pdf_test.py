#!/usr/bin/env python3
"""
Standalone PDF test for main.py - minimal dependencies
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Investment Portfolio Advisor API - PDF Test Mode",
    description="Minimal API for testing PDF generation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Investment Portfolio Backend API - PDF Test Mode", 
        "status": "active",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Backend server is running"}

@app.get("/api/test-pdf")
async def test_pdf_generation():
    """Test endpoint to verify PDF generation works"""
    try:
        logger.info("Testing PDF generation...")
        
        # Import here to avoid loading dependencies at startup
        from report_generator import UnifiedReportGenerator
        
        test_data = {
            'riskTolerance': 'moderate',
            'timeHorizon': 10,
            'annualIncome': 75000,
            'monthlySavings': 1000,
            'goals': [{'id': 'retirement', 'label': 'Retirement', 'priority': 1}],
            'values': {
                'avoidIndustries': ['tobacco'],
                'preferIndustries': ['technology'],
                'specificAssets': 'AAPL and MSFT'  # Test the new string format
            }
        }
        
        generator = UnifiedReportGenerator()
        pdf_path = generator.generate_comprehensive_report(test_data)
        
        import os
        if os.path.exists(pdf_path):
            return {
                "status": "success",
                "message": "PDF generation test successful",
                "pdf_path": pdf_path,
                "pdf_size": os.path.getsize(pdf_path),
                "test_data_used": test_data
            }
        else:
            return {
                "status": "error",
                "message": "PDF file not found after generation"
            }
            
    except Exception as e:
        logger.error(f"PDF test failed: {str(e)}")
        import traceback
        return {
            "status": "error",
            "message": f"PDF test failed: {str(e)}",
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    print("🚀 Starting Investment Portfolio Backend - PDF Test Mode...")
    print("📍 Server will be available at: http://localhost:8002")
    print("🔗 PDF Test: http://localhost:8002/api/test-pdf")
    
    uvicorn.run(
        app, 
        host="127.0.0.1",
        port=8002,
        log_level="info"
    )