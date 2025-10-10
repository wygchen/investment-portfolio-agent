#!/usr/bin/env python3
"""
Minimal server to test PDF endpoint functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="PDF Test API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "PDF Test API", "status": "running"}

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
            'goals': [{'id': 'retirement', 'label': 'Retirement', 'priority': 1}]
        }
        
        generator = UnifiedReportGenerator()
        pdf_path = generator.generate_comprehensive_report(test_data)
        
        if os.path.exists(pdf_path):
            return {
                "status": "success",
                "message": "PDF generation test successful",
                "pdf_path": pdf_path,
                "pdf_size": os.path.getsize(pdf_path)
            }
        else:
            return {
                "status": "error",
                "message": "PDF file not found after generation"
            }
            
    except Exception as e:
        logger.error(f"PDF test failed: {str(e)}")
        return {
            "status": "error",
            "message": f"PDF test failed: {str(e)}"
        }

if __name__ == "__main__":
    print("🚀 Starting PDF Test Server...")
    print("📍 Server will be available at: http://localhost:8080")
    print("🔗 Test PDF endpoint: http://localhost:8080/api/test-pdf")
    
    uvicorn.run(
        app, 
        host="127.0.0.1",
        port=8080,
        log_level="info"
    )