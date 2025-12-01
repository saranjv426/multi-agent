"""
Test the roof validation system with sample.png
"""
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.optimized_orchestrator import OptimizedRoofValidator

load_dotenv()

def test_sample_validation():
    """Test validation with sample.png"""
    print("\n" + "="*80)
    print("TESTING ROOF VALIDATION SYSTEM")
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
    
    print("✓ Validator initialized with GPT-5.1")
    
    # Load sample file (can test with sample.png or sample1.png)
    sample_file = "sample1.png"  # Change to test different files
    sample_path = Path(f"/Users/durgamaheshboppani/Desktop/MAS/Training Data/{sample_file}")
    if not sample_path.exists():
        print(f"ERROR: {sample_path} not found")
        return
    
    print(f"✓ Sample file found: {sample_path.name}")
    print(f"  Size: {sample_path.stat().st_size / 1024:.1f} KB")
    
    # Run validation
    print("\n" + "-"*80)
    print("STARTING VALIDATION...")
    print("-"*80)
    
    start_time = time.time()
    
    with open(sample_path, 'rb') as f:
        result = validator.validate_roof_design_optimized(f, filename=sample_path.name)
    
    elapsed = time.time() - start_time
    
    # Display results
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    
    print(f"\n⏱️  Processing Time: {elapsed:.2f} seconds")
    print(f"✓ Success: {result.get('success', False)}")
    
    if result.get('success'):
        print(f"\n📄 COMPLIANCE REPORT:")
        print("-"*80)
        
        validation_report = result.get('validation_report', '')
        if validation_report:
            # Print first 2000 characters
            print(validation_report[:2000])
            if len(validation_report) > 2000:
                print(f"\n... (report continues, total length: {len(validation_report)} characters)")
        else:
            print("⚠️  No validation report generated")
        
        analysis = result.get('analysis', '')
        if analysis:
            print(f"\n📊 ANALYSIS EXCERPT (first 1000 chars):")
            print("-"*80)
            print(analysis[:1000])
            if len(analysis) > 1000:
                print(f"\n... (analysis continues)")
    else:
        print(f"\n❌ ERROR: {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    
    return result

if __name__ == "__main__":
    result = test_sample_validation()
