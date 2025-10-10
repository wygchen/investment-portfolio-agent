#!/usr/bin/env python3
"""
Direct test of PDF generation functionality
"""

import sys
import os

# Add current directory to path so we can import from local files
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pdf_import():
    """Test if we can import the PDF generator"""
    try:
        from report_generator import UnifiedReportGenerator
        print("✅ Successfully imported UnifiedReportGenerator")
        return True
    except ImportError as e:
        print(f"❌ Failed to import UnifiedReportGenerator: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error importing: {e}")
        return False

def test_pdf_generation():
    """Test basic PDF generation"""
    try:
        from report_generator import UnifiedReportGenerator
        
        print("📄 Testing PDF generation...")
        
        test_data = {
            'riskTolerance': 'moderate',
            'timeHorizon': 10,
            'annualIncome': 75000,
            'monthlySavings': 1000,
            'goals': [{'id': 'retirement', 'label': 'Retirement', 'priority': 1}]
        }
        
        generator = UnifiedReportGenerator()
        print("📝 UnifiedReportGenerator created successfully")
        
        pdf_path = generator.generate_comprehensive_report(test_data)
        print(f"📊 PDF generated at: {pdf_path}")
        
        # Check if file exists
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"✅ PDF file exists, size: {file_size} bytes")
            return True
        else:
            print("❌ PDF file was not created")
            return False
            
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Testing PDF Generation Functionality")
    print("=" * 50)
    
    # Test 1: Import
    import_success = test_pdf_import()
    
    if import_success:
        # Test 2: Generation
        generation_success = test_pdf_generation()
        
        if generation_success:
            print("\n🎉 All tests passed! PDF generation is working.")
        else:
            print("\n💥 PDF generation failed.")
    else:
        print("\n💥 Cannot import PDF generator.")
    
    print("=" * 50)