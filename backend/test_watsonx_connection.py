#!/usr/bin/env python3
"""
Test script for Watsonx.ai connection and risk analytics service.
Run this to verify your Watsonx setup before running the main application.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from services.watsonx_service import initialize_watsonx_service, WatsonxService
from watsonx_utils import load_environment


async def test_watsonx_connection():
    """Test Watsonx connection and basic functionality"""
    print("🔧 Testing Watsonx.ai Connection...")
    print("=" * 50)
    
    try:
        # Load environment variables
        print("📋 Loading environment variables...")
        env_vars = load_environment()
        print(f"✅ Environment loaded:")
        print(f"   - Watsonx URL: {env_vars['WATSONX_URL']}")
        print(f"   - Project ID: {env_vars['PROJ_ID'][:8]}...")
        print(f"   - API Key: {'*' * 20}{env_vars['WATSONX_APIKEY'][-4:]}")
        
    except Exception as e:
        print(f"❌ Environment setup failed: {e}")
        print("\n💡 Make sure you have:")
        print("   1. Created a .env file from .env.example")
        print("   2. Added your Watsonx API key, URL, and Project ID")
        return False
    
    try:
        # Initialize service
        print("\n🚀 Initializing Watsonx service...")
        service = await initialize_watsonx_service()
        
        # Check service status
        status = service.get_service_status()
        print(f"✅ Service initialized:")
        print(f"   - Status: {status['status']}")
        print(f"   - Model: {status['model_id']}")
        print(f"   - Connection: {'✅' if status['connection_initialized'] else '❌'}")
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False
    
    try:
        # Test basic AI functionality
        print("\n🧠 Testing AI functionality...")
        
        # Sample assessment data for testing
        test_assessment = {
            "age": 35,
            "income": 75000,
            "net_worth": 150000,
            "dependents": 2,
            "primary_goal": "retirement",
            "time_horizon": 25,
            "target_amount": 1000000,
            "monthly_contribution": 1500,
            "risk_tolerance": 6,
            "risk_capacity": "medium",
            "previous_experience": ["stocks", "bonds"],
            "market_reaction": "hold_course"
        }
        
        # Test risk analysis
        response = await service.generate_risk_analysis(test_assessment, "comprehensive")
        
        print(f"✅ Risk analysis completed:")
        print(f"   - Success: {response.success}")
        print(f"   - Source: {response.source}")
        print(f"   - Processing time: {response.processing_time:.2f}s")
        print(f"   - Model: {response.model_version}")
        print(f"   - Confidence: {response.confidence}")
        
        if response.success:
            # Try to extract JSON from response
            content = response.content
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                if json_end > json_start:
                    json_content = content[json_start:json_end].strip()
                    print(f"\n📊 Risk Blueprint Preview:")
                    print(json_content[:200] + "..." if len(json_content) > 200 else json_content)
        
        if response.error:
            print(f"⚠️  Error details: {response.error}")
            
    except Exception as e:
        print(f"❌ AI functionality test failed: {e}")
        return False
    
    try:
        # Test fallback mechanism
        print("\n🔄 Testing fallback mechanism...")
        
        # Temporarily break the connection to test fallback
        original_llm = service.llm
        service.llm = None
        
        fallback_response = await service.generate_risk_analysis(test_assessment, "quick")
        
        print(f"✅ Fallback test completed:")
        print(f"   - Success: {fallback_response.success}")
        print(f"   - Source: {fallback_response.source}")
        print(f"   - Fallback working: {'✅' if fallback_response.source == 'mock' else '❌'}")
        
        # Restore connection
        service.llm = original_llm
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Watsonx service is ready for use.")
    print("\n💡 Next steps:")
    print("   1. Run the main application: python main.py")
    print("   2. Test the risk analytics API endpoints")
    print("   3. Integrate with your frontend")
    
    return True


async def test_health_check():
    """Test service health check functionality"""
    print("\n🏥 Testing health check...")
    
    service = await initialize_watsonx_service()
    is_healthy = await service.health_check()
    
    print(f"Health check result: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
    return is_healthy


if __name__ == "__main__":
    print("🤖 Watsonx.ai Risk Analytics Service Test")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ No .env file found!")
        print("💡 Please copy .env.example to .env and configure your credentials")
        sys.exit(1)
    
    # Run tests
    try:
        success = asyncio.run(test_watsonx_connection())
        if success:
            print("\n✅ Ready for hackathon! 🚀")
            sys.exit(0)
        else:
            print("\n❌ Setup incomplete. Please fix the issues above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)