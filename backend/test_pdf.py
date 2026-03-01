"""
Test PDF processing with the actual PDF file
"""
import sys
from pathlib import Path
import traceback

sys.path.insert(0, str(Path(__file__).parent))

from agents.image_utils import document_bytes_to_image

def test_pdf_processing():
    """Test if PDF can be converted to image"""
    pdf_path = Path("/Users/durgamaheshboppani/Desktop/MAS/Training Data/GAINESVILLE SEAFOOD AND CHICKEN A2 (1).pdf")
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return False
    
    print(f"✓ PDF found: {pdf_path.name}")
    print(f"  Size: {pdf_path.stat().st_size / 1024:.1f} KB")
    
    try:
        # Read PDF bytes
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        print(f"\n✓ Read {len(pdf_bytes)} bytes")
        print(f"  PDF header check: {pdf_bytes[:4]}")
        
        # Convert to image
        print("\n🔄 Converting PDF to image...")
        image_bytes = document_bytes_to_image(pdf_bytes)
        
        print(f"✓ Converted successfully!")
        print(f"  Image size: {len(image_bytes)} bytes ({len(image_bytes)/1024:.1f} KB)")
        
        # Save test output
        output_path = Path("test_pdf_output.png")
        with open(output_path, 'wb') as f:
            f.write(image_bytes)
        print(f"✓ Saved test image to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_processing()
    sys.exit(0 if success else 1)
