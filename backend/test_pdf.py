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
    pdf_path = Path(__file__).resolve().parents[1] / "Training Data" / "GAINESVILLE SEAFOOD AND CHICKEN A2 (1).pdf"
    
    assert pdf_path.exists(), f"PDF not found: {pdf_path}"
    
    print(f"✓ PDF found: {pdf_path.name}")
    print(f"  Size: {pdf_path.stat().st_size / 1024:.1f} KB")
    
    try:
        # Read PDF bytes
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        print(f"\n✓ Read {len(pdf_bytes)} bytes")
        print(f"  PDF header check: {pdf_bytes[:4]}")
        assert pdf_bytes[:4] == b"%PDF"
        
        # Convert to image
        print("\n🔄 Converting PDF to image...")
        image_bytes = document_bytes_to_image(pdf_bytes)
        
        print(f"✓ Converted successfully!")
        print(f"  Image size: {len(image_bytes)} bytes ({len(image_bytes)/1024:.1f} KB)")
        assert image_bytes.startswith(b"\x89PNG")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"\nFull traceback:")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    test_pdf_processing()
