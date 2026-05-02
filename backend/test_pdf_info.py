"""
Check PDF structure and pages
"""
import fitz
from pathlib import Path

PDF_PATH = Path(__file__).resolve().parents[1] / "Training Data" / "GAINESVILLE SEAFOOD AND CHICKEN A2 (1).pdf"


def test_pdf_info():
    assert PDF_PATH.exists(), f"PDF fixture not found: {PDF_PATH}"

    with fitz.open(PDF_PATH) as doc:
        print(f"PDF: {PDF_PATH.name}")
        print(f"Pages: {len(doc)}")
        print(f"Encrypted: {doc.is_encrypted}")
        print(f"Needs password: {doc.needs_pass}")

        assert len(doc) > 0
        assert not doc.is_encrypted

        for i, page in enumerate(doc):
            print(f"\nPage {i+1}:")
            print(f"  Size: {page.rect.width:.1f} x {page.rect.height:.1f}")
            print(f"  Rotation: {page.rotation}")
            text = page.get_text()[:200]
            preview = text[:100] if text.strip() else "No text (image-based)"
            print(f"  Text preview: {preview}")
