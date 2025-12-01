"""
Test validation with the PDF file
"""
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))

from agents.optimized_orchestrator import OptimizedRoofValidator

load_dotenv()

def test_pdf_validation():
    """Test validation with PDF"""
    print("\n" + "="*80)
    print("TESTING PDF VALIDATION")
    print("="*80)
    
    # Initialize validator
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found")
        return
    
    print(f"\n✓ API Key loaded: {api_key[:8]}...")
    
    validator = OptimizedRoofValidator(
        openai_api_key=api_key,
        api_base="https://api.openai.com/v1",
        main_model="gpt-5.1",
        summary_model="gpt-5-mini"
    )
    
    print("✓ Validator initialized")
    
    # Load PDF
    pdf_path = Path("/Users/durgamaheshboppani/Desktop/MAS/Training Data/GAINESVILLE SEAFOOD AND CHICKEN A2 (1).pdf")
    if not pdf_path.exists():
        print(f"ERROR: {pdf_path} not found")
        return
    
    print(f"✓ PDF file found: {pdf_path.name}")
    print(f"  Size: {pdf_path.stat().st_size / 1024:.1f} KB")
    
    # Run validation
    print("\n" + "-"*80)
    print("STARTING VALIDATION...")
    print("-"*80)
    
    start_time = time.time()
    
    with open(pdf_path, 'rb') as f:
        result = validator.validate_roof_design_optimized(f, filename=pdf_path.name)
    
    elapsed = time.time() - start_time
    
    # Display results
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    
    print(f"\n⏱️  Processing Time: {elapsed:.2f} seconds")
    print(f"{'✓' if result.get('success') else '❌'} Success: {result.get('success', False)}")
    
    if result.get('success'):
        validation_report = result.get('validation_report', '')
        analysis = result.get('analysis', '')
        
        print(f"\n📊 Analysis length: {len(analysis)} chars")
        print(f"📄 Validation report length: {len(validation_report)} chars")
        
        if validation_report:
            print(f"\n📄 COMPLIANCE REPORT (first 1500 chars):")
            print("-"*80)
            print(validation_report[:1500])
            if len(validation_report) > 1500:
                print(f"\n... (report continues, total: {len(validation_report)} chars)")
        else:
            print("\n⚠️  No validation report generated")
        
        if analysis:
            print(f"\n📊 ANALYSIS EXCERPT (first 800 chars):")
            print("-"*80)
            print(analysis[:800])
            if len(analysis) > 800:
                print(f"\n... (analysis continues, total: {len(analysis)} chars)")
        else:
            print("\n⚠️  No analysis generated")
            
    else:
        print(f"\n❌ ERROR: {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    
    return result

if __name__ == "__main__":
    result = test_pdf_validation()
