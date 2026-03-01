"""
Utilities for normalizing user uploads (images or PDFs) into vision-friendly PNG bytes.
"""

from __future__ import annotations

import io
from typing import Tuple

import fitz  # PyMuPDF
from PIL import Image

MAX_IMAGE_SIZE: Tuple[int, int] = (2000, 2000)
PDF_HEADER = b"%PDF"


def document_bytes_to_image(image_bytes: bytes) -> bytes:
    """
    Convert uploaded bytes (PNG/JPG/PDF) to a normalized PNG byte string.

    Args:
        image_bytes: Raw bytes from the uploaded file

    Returns:
        PNG bytes ready for base64 encoding / Vision API usage
    """
    if image_bytes.startswith(PDF_HEADER):
        return _pdf_page_to_png(image_bytes)
    return _normalize_image_bytes(image_bytes)


def _pdf_page_to_png(pdf_bytes: bytes, dpi: int = 150) -> bytes:
    """
    Render the first page of a PDF to PNG bytes.
    Reduced DPI from 180 to 150 to decrease image size while maintaining readability.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = doc.load_page(0)
        scale = dpi / 72
        matrix = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        png_bytes = pix.tobytes("png")
        
        # Further compress and resize if needed using PIL
        return _normalize_image_bytes(png_bytes)
    finally:
        doc.close()


def _normalize_image_bytes(image_bytes: bytes) -> bytes:
    """
    Ensure the uploaded image fits size/color constraints and return as PNG.
    """
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    if image.size[0] > MAX_IMAGE_SIZE[0] or image.size[1] > MAX_IMAGE_SIZE[1]:
        image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()

