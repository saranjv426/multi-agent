"""
Check PDF structure and pages
"""
import fitz
from pathlib import Path

pdf_path = Path("/Users/durgamaheshboppani/Desktop/MAS/Training Data/GAINESVILLE SEAFOOD AND CHICKEN A2 (1).pdf")

doc = fitz.open(pdf_path)
print(f"PDF: {pdf_path.name}")
print(f"Pages: {len(doc)}")
print(f"Encrypted: {doc.is_encrypted}")
print(f"Needs password: {doc.needs_pass}")

for i, page in enumerate(doc):
    print(f"\nPage {i+1}:")
    print(f"  Size: {page.rect.width:.1f} x {page.rect.height:.1f}")
    print(f"  Rotation: {page.rotation}")
    text = page.get_text()[:200]
    print(f"  Text preview: {text[:100] if text.strip() else 'No text (image-based)'}")

doc.close()
