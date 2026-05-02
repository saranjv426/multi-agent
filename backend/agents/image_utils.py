"""
Utilities for normalizing user uploads (images or PDFs) into vision-friendly PNG bytes.
"""

from __future__ import annotations

import io
import re
import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Iterable, Literal

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover - handled at runtime if PDF support is unavailable
    fitz = None

from PIL import Image, ImageFilter

MAX_IMAGE_SIZE: Tuple[int, int] = (4096, 4096)
MIN_VISION_LONG_EDGE = 2200
PDF_HEADER = b"%PDF"
CONTENT_THRESHOLD = 242
MIN_REGION_AREA_RATIO = 0.015
MIN_REGION_WIDTH_RATIO = 0.18
MIN_REGION_HEIGHT_RATIO = 0.12
MAX_DETECTION_SIZE: Tuple[int, int] = (1600, 1600)
MAX_SPLIT_DEPTH = 6
MAX_REFINEMENT_DEPTH = 3
CONTENT_PADDING = 24
PDF_DRAWING_TITLE_PADDING_TOP = 40
PDF_DRAWING_TITLE_PADDING_BOTTOM = 180
PDF_DRAWING_TITLE_PADDING_SIDE = 36
GRID_GAP_CONTENT_RATIO = 0.012
LOW_DENSITY_GAP_RATIO = 0.14
INTERNAL_SPLIT_DENSITY_RATIO = 0.22
MAX_REGION_REFINEMENT_CHILDREN = 12
STRONG_LINE_RATIO = 0.68
COMPONENT_DILATION_SIZE = 3
COMPONENT_MIN_PIXEL_RATIO = 0.0015
COMPONENT_MIN_BOX_AREA_RATIO = 0.02
COMPONENT_MAX_BOX_AREA_RATIO = 0.18
TITLE_PADDING_X = 36
TITLE_PADDING_TOP = 96
TITLE_PADDING_BOTTOM = 28
TITLE_VERTICAL_TOLERANCE = 84
TITLE_MIN_CHARS = 6
TITLE_MAX_WORD_GAP = 42
MAX_SINGLE_REGION_AREA_RATIO = 0.82
MAX_SINGLE_REGION_WIDTH_RATIO = 0.92
MAX_SINGLE_REGION_HEIGHT_RATIO = 0.92
DRAWING_TITLE_PATTERN = re.compile(
    r"\b("
    r"roof|plan|section|detail|eave|ridge|framing|truss|rafter|parapet|soffit|fascia|"
    r"flashing|coping|dormer|gable|hip|valley|canopy"
    r")\b",
    re.IGNORECASE,
)
NON_DRAWING_TITLE_PATTERN = re.compile(
    r"\b(sheet|scale|project|revision|general notes|legend|title|architect|consultant)\b",
    re.IGNORECASE,
)
WALL_SECTION_TITLE_PATTERN = re.compile(r"\bwall\b", re.IGNORECASE)
ExtractionMode = Literal["wall-sections", "direct"]


@dataclass
class ExtractedDrawing:
    image_bytes: bytes
    page_number: int
    drawing_index: int
    source_kind: str
    bbox: Optional[Tuple[int, int, int, int]] = None

    @property
    def label(self) -> str:
        if self.source_kind == "pdf":
            return f"Page {self.page_number} Drawing {self.drawing_index}"
        return "Drawing 1"


@dataclass
class ExtractionPageDiagnostics:
    page_number: int
    title_region_count: int
    refined_title_region_count: int
    image_region_count: int
    fused_region_count: int
    selected_region_count: int
    strategy: str


def _page_diagnostics_to_dict(diagnostics: ExtractionPageDiagnostics) -> Dict[str, int | str]:
    return {
        "page_number": diagnostics.page_number,
        "title_region_count": diagnostics.title_region_count,
        "refined_title_region_count": diagnostics.refined_title_region_count,
        "image_region_count": diagnostics.image_region_count,
        "fused_region_count": diagnostics.fused_region_count,
        "selected_region_count": diagnostics.selected_region_count,
        "strategy": diagnostics.strategy,
    }


def document_bytes_to_image(
    image_bytes: bytes,
    extraction_mode: ExtractionMode = "wall-sections",
) -> bytes:
    """
    Convert uploaded bytes (PNG/JPG/PDF) to a normalized PNG byte string.
    """
    drawings = extract_document_drawings(image_bytes, extraction_mode=extraction_mode)
    return drawings[0].image_bytes


def extract_document_drawings(
    image_bytes: bytes,
    extraction_mode: ExtractionMode = "wall-sections",
) -> List[ExtractedDrawing]:
    """
    Extract one or more drawing crops from an uploaded image or PDF.
    """
    drawings, _diagnostics = extract_document_drawings_with_diagnostics(
        image_bytes,
        extraction_mode=extraction_mode,
    )
    return drawings


def extract_document_drawings_with_diagnostics(
    image_bytes: bytes,
    extraction_mode: ExtractionMode = "wall-sections",
) -> Tuple[List[ExtractedDrawing], Dict[str, object]]:
    """
    Extract one or more drawing crops and return lightweight diagnostics describing
    how the document was segmented.
    """
    start_time = time.time()
    if image_bytes.startswith(PDF_HEADER):
        if extraction_mode == "direct":
            drawings, diagnostics = _extract_pdf_pages_direct_with_diagnostics(image_bytes)
        else:
            drawings, diagnostics = _extract_pdf_drawings_with_diagnostics(image_bytes)
        diagnostics["extraction_time"] = time.time() - start_time
        return drawings, diagnostics

    normalized_image = _normalize_image_bytes(image_bytes)
    if extraction_mode == "direct":
        drawings = [
            ExtractedDrawing(
                image_bytes=normalized_image,
                page_number=1,
                drawing_index=1,
                source_kind="image",
            )
        ]
        strategy = "single-image-direct"
    else:
        drawings = _extract_drawings_from_page(
            normalized_image,
            page_number=1,
            source_kind="image",
        )
        strategy = "image-drawings" if len(drawings) > 1 else "single-image"

    return drawings, {
        "source_kind": "image",
        "extraction_mode": extraction_mode,
        "render_dpi": None,
        "pages": [{
            "page_number": 1,
            "title_region_count": 0,
            "refined_title_region_count": 0,
            "image_region_count": len(drawings),
            "fused_region_count": len(drawings),
            "selected_region_count": len(drawings),
            "strategy": strategy,
        }],
        "total_drawings": len(drawings),
        "extraction_time": time.time() - start_time,
    }


def _pdf_to_page_images(pdf_bytes: bytes, dpi: int = 160) -> List[bytes]:
    if fitz is None:
        raise RuntimeError("PyMuPDF is required for PDF uploads but is not installed")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        page_images: List[bytes] = []
        scale = dpi / 72
        matrix = fitz.Matrix(scale, scale)
        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            page_images.append(pix.tobytes("png"))
        return page_images
    finally:
        doc.close()


def _extract_pdf_drawings(pdf_bytes: bytes, dpi: int = 160) -> List[ExtractedDrawing]:
    drawings, _diagnostics = _extract_pdf_drawings_with_diagnostics(pdf_bytes, dpi=dpi)
    return drawings


def _extract_pdf_drawings_with_diagnostics(
    pdf_bytes: bytes,
    dpi: int = 160,
) -> Tuple[List[ExtractedDrawing], Dict[str, object]]:
    if fitz is None:
        raise RuntimeError("PyMuPDF is required for PDF uploads but is not installed")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        try:
            page_images = _pdf_to_page_images(pdf_bytes, dpi=dpi)
        except TypeError as exc:
            if "dpi" not in str(exc):
                raise
            page_images = _pdf_to_page_images(pdf_bytes)
        drawings: List[ExtractedDrawing] = []
        page_diagnostics: List[Dict[str, object]] = []
        for page_index, page_image in enumerate(page_images, start=1):
            page_drawings = _extract_drawings_from_page(
                page_image,
                page_number=page_index,
                source_kind="pdf",
            )
            drawings.extend(page_drawings)
            page_diagnostics.append({
                "page_number": page_index,
                "title_region_count": 0,
                "refined_title_region_count": 0,
                "image_region_count": len(page_drawings),
                "fused_region_count": len(page_drawings),
                "selected_region_count": len(page_drawings),
                "strategy": "rendered-page-image-drawings" if len(page_drawings) > 1 else "rendered-page-image",
            })

        return drawings, {
            "source_kind": "pdf",
            "extraction_mode": "wall-sections",
            "render_dpi": dpi,
            "pages": page_diagnostics,
            "total_drawings": len(drawings),
        }

    try:
        drawings: List[ExtractedDrawing] = []
        page_diagnostics: List[Dict[str, object]] = []
        scale = dpi / 72
        matrix = fitz.Matrix(scale, scale)
        for page_number in range(1, doc.page_count + 1):
            page = doc.load_page(page_number - 1)
            page_drawings, diagnostics = _extract_drawings_from_pdf_page_with_diagnostics(
                page,
                page_number=page_number,
                matrix=matrix,
            )
            drawings.extend(page_drawings)
            page_diagnostics.append(_page_diagnostics_to_dict(diagnostics))

        if drawings:
            return drawings, {
                "source_kind": "pdf",
                "extraction_mode": "wall-sections",
                "render_dpi": dpi,
                "pages": page_diagnostics,
                "total_drawings": len(drawings),
            }

        page_images = [doc.load_page(index).get_pixmap(matrix=matrix, alpha=False).tobytes("png") for index in range(doc.page_count)]
        drawings = [
            ExtractedDrawing(
                image_bytes=_normalize_image_bytes(page_images[0]),
                page_number=1,
                drawing_index=1,
                source_kind="pdf",
            )
        ]
        page_diagnostics.append({
            "page_number": 1,
            "title_region_count": 0,
            "refined_title_region_count": 0,
            "image_region_count": 1,
            "fused_region_count": 0,
            "selected_region_count": 1,
            "strategy": "full-page-fallback",
        })
        return drawings, {
            "source_kind": "pdf",
            "extraction_mode": "wall-sections",
            "render_dpi": dpi,
            "pages": page_diagnostics,
            "total_drawings": len(drawings),
        }
    finally:
        doc.close()


def _extract_pdf_pages_direct_with_diagnostics(
    pdf_bytes: bytes,
    dpi: int = 160,
) -> Tuple[List[ExtractedDrawing], Dict[str, object]]:
    page_images = _pdf_to_page_images(pdf_bytes, dpi=dpi)
    drawings = [
        ExtractedDrawing(
            image_bytes=_normalize_image_bytes(page_image),
            page_number=page_index + 1,
            drawing_index=1,
            source_kind="pdf",
        )
        for page_index, page_image in enumerate(page_images)
    ]
    return drawings, {
        "source_kind": "pdf",
        "extraction_mode": "direct",
        "render_dpi": dpi,
        "pages": [
            {
                "page_number": page_index + 1,
                "title_region_count": 0,
                "refined_title_region_count": 0,
                "image_region_count": 1,
                "fused_region_count": 1,
                "selected_region_count": 1,
                "strategy": "full-page-direct",
            }
            for page_index in range(len(page_images))
        ],
        "total_drawings": len(drawings),
    }


def _extract_drawings_from_pdf_page(page, page_number: int, matrix) -> List[ExtractedDrawing]:
    drawings, _diagnostics = _extract_drawings_from_pdf_page_with_diagnostics(
        page,
        page_number=page_number,
        matrix=matrix,
    )
    return drawings


def _extract_drawings_from_pdf_page_with_diagnostics(
    page,
    page_number: int,
    matrix,
) -> Tuple[List[ExtractedDrawing], ExtractionPageDiagnostics]:
    title_boxes = _find_drawing_title_boxes(page)
    wall_title_boxes = _filter_wall_section_title_boxes(title_boxes)
    use_wall_only_titles = len(wall_title_boxes) > 0
    if use_wall_only_titles and len(wall_title_boxes) < len(title_boxes):
        titled_regions = _regions_for_selected_titles(title_boxes, wall_title_boxes, page.rect.width, page.rect.height)
    else:
        try:
            titled_regions = _extract_titled_regions_from_pdf_page(
                page,
                title_boxes=wall_title_boxes if use_wall_only_titles else title_boxes,
            )
        except TypeError as exc:
            if "title_boxes" not in str(exc):
                raise
            titled_regions = _extract_titled_regions_from_pdf_page(page)
    title_region_count = len(titled_regions)
    page_pix = page.get_pixmap(matrix=matrix, alpha=False)
    page_png = page_pix.tobytes("png")
    image_drawings = _extract_drawings_from_page(page_png, page_number=page_number)
    image_region_count = len(image_drawings)
    titled_regions = _refine_pdf_region_bboxes(page_png, titled_regions, page, matrix)
    refined_title_region_count = len(titled_regions)
    fused_regions = _fuse_pdf_regions(
        titled_regions,
        image_drawings,
        page,
        matrix,
        include_image_candidates=not use_wall_only_titles,
    )
    fused_region_count = len(fused_regions)
    if len(fused_regions) > 1 or (use_wall_only_titles and len(fused_regions) == 1):
        drawings: List[ExtractedDrawing] = []
        for drawing_index, bbox in enumerate(fused_regions, start=1):
            expanded_bbox = _expand_pdf_crop_bbox(
                bbox,
                page_width=page.rect.width,
                page_height=page.rect.height,
            )
            clip = fitz.Rect(*expanded_bbox)
            pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False)
            drawings.append(
                ExtractedDrawing(
                    image_bytes=_normalize_image_bytes(pix.tobytes("png")),
                    page_number=page_number,
                    drawing_index=drawing_index,
                    source_kind="pdf",
                    bbox=(
                        int(expanded_bbox[0]),
                        int(expanded_bbox[1]),
                        int(expanded_bbox[2]),
                        int(expanded_bbox[3]),
                    ),
                )
            )
        return drawings, ExtractionPageDiagnostics(
            page_number=page_number,
            title_region_count=title_region_count,
            refined_title_region_count=refined_title_region_count,
            image_region_count=image_region_count,
            fused_region_count=fused_region_count,
            selected_region_count=len(drawings),
            strategy="wall-title-regions" if use_wall_only_titles else "fused-regions",
        )

    if len(fused_regions) == 1:
        return [_build_full_page_pdf_drawing(page_png, page_number)], ExtractionPageDiagnostics(
            page_number=page_number,
            title_region_count=title_region_count,
            refined_title_region_count=refined_title_region_count,
            image_region_count=image_region_count,
            fused_region_count=fused_region_count,
            selected_region_count=1,
            strategy="single-drawing-page",
        )

    if len(image_drawings) > 1:
        return image_drawings, ExtractionPageDiagnostics(
            page_number=page_number,
            title_region_count=title_region_count,
            refined_title_region_count=refined_title_region_count,
            image_region_count=image_region_count,
            fused_region_count=fused_region_count,
            selected_region_count=len(image_drawings),
            strategy="image-drawings",
        )

    return [_build_full_page_pdf_drawing(page_png, page_number)], ExtractionPageDiagnostics(
        page_number=page_number,
        title_region_count=title_region_count,
        refined_title_region_count=refined_title_region_count,
        image_region_count=image_region_count,
        fused_region_count=fused_region_count,
        selected_region_count=1,
        strategy="single-page-original" if image_drawings else "full-page-fallback",
    )


def _build_full_page_pdf_drawing(page_png: bytes, page_number: int) -> ExtractedDrawing:
    image = Image.open(io.BytesIO(page_png))
    return ExtractedDrawing(
        image_bytes=_normalize_image_bytes(page_png),
        page_number=page_number,
        drawing_index=1,
        source_kind="pdf",
        bbox=(0, 0, image.width, image.height),
    )


def _expand_pdf_crop_bbox(
    bbox: Tuple[float, float, float, float],
    *,
    page_width: float,
    page_height: float,
) -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = bbox
    return (
        max(0.0, x0 - PDF_DRAWING_TITLE_PADDING_SIDE),
        max(0.0, y0 - PDF_DRAWING_TITLE_PADDING_TOP),
        min(page_width, x1 + PDF_DRAWING_TITLE_PADDING_SIDE),
        min(page_height, y1 + PDF_DRAWING_TITLE_PADDING_BOTTOM),
    )


def _fuse_pdf_regions(
    titled_regions: List[Tuple[float, float, float, float]],
    image_drawings: List[ExtractedDrawing],
    page,
    matrix,
    *,
    include_image_candidates: bool = True,
) -> List[Tuple[float, float, float, float]]:
    page_width = page.rect.width
    page_height = page.rect.height
    image_regions = _pdf_regions_from_image_drawings(image_drawings, matrix)

    candidates: List[Tuple[float, float, float, float]] = []
    candidates.extend(titled_regions)

    # Only trust image-based candidates when they look like a plausible panel set.
    if include_image_candidates and 1 < len(image_regions) <= 12:
        candidates.extend(image_regions)

    if not candidates:
        return []

    filtered = [
        region for region in candidates
        if _region_area_ratio(region, page_width, page_height) >= 0.025
    ]
    if not filtered:
        return []

    filtered = [
        region for region in filtered
        if not _region_is_composite_candidate(region, filtered)
    ]
    if not filtered:
        return []

    deduped: List[Tuple[float, float, float, float]] = []
    for candidate in sorted(filtered, key=lambda item: (_region_area(item), item[1], item[0])):
        if any(_region_contains(existing, candidate, padding=8.0) for existing in deduped):
            continue
        if any(_boxes_overlap(candidate, existing, overlap_ratio=0.85) for existing in deduped):
            continue
        deduped.append(candidate)

    deduped.sort(key=lambda item: (item[1], item[0]))
    return deduped


def _pdf_regions_from_image_drawings(
    image_drawings: List[ExtractedDrawing],
    matrix,
) -> List[Tuple[float, float, float, float]]:
    scale_x = getattr(matrix, "a", 1.0) or 1.0
    scale_y = getattr(matrix, "d", 1.0) or 1.0
    regions: List[Tuple[float, float, float, float]] = []

    for drawing in image_drawings:
        if not drawing.bbox:
            continue
        x0, y0, x1, y1 = drawing.bbox
        regions.append((
            x0 / scale_x,
            y0 / scale_y,
            x1 / scale_x,
            y1 / scale_y,
        ))

    return regions


def _refine_pdf_region_bboxes(
    page_png: bytes,
    regions: List[Tuple[float, float, float, float]],
    page,
    matrix,
) -> List[Tuple[float, float, float, float]]:
    if not regions:
        return []

    scale_x = getattr(matrix, "a", 1.0) or 1.0
    scale_y = getattr(matrix, "d", 1.0) or 1.0
    page_image = Image.open(io.BytesIO(page_png))
    if page_image.mode != "RGB":
        page_image = page_image.convert("RGB")

    refined_regions: List[Tuple[float, float, float, float]] = []
    for region in regions:
        child_regions = _split_pdf_region_from_image(
            page_image,
            region,
            scale_x=scale_x,
            scale_y=scale_y,
            page_width=page.rect.width,
            page_height=page.rect.height,
        )
        if child_regions:
            refined_regions.extend(child_regions)
        else:
            refined_regions.append(region)

    deduped: List[Tuple[float, float, float, float]] = []
    for candidate in sorted(refined_regions, key=lambda item: (item[1], item[0])):
        if any(_boxes_overlap(candidate, existing, overlap_ratio=0.75) for existing in deduped):
            continue
        deduped.append(candidate)
    return deduped


def _split_pdf_region_from_image(
    page_image: Image.Image,
    region: Tuple[float, float, float, float],
    *,
    scale_x: float,
    scale_y: float,
    page_width: float,
    page_height: float,
) -> List[Tuple[float, float, float, float]]:
    x0, y0, x1, y1 = region
    region_width = x1 - x0
    region_height = y1 - y0
    if region_width <= 0 or region_height <= 0:
        return []

    page_area = max(1.0, page_width * page_height)
    region_area_ratio = (region_width * region_height) / page_area
    if region_area_ratio < 0.08:
        return []

    px_box = (
        max(0, int(x0 * scale_x)),
        max(0, int(y0 * scale_y)),
        min(page_image.width, int(x1 * scale_x)),
        min(page_image.height, int(y1 * scale_y)),
    )
    if (px_box[2] - px_box[0]) < 120 or (px_box[3] - px_box[1]) < 120:
        return []

    crop = page_image.crop(px_box)
    crop_mask = _build_content_mask(crop)
    crop_root = _trim_box(crop_mask, (0, 0, crop.width, crop.height))
    if crop_root is None:
        return []

    # Detail rows on architectural sheets often contain 4+ narrow panels.
    # Keep refinement permissive enough to split those merged regions.
    min_width = max(72, int(crop.width * 0.10))
    min_height = max(72, int(crop.height * 0.18))
    min_area = max(5000, int(crop.width * crop.height * 0.08))
    candidate_boxes = _refine_detected_boxes(
        crop_mask,
        [crop_root],
        min_width=min_width,
        min_height=min_height,
        min_area=min_area,
        depth=0,
    )
    candidate_boxes = [
        box for box in candidate_boxes
        if (box[2] - box[0]) >= min_width
        and (box[3] - box[1]) >= min_height
        and ((box[2] - box[0]) * (box[3] - box[1])) >= min_area
    ]
    component_boxes = [
        box for box in _detect_component_boxes(crop)
        if (box[2] - box[0]) >= min_width
        and (box[3] - box[1]) >= min_height
        and ((box[2] - box[0]) * (box[3] - box[1])) >= min_area
    ]
    if len(component_boxes) > len(candidate_boxes):
        candidate_boxes = component_boxes
    whitespace_panel_boxes = _split_region_by_whitespace_gaps(
        crop_mask,
        crop_root,
        min_width=min_width,
        min_height=min_height,
        min_area=min_area,
    )
    if len(whitespace_panel_boxes) > len(candidate_boxes):
        candidate_boxes = whitespace_panel_boxes
    if len(candidate_boxes) <= 1:
        candidate_boxes = _split_region_by_panel_lines(
            crop_mask,
            crop_root,
            min_width=min_width,
            min_height=min_height,
            min_area=min_area,
        )
    if not (1 < len(candidate_boxes) <= MAX_REGION_REFINEMENT_CHILDREN):
        return []

    refined_regions: List[Tuple[float, float, float, float]] = []
    for child_x0, child_y0, child_x1, child_y1 in sorted(candidate_boxes, key=lambda item: (item[1], item[0])):
        refined_regions.append((
            max(0.0, x0 + (child_x0 / scale_x)),
            max(0.0, y0 + (child_y0 / scale_y)),
            min(page_width, x0 + (child_x1 / scale_x)),
            min(page_height, y0 + (child_y1 / scale_y)),
        ))

    return refined_regions


def _split_region_by_whitespace_gaps(
    mask: List[List[int]],
    root_box: Tuple[int, int, int, int],
    *,
    min_width: int,
    min_height: int,
    min_area: int,
) -> List[Tuple[int, int, int, int]]:
    x0, y0, x1, y1 = root_box
    width = x1 - x0
    height = y1 - y0
    row_profile = [_row_sum(mask, y, x0, x1) for y in range(y0, y1)]
    col_profile = [_col_sum(mask, x, y0, y1) for x in range(x0, x1)]

    horizontal_gaps = _find_whitespace_runs(
        row_profile,
        start=y0,
        min_gap=max(12, int(height * 0.025)),
        max_content=max(2, int(width * 0.01)),
    )
    vertical_gaps = _find_whitespace_runs(
        col_profile,
        start=x0,
        min_gap=max(12, int(width * 0.015)),
        max_content=max(2, int(height * 0.01)),
    )

    candidates: List[List[Tuple[int, int, int, int]]] = []
    for axis, gaps in (("horizontal", horizontal_gaps), ("vertical", vertical_gaps)):
        if not gaps:
            continue
        if axis == "horizontal":
            segments = _segments_from_gaps(y0, y1, gaps, min_size=min_height)
            boxes = [_trim_box(mask, (x0, sy0, x1, sy1)) for sy0, sy1 in segments]
        else:
            segments = _segments_from_gaps(x0, x1, gaps, min_size=min_width)
            boxes = [_trim_box(mask, (sx0, y0, sx1, y1)) for sx0, sx1 in segments]
        valid = [
            box for box in boxes
            if box is not None
            and (box[2] - box[0]) >= min_width
            and (box[3] - box[1]) >= min_height
            and ((box[2] - box[0]) * (box[3] - box[1])) >= min_area
        ]
        if 1 < len(valid) <= MAX_REGION_REFINEMENT_CHILDREN:
            candidates.append(valid)

    if not candidates:
        return []
    candidates.sort(key=lambda boxes: (len(boxes), sum(_region_area(box) for box in boxes)), reverse=True)
    return candidates[0]


def _split_region_by_panel_lines(
    mask: List[List[int]],
    root_box: Tuple[int, int, int, int],
    *,
    min_width: int,
    min_height: int,
    min_area: int,
) -> List[Tuple[int, int, int, int]]:
    x0, y0, x1, y1 = root_box
    width = x1 - x0
    height = y1 - y0

    row_profile = [_row_sum(mask, y, x0, x1) for y in range(y0, y1)]
    col_profile = [_col_sum(mask, x, y0, y1) for x in range(x0, x1)]

    horizontal_lines = _find_strong_line_runs(
        row_profile,
        start=y0,
        min_run=max(2, int(height * 0.01)),
        threshold_ratio=STRONG_LINE_RATIO,
    )
    vertical_lines = _find_strong_line_runs(
        col_profile,
        start=x0,
        min_run=max(2, int(width * 0.01)),
        threshold_ratio=STRONG_LINE_RATIO,
    )

    horizontal_boxes = _boxes_from_line_splits(
        mask,
        root_box,
        horizontal_lines,
        axis="horizontal",
        min_width=min_width,
        min_height=min_height,
        min_area=min_area,
    )
    vertical_boxes = _boxes_from_line_splits(
        mask,
        root_box,
        vertical_lines,
        axis="vertical",
        min_width=min_width,
        min_height=min_height,
        min_area=min_area,
    )

    candidates = [horizontal_boxes, vertical_boxes]
    candidates = [boxes for boxes in candidates if 1 < len(boxes) <= MAX_REGION_REFINEMENT_CHILDREN]
    if not candidates:
        return []

    candidates.sort(key=lambda boxes: (len(boxes), sum(_region_area(box) for box in boxes)), reverse=True)
    return candidates[0]


def _find_strong_line_runs(
    profile: List[int],
    *,
    start: int,
    min_run: int,
    threshold_ratio: float,
) -> List[Tuple[int, int]]:
    if not profile:
        return []

    max_value = max(profile)
    if max_value <= 0:
        return []

    threshold = max_value * threshold_ratio
    runs: List[Tuple[int, int]] = []
    run_start: Optional[int] = None

    for idx, value in enumerate(profile):
        if value >= threshold:
            if run_start is None:
                run_start = idx
            continue

        if run_start is not None:
            run_end = idx
            if (run_end - run_start) >= min_run:
                runs.append((start + run_start, start + run_end))
            run_start = None

    if run_start is not None:
        run_end = len(profile)
        if (run_end - run_start) >= min_run:
            runs.append((start + run_start, start + run_end))

    return runs


def _boxes_from_line_splits(
    mask: List[List[int]],
    root_box: Tuple[int, int, int, int],
    line_runs: List[Tuple[int, int]],
    *,
    axis: str,
    min_width: int,
    min_height: int,
    min_area: int,
) -> List[Tuple[int, int, int, int]]:
    x0, y0, x1, y1 = root_box
    if len(line_runs) < 1:
        return []

    centers = [int((run_start + run_end) / 2) for run_start, run_end in line_runs]
    if axis == "horizontal":
        boundaries = [y0] + [center for center in centers if y0 < center < y1] + [y1]
        segments = []
        for start_y, end_y in zip(boundaries, boundaries[1:]):
            candidate = _trim_box(mask, (x0, start_y, x1, end_y))
            if candidate is None:
                continue
            cx0, cy0, cx1, cy1 = candidate
            if (cx1 - cx0) < min_width or (cy1 - cy0) < min_height:
                continue
            if (cx1 - cx0) * (cy1 - cy0) < min_area:
                continue
            segments.append(candidate)
        return segments

    boundaries = [x0] + [center for center in centers if x0 < center < x1] + [x1]
    segments = []
    for start_x, end_x in zip(boundaries, boundaries[1:]):
        candidate = _trim_box(mask, (start_x, y0, end_x, y1))
        if candidate is None:
            continue
        cx0, cy0, cx1, cy1 = candidate
        if (cx1 - cx0) < min_width or (cy1 - cy0) < min_height:
            continue
        if (cx1 - cx0) * (cy1 - cy0) < min_area:
            continue
        segments.append(candidate)
    return segments


def _extract_titled_regions_from_pdf_page(
    page,
    *,
    title_boxes: Optional[List[Tuple[float, float, float, float, str]]] = None,
) -> List[Tuple[float, float, float, float]]:
    if title_boxes is None:
        title_boxes = _find_drawing_title_boxes(page)
    if not title_boxes:
        return []

    page_rect = page.rect
    regions = _build_regions_from_titles(title_boxes, page_rect.width, page_rect.height)
    merged_regions = _merge_overlapping_regions(regions)

    # If merging collapses a multi-title page into one giant region, keep the
    # original title-derived regions and let downstream filtering handle them.
    if len(regions) > 1 and len(merged_regions) <= 1:
        return regions

    if len(merged_regions) < max(1, len(regions) // 2):
        return regions

    return merged_regions


def _filter_wall_section_title_boxes(
    title_boxes: List[Tuple[float, float, float, float, str]]
) -> List[Tuple[float, float, float, float, str]]:
    return [
        title_box
        for title_box in title_boxes
        if WALL_SECTION_TITLE_PATTERN.search(title_box[4])
    ]


def _should_use_titled_regions(
    regions: List[Tuple[float, float, float, float]],
    page_width: float,
    page_height: float,
) -> bool:
    if not regions:
        return False
    if len(regions) > 1:
        return True

    x0, y0, x1, y1 = regions[0]
    region_width = max(1.0, x1 - x0)
    region_height = max(1.0, y1 - y0)
    page_area = max(1.0, page_width * page_height)
    region_area_ratio = (region_width * region_height) / page_area
    region_width_ratio = region_width / max(1.0, page_width)
    region_height_ratio = region_height / max(1.0, page_height)

    return not (
        region_area_ratio >= MAX_SINGLE_REGION_AREA_RATIO
        or region_width_ratio >= MAX_SINGLE_REGION_WIDTH_RATIO
        or region_height_ratio >= MAX_SINGLE_REGION_HEIGHT_RATIO
    )


def _find_drawing_title_boxes(page) -> List[Tuple[float, float, float, float, str]]:
    title_boxes: List[Tuple[float, float, float, float, str]] = []
    for finder in (
        _find_block_level_title_boxes,
        _find_line_level_title_boxes,
        _find_word_cluster_title_boxes,
    ):
        try:
            title_boxes.extend(finder(page))
        except (AttributeError, TypeError):
            continue
    return _dedupe_title_boxes(title_boxes)


def _find_block_level_title_boxes(page) -> List[Tuple[float, float, float, float, str]]:
    text_blocks = page.get_text("blocks") or []
    title_boxes: List[Tuple[float, float, float, float, str]] = []

    for block in text_blocks:
        if len(block) < 5:
            continue
        x0, y0, x1, y1, text = block[:5]
        if not text:
            continue
        normalized = _normalize_title_text(str(text))
        if not _looks_like_drawing_title(normalized):
            continue
        title_boxes.append((float(x0), float(y0), float(x1), float(y1), normalized))

    return title_boxes


def _find_line_level_title_boxes(page) -> List[Tuple[float, float, float, float, str]]:
    text_dict = page.get_text("dict") or {}
    blocks = text_dict.get("blocks") or []
    title_boxes: List[Tuple[float, float, float, float, str]] = []

    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines") or []:
            spans = line.get("spans") or []
            if not spans:
                continue
            text = " ".join(str(span.get("text", "")) for span in spans)
            normalized = _normalize_title_text(text)
            if not _looks_like_drawing_title(normalized):
                continue

            x0 = min(float(span["bbox"][0]) for span in spans)
            y0 = min(float(span["bbox"][1]) for span in spans)
            x1 = max(float(span["bbox"][2]) for span in spans)
            y1 = max(float(span["bbox"][3]) for span in spans)
            title_boxes.append((x0, y0, x1, y1, normalized))

    return title_boxes


def _find_word_cluster_title_boxes(page) -> List[Tuple[float, float, float, float, str]]:
    words = page.get_text("words") or []
    if not words:
        return []

    title_boxes: List[Tuple[float, float, float, float, str]] = []
    sorted_words = sorted(words, key=lambda item: (float(item[1]), float(item[0])))
    line_clusters: List[List[Tuple[float, float, float, float, str]]] = []

    for word in sorted_words:
        x0, y0, x1, y1, text = word[:5]
        token = str(text).strip()
        if not token:
            continue
        placed = False
        for cluster in line_clusters:
            cluster_mid_y = sum((item[1] + item[3]) / 2 for item in cluster) / len(cluster)
            word_mid_y = (float(y0) + float(y1)) / 2
            cluster_x1 = max(item[2] for item in cluster)
            if abs(word_mid_y - cluster_mid_y) <= 8 and (float(x0) - cluster_x1) <= TITLE_MAX_WORD_GAP:
                cluster.append((float(x0), float(y0), float(x1), float(y1), token))
                placed = True
                break
        if not placed:
            line_clusters.append([(float(x0), float(y0), float(x1), float(y1), token)])

    for cluster in line_clusters:
        normalized = _normalize_title_text(" ".join(item[4] for item in cluster))
        if not _looks_like_drawing_title(normalized):
            continue
        x0 = min(item[0] for item in cluster)
        y0 = min(item[1] for item in cluster)
        x1 = max(item[2] for item in cluster)
        y1 = max(item[3] for item in cluster)
        title_boxes.append((x0, y0, x1, y1, normalized))

    return title_boxes


def _normalize_title_text(text: str) -> str:
    tokens = [token for token in str(text).replace("\n", " ").split() if token]
    if tokens and all(len(re.sub(r"[^A-Za-z0-9]", "", token)) == 1 for token in tokens):
        compact = "".join(re.sub(r"[^A-Za-z0-9]", "", token) for token in tokens).upper()
        title_words = (
            "TYPICAL",
            "EXISTING",
            "EXIST",
            "NEW",
            "ROOF",
            "FRAMING",
            "PLAN",
            "WALL",
            "SECTION",
            "DETAIL",
            "INT",
        )
        split_words: List[str] = []
        index = 0
        while index < len(compact):
            match = next((word for word in title_words if compact.startswith(word, index)), "")
            if not match:
                split_words = []
                break
            split_words.append(match)
            index += len(match)
        if split_words:
            return " ".join(split_words)

    merged_tokens: List[str] = []
    index = 0

    while index < len(tokens):
        token = tokens[index]
        cleaned = re.sub(r"[^A-Za-z0-9]", "", token)
        if len(cleaned) == 1 and cleaned.isalpha():
            letters = [cleaned]
            next_index = index + 1
            while next_index < len(tokens):
                next_clean = re.sub(r"[^A-Za-z0-9]", "", tokens[next_index])
                if len(next_clean) == 1 and next_clean.isalpha():
                    letters.append(next_clean)
                    next_index += 1
                    continue
                break
            if len(letters) >= 3:
                merged_tokens.append("".join(letters))
                index = next_index
                continue
        merged_tokens.append(token)
        index += 1

    return " ".join(merged_tokens)


def _looks_like_drawing_title(normalized: str) -> bool:
    if len(normalized) < TITLE_MIN_CHARS:
        return False
    if NON_DRAWING_TITLE_PATTERN.search(normalized):
        return False
    if DRAWING_TITLE_PATTERN.search(normalized):
        return True

    tokens = normalized.split()
    uppercase_tokens = [token for token in tokens if any(char.isalpha() for char in token) and token == token.upper()]
    return len(tokens) <= 8 and len(uppercase_tokens) >= 2


def _dedupe_title_boxes(title_boxes: Iterable[Tuple[float, float, float, float, str]]) -> List[Tuple[float, float, float, float, str]]:
    deduped: List[Tuple[float, float, float, float, str]] = []
    for candidate in sorted(title_boxes, key=lambda item: (item[1], item[0], -(item[2] - item[0]))):
        x0, y0, x1, y1, text = candidate
        if any(_boxes_overlap((x0, y0, x1, y1), existing[:4], overlap_ratio=0.65) for existing in deduped):
            continue
        deduped.append((x0, y0, x1, y1, text))
    return deduped


def _build_regions_from_titles(
    title_boxes: List[Tuple[float, float, float, float, str]],
    page_width: float,
    page_height: float,
) -> List[Tuple[float, float, float, float]]:
    grouped_rows = _group_titles_into_rows(title_boxes)
    regions: List[Tuple[float, float, float, float]] = []

    for row_index, row in enumerate(grouped_rows):
        row_top = 0.0 if row_index == 0 else (grouped_rows[row_index - 1][0][3] + row[0][1]) / 2
        row_bottom = page_height if row_index == len(grouped_rows) - 1 else (row[0][3] + grouped_rows[row_index + 1][0][1]) / 2
        padded_row_top = max(0.0, row_top - TITLE_PADDING_TOP) if row_index == 0 else min(page_height, row_top + 2.0)
        padded_row_bottom = min(page_height, row_bottom + TITLE_PADDING_BOTTOM) if row_index == len(grouped_rows) - 1 else max(0.0, row_bottom - 2.0)

        sorted_row = sorted(row, key=lambda item: item[0])
        for item_index, (x0, y0, x1, y1, _text) in enumerate(sorted_row):
            region_left = 0.0 if item_index == 0 else (sorted_row[item_index - 1][2] + x0) / 2
            region_right = page_width if item_index == len(sorted_row) - 1 else (x1 + sorted_row[item_index + 1][0]) / 2
            region = (
                max(0.0, region_left - TITLE_PADDING_X),
                padded_row_top,
                min(page_width, region_right + TITLE_PADDING_X),
                padded_row_bottom,
            )
            regions.append(region)

    return regions


def _ordered_title_boxes(
    title_boxes: List[Tuple[float, float, float, float, str]]
) -> List[Tuple[float, float, float, float, str]]:
    ordered: List[Tuple[float, float, float, float, str]] = []
    for row in _group_titles_into_rows(title_boxes):
        ordered.extend(sorted(row, key=lambda item: item[0]))
    return ordered


def _regions_for_selected_titles(
    all_title_boxes: List[Tuple[float, float, float, float, str]],
    selected_title_boxes: List[Tuple[float, float, float, float, str]],
    page_width: float,
    page_height: float,
) -> List[Tuple[float, float, float, float]]:
    all_regions = _build_regions_from_titles(all_title_boxes, page_width, page_height)
    ordered_titles = _ordered_title_boxes(all_title_boxes)
    selected_keys = {(box[0], box[1], box[2], box[3], box[4]) for box in selected_title_boxes}
    return [
        region
        for title_box, region in zip(ordered_titles, all_regions)
        if (title_box[0], title_box[1], title_box[2], title_box[3], title_box[4]) in selected_keys
    ]


def _group_titles_into_rows(
    title_boxes: List[Tuple[float, float, float, float, str]]
) -> List[List[Tuple[float, float, float, float, str]]]:
    rows: List[List[Tuple[float, float, float, float, str]]] = []

    for title_box in sorted(title_boxes, key=lambda item: (item[1], item[0])):
        placed = False
        title_mid_y = (title_box[1] + title_box[3]) / 2
        for row in rows:
            row_mid_y = sum((item[1] + item[3]) / 2 for item in row) / len(row)
            if abs(title_mid_y - row_mid_y) <= TITLE_VERTICAL_TOLERANCE:
                row.append(title_box)
                placed = True
                break
        if not placed:
            rows.append([title_box])

    return rows


def _merge_overlapping_regions(regions: List[Tuple[float, float, float, float]]) -> List[Tuple[float, float, float, float]]:
    merged: List[Tuple[float, float, float, float]] = []

    for region in sorted(regions, key=lambda item: (item[1], item[0])):
        current = region
        did_merge = True
        while did_merge:
            did_merge = False
            next_merged: List[Tuple[float, float, float, float]] = []
            for existing in merged:
                if _boxes_overlap(current, existing, overlap_ratio=0.75):
                    current = (
                        min(current[0], existing[0]),
                        min(current[1], existing[1]),
                        max(current[2], existing[2]),
                        max(current[3], existing[3]),
                    )
                    did_merge = True
                else:
                    next_merged.append(existing)
            merged = next_merged
        merged.append(current)

    return merged


def _boxes_overlap(
    first: Tuple[float, float, float, float],
    second: Tuple[float, float, float, float],
    *,
    overlap_ratio: float,
) -> bool:
    x0 = max(first[0], second[0])
    y0 = max(first[1], second[1])
    x1 = min(first[2], second[2])
    y1 = min(first[3], second[3])
    if x1 <= x0 or y1 <= y0:
        return False

    intersection_area = (x1 - x0) * (y1 - y0)
    first_area = max(1.0, (first[2] - first[0]) * (first[3] - first[1]))
    second_area = max(1.0, (second[2] - second[0]) * (second[3] - second[1]))
    return (intersection_area / min(first_area, second_area)) >= overlap_ratio


def _region_area(region: Tuple[float, float, float, float]) -> float:
    return max(1.0, (region[2] - region[0]) * (region[3] - region[1]))


def _region_area_ratio(region: Tuple[float, float, float, float], page_width: float, page_height: float) -> float:
    return _region_area(region) / max(1.0, page_width * page_height)


def _region_contains(
    outer: Tuple[float, float, float, float],
    inner: Tuple[float, float, float, float],
    *,
    padding: float = 0.0,
) -> bool:
    return (
        inner[0] >= (outer[0] - padding)
        and inner[1] >= (outer[1] - padding)
        and inner[2] <= (outer[2] + padding)
        and inner[3] <= (outer[3] + padding)
    )


def _region_is_composite_candidate(
    region: Tuple[float, float, float, float],
    regions: List[Tuple[float, float, float, float]],
) -> bool:
    contained_children = []
    region_area = _region_area(region)

    for candidate in regions:
        if candidate == region:
            continue
        if not _region_contains(region, candidate, padding=6.0):
            continue
        if _region_area(candidate) < (region_area * 0.18):
            continue
        contained_children.append(candidate)

    # If a region contains multiple substantial child panels, treat it as a
    # composite crop and prefer the more specific children instead.
    return len(contained_children) >= 2


def _extract_drawings_from_page(
    page_image_bytes: bytes,
    page_number: int,
    source_kind: str = "pdf",
) -> List[ExtractedDrawing]:
    image = Image.open(io.BytesIO(page_image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")

    detection_image = image.copy()
    detection_image.thumbnail(MAX_DETECTION_SIZE, Image.Resampling.LANCZOS)

    boxes = _collect_image_candidate_boxes(detection_image)
    if not boxes:
        return [
            ExtractedDrawing(
                image_bytes=_normalize_image_bytes(page_image_bytes),
                page_number=page_number,
                drawing_index=1,
                source_kind=source_kind,
                bbox=(0, 0, image.width, image.height),
            )
        ]

    scale_x = image.width / detection_image.width
    scale_y = image.height / detection_image.height
    drawings: List[ExtractedDrawing] = []

    for drawing_index, box in enumerate(boxes, start=1):
        x0, y0, x1, y1 = box
        orig_box = (
            max(0, int(x0 * scale_x) - PDF_DRAWING_TITLE_PADDING_SIDE),
            max(0, int(y0 * scale_y) - PDF_DRAWING_TITLE_PADDING_TOP),
            min(image.width, int(x1 * scale_x) + PDF_DRAWING_TITLE_PADDING_SIDE),
            min(image.height, int(y1 * scale_y) + PDF_DRAWING_TITLE_PADDING_BOTTOM),
        )
        cropped = image.crop(orig_box)
        buffer = io.BytesIO()
        cropped.save(buffer, format="PNG", optimize=True)
        drawings.append(
            ExtractedDrawing(
                image_bytes=_normalize_image_bytes(buffer.getvalue()),
                page_number=page_number,
                drawing_index=drawing_index,
                source_kind=source_kind,
                bbox=orig_box,
            )
        )

    return drawings


def _collect_image_candidate_boxes(image: Image.Image) -> List[Tuple[int, int, int, int]]:
    primary_boxes = _detect_drawing_boxes(image)
    grid_boxes = _detect_grid_boxes(image)
    component_boxes = _detect_component_boxes(image)

    mask = _build_content_mask(image)
    root_box = _trim_box(mask, (0, 0, image.width, image.height))
    panel_boxes: List[Tuple[int, int, int, int]] = []
    if root_box is not None:
        panel_boxes = _split_region_by_panel_lines(
            mask,
            root_box,
            min_width=max(72, int(image.width * 0.1)),
            min_height=max(72, int(image.height * 0.08)),
            min_area=max(6000, int(image.width * image.height * 0.008)),
        )

    return _select_major_image_boxes(
        image.width,
        image.height,
        primary_boxes=primary_boxes,
        grid_boxes=grid_boxes,
        component_boxes=component_boxes,
        panel_boxes=panel_boxes,
    )


def _select_major_image_boxes(
    image_width: int,
    image_height: int,
    *,
    primary_boxes: List[Tuple[int, int, int, int]],
    grid_boxes: List[Tuple[int, int, int, int]],
    component_boxes: List[Tuple[int, int, int, int]],
    panel_boxes: List[Tuple[int, int, int, int]],
) -> List[Tuple[int, int, int, int]]:
    candidate_sets = [
        _dedupe_image_boxes(primary_boxes),
        _dedupe_image_boxes(grid_boxes),
        _dedupe_image_boxes(component_boxes),
        _dedupe_image_boxes(primary_boxes + grid_boxes),
        _dedupe_image_boxes(primary_boxes + component_boxes),
        _dedupe_image_boxes(grid_boxes + component_boxes),
    ]
    candidate_sets = [boxes for boxes in candidate_sets if boxes]
    if not candidate_sets:
        return []

    selected = max(
        candidate_sets,
        key=lambda boxes: _score_image_box_set(boxes, image_width=image_width, image_height=image_height),
    )

    selected = list(selected)
    if selected:
        selected_areas = sorted(_region_area(box) for box in selected)
        median_area = selected_areas[len(selected_areas) // 2]
    else:
        median_area = 0.0
    page_area = max(1.0, image_width * image_height)
    min_panel_area = max(page_area * 0.02, median_area * 0.6)

    for candidate in sorted(_dedupe_image_boxes(panel_boxes), key=lambda item: (_region_area(item), item[1], item[0])):
        if len(selected) >= 12:
            break
        if _region_area(candidate) < min_panel_area:
            continue
        if any(_region_contains(existing, candidate, padding=6.0) for existing in selected):
            continue
        if any(_boxes_overlap(candidate, existing, overlap_ratio=0.8) for existing in selected):
            continue
        selected.append(candidate)

    selected = _dedupe_image_boxes(selected)
    selected.sort(key=lambda item: (item[1], item[0]))
    return selected


def _dedupe_image_boxes(boxes: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
    deduped: List[Tuple[int, int, int, int]] = []
    for candidate in sorted(boxes, key=lambda item: (_region_area(item), item[1], item[0])):
        if any(_region_contains(existing, candidate, padding=6.0) for existing in deduped):
            continue
        if any(_boxes_overlap(candidate, existing, overlap_ratio=0.8) for existing in deduped):
            continue
        deduped.append(candidate)
    return deduped


def _score_image_box_set(
    boxes: List[Tuple[int, int, int, int]],
    *,
    image_width: int,
    image_height: int,
) -> float:
    page_area = max(1.0, image_width * image_height)
    count = len(boxes)
    area_ratios = [_region_area(box) / page_area for box in boxes]
    avg_area_ratio = sum(area_ratios) / count
    union_area_ratio = sum(area_ratios)
    row_clusters = _cluster_box_centers(boxes, axis="y", gap=max(90, int(image_height * 0.12)))
    col_clusters = _cluster_box_centers(boxes, axis="x", gap=max(90, int(image_width * 0.12)))

    # Prefer plausible sheet-level panel counts, good spread across rows/columns,
    # and broad page coverage over fragmented but oversized crops.
    count_penalty = abs(count - 8)
    if count > 12:
        count_penalty += (count - 12) * 4
    if count < 2:
        count_penalty += 8
    row_penalty = 0 if 2 <= row_clusters <= 3 else abs(row_clusters - 2) * 3
    col_penalty = 0 if 3 <= col_clusters <= 5 else abs(col_clusters - 4) * 2
    oversized_penalty = sum(4 for area_ratio in area_ratios if area_ratio > 0.18)
    return (avg_area_ratio * 75.0) + (union_area_ratio * 25.0) - count_penalty - row_penalty - col_penalty - oversized_penalty


def _cluster_box_centers(
    boxes: List[Tuple[int, int, int, int]],
    *,
    axis: str,
    gap: int,
) -> int:
    if not boxes:
        return 0

    if axis == "y":
        values = sorted((box[1] + box[3]) / 2 for box in boxes)
    else:
        values = sorted((box[0] + box[2]) / 2 for box in boxes)

    clusters = 1
    anchor = values[0]
    for value in values[1:]:
        if abs(value - anchor) > gap:
            clusters += 1
        anchor = value
    return clusters


def _detect_component_boxes(image: Image.Image) -> List[Tuple[int, int, int, int]]:
    """
    Detect panel-sized regions from connected components on a lightly dilated mask.
    This works better on sparse architectural sheets where whitespace inside a drawing
    can confuse pure split-based heuristics.
    """
    grayscale = image.convert("L")
    binary = grayscale.point(lambda px: 255 if px < CONTENT_THRESHOLD else 0, mode="L")
    dense = binary.filter(ImageFilter.MaxFilter(COMPONENT_DILATION_SIZE))
    width, height = dense.size
    pixels = [1 if px else 0 for px in dense.getdata()]
    page_area = max(1.0, width * height)
    min_pixel_count = max(1500, int(page_area * COMPONENT_MIN_PIXEL_RATIO))
    min_box_area = page_area * COMPONENT_MIN_BOX_AREA_RATIO
    max_box_area = page_area * COMPONENT_MAX_BOX_AREA_RATIO

    boxes: List[Tuple[int, int, int, int]] = []
    visited = set()
    for start_index, is_filled in enumerate(pixels):
        if not is_filled or start_index in visited:
            continue

        queue = deque([start_index])
        visited.add(start_index)
        count = 0
        min_x = max_x = start_index % width
        min_y = max_y = start_index // width

        while queue:
            current = queue.popleft()
            x = current % width
            y = current // width
            count += 1
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

            for next_x, next_y in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if not (0 <= next_x < width and 0 <= next_y < height):
                    continue
                next_index = (next_y * width) + next_x
                if not pixels[next_index] or next_index in visited:
                    continue
                visited.add(next_index)
                queue.append(next_index)

        if count < min_pixel_count:
            continue

        candidate = (min_x, min_y, max_x + 1, max_y + 1)
        box_area = _region_area(candidate)
        if box_area < min_box_area or box_area > max_box_area:
            continue
        boxes.append(candidate)

    boxes = _dedupe_image_boxes(boxes)
    boxes = [box for box in boxes if not _region_is_composite_candidate(box, boxes)]
    boxes.sort(key=lambda item: (item[1], item[0]))
    return boxes


def _detect_drawing_boxes(image: Image.Image) -> List[Tuple[int, int, int, int]]:
    mask = _build_content_mask(image)
    root_box = _trim_box(mask, (0, 0, image.width, image.height))
    if root_box is None:
        return []

    page_area = image.width * image.height
    min_width = max(80, int(image.width * MIN_REGION_WIDTH_RATIO))
    min_height = max(80, int(image.height * MIN_REGION_HEIGHT_RATIO))
    min_area = max(10000, int(page_area * MIN_REGION_AREA_RATIO))

    boxes = _split_box(mask, root_box, min_width=min_width, min_height=min_height, min_area=min_area, depth=0)
    boxes = _refine_detected_boxes(
        mask,
        boxes,
        min_width=min_width,
        min_height=min_height,
        min_area=min_area,
        depth=0,
    )
    filtered = []
    seen = set()

    for box in sorted(boxes, key=lambda item: (item[1], item[0])):
        trimmed = _trim_box(mask, box)
        if trimmed is None:
            continue
        x0, y0, x1, y1 = trimmed
        if (x1 - x0) < min_width or (y1 - y0) < min_height:
            continue
        if (x1 - x0) * (y1 - y0) < min_area:
            continue
        if trimmed in seen:
            continue
        seen.add(trimmed)
        filtered.append(trimmed)

    return filtered


def _detect_grid_boxes(image: Image.Image) -> List[Tuple[int, int, int, int]]:
    mask = _build_content_mask(image)
    root_box = _trim_box(mask, (0, 0, image.width, image.height))
    if root_box is None:
        return []

    x0, y0, x1, y1 = root_box
    width = x1 - x0
    height = y1 - y0
    min_width = max(100, int(width * 0.12))
    min_height = max(100, int(height * 0.10))

    row_profile = [_row_sum(mask, y, x0, x1) for y in range(y0, y1)]
    horizontal_gaps = _find_whitespace_runs(
        row_profile,
        start=y0,
        min_gap=max(18, int(height * 0.025)),
        max_content=max(4, int(width * GRID_GAP_CONTENT_RATIO)),
    )
    if not horizontal_gaps:
        horizontal_gaps = _find_low_density_runs(
            row_profile,
            start=y0,
            min_gap=max(22, int(height * 0.03)),
            threshold_ratio=LOW_DENSITY_GAP_RATIO,
        )
    row_bands = _segments_from_gaps(y0, y1, horizontal_gaps, min_size=min_height)
    if not row_bands:
        row_bands = [(y0, y1)]

    boxes: List[Tuple[int, int, int, int]] = []
    for band_y0, band_y1 in row_bands:
        band_box = _trim_box(mask, (x0, band_y0, x1, band_y1))
        if band_box is None:
            continue
        bx0, by0, bx1, by1 = band_box
        band_width = bx1 - bx0
        col_profile = [_col_sum(mask, x, by0, by1) for x in range(bx0, bx1)]
        vertical_gaps = _find_whitespace_runs(
            col_profile,
            start=bx0,
            min_gap=max(18, int(band_width * 0.02)),
            max_content=max(4, int((by1 - by0) * GRID_GAP_CONTENT_RATIO)),
        )
        if not vertical_gaps:
            vertical_gaps = _find_low_density_runs(
                col_profile,
                start=bx0,
                min_gap=max(20, int(band_width * 0.025)),
                threshold_ratio=LOW_DENSITY_GAP_RATIO,
            )
        col_segments = _segments_from_gaps(bx0, bx1, vertical_gaps, min_size=min_width)
        if not col_segments:
            col_segments = [(bx0, bx1)]

        for seg_x0, seg_x1 in col_segments:
            candidate = _trim_box(mask, (seg_x0, by0, seg_x1, by1))
            if candidate is None:
                continue
            cx0, cy0, cx1, cy1 = candidate
            if (cx1 - cx0) < min_width or (cy1 - cy0) < min_height:
                continue
            boxes.append(candidate)

    deduped: List[Tuple[int, int, int, int]] = []
    for candidate in sorted(boxes, key=lambda item: (item[1], item[0])):
        if any(_boxes_overlap(candidate, existing, overlap_ratio=0.7) for existing in deduped):
            continue
        deduped.append(candidate)
    return _refine_detected_boxes(
        mask,
        deduped,
        min_width=min_width,
        min_height=min_height,
        min_area=max(8000, int((image.width * image.height) * 0.01)),
        depth=0,
    )


def _split_box(
    mask: List[List[int]],
    box: Tuple[int, int, int, int],
    *,
    min_width: int,
    min_height: int,
    min_area: int,
    depth: int,
) -> List[Tuple[int, int, int, int]]:
    trimmed = _trim_box(mask, box)
    if trimmed is None:
        return []

    x0, y0, x1, y1 = trimmed
    width = x1 - x0
    height = y1 - y0
    area = width * height
    if depth >= MAX_SPLIT_DEPTH or width < (min_width * 2) or height < (min_height * 2) or area < (min_area * 2):
        return [trimmed]

    split = _find_best_split(mask, trimmed, min_width=min_width, min_height=min_height)
    if split is None:
        return [trimmed]

    axis, split_start, split_end = split
    if axis == "horizontal":
        top = (x0, y0, x1, split_start)
        bottom = (x0, split_end, x1, y1)
        return _split_box(mask, top, min_width=min_width, min_height=min_height, min_area=min_area, depth=depth + 1) + _split_box(
            mask, bottom, min_width=min_width, min_height=min_height, min_area=min_area, depth=depth + 1
        )

    left = (x0, y0, split_start, y1)
    right = (split_end, y0, x1, y1)
    return _split_box(mask, left, min_width=min_width, min_height=min_height, min_area=min_area, depth=depth + 1) + _split_box(
        mask, right, min_width=min_width, min_height=min_height, min_area=min_area, depth=depth + 1
    )


def _find_best_split(
    mask: List[List[int]],
    box: Tuple[int, int, int, int],
    *,
    min_width: int,
    min_height: int,
) -> Optional[Tuple[str, int, int]]:
    x0, y0, x1, y1 = box
    width = x1 - x0
    height = y1 - y0

    candidates = []
    horizontal = _find_whitespace_run(
        [_row_sum(mask, y, x0, x1) for y in range(y0, y1)],
        start=y0,
        min_gap=max(18, int(height * 0.05)),
        min_before=min_height,
        min_after=min_height,
        max_content=max(2, int(width * 0.003)),
    )
    if horizontal is not None:
        gap_start, gap_end = horizontal
        candidates.append(("horizontal", gap_start, gap_end, gap_end - gap_start))

    vertical = _find_whitespace_run(
        [_col_sum(mask, x, y0, y1) for x in range(x0, x1)],
        start=x0,
        min_gap=max(18, int(width * 0.04)),
        min_before=min_width,
        min_after=min_width,
        max_content=max(2, int(height * 0.003)),
    )
    if vertical is not None:
        gap_start, gap_end = vertical
        candidates.append(("vertical", gap_start, gap_end, gap_end - gap_start))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[3], reverse=True)
    axis, gap_start, gap_end, _ = candidates[0]
    return axis, gap_start, gap_end


def _refine_detected_boxes(
    mask: List[List[int]],
    boxes: List[Tuple[int, int, int, int]],
    *,
    min_width: int,
    min_height: int,
    min_area: int,
    depth: int,
) -> List[Tuple[int, int, int, int]]:
    refined: List[Tuple[int, int, int, int]] = []

    for box in boxes:
        trimmed = _trim_box(mask, box)
        if trimmed is None:
            continue

        x0, y0, x1, y1 = trimmed
        width = x1 - x0
        height = y1 - y0
        area = width * height
        if depth >= MAX_REFINEMENT_DEPTH or width < min_width or height < min_height or area < min_area:
            refined.append(trimmed)
            continue

        relaxed_split = _find_relaxed_density_split(
            mask,
            trimmed,
            min_width=min_width,
            min_height=min_height,
        )
        if relaxed_split is None:
            refined.append(trimmed)
            continue

        axis, split_start, split_end = relaxed_split
        if axis == "horizontal":
            children = [(x0, y0, x1, split_start), (x0, split_end, x1, y1)]
        else:
            children = [(x0, y0, split_start, y1), (split_end, y0, x1, y1)]

        valid_children = []
        for child in children:
            child_trimmed = _trim_box(mask, child)
            if child_trimmed is None:
                valid_children = []
                break
            cx0, cy0, cx1, cy1 = child_trimmed
            child_width = cx1 - cx0
            child_height = cy1 - cy0
            if child_width < min_width or child_height < min_height:
                valid_children = []
                break
            if child_width * child_height < min_area:
                valid_children = []
                break
            valid_children.append(child_trimmed)

        if not valid_children:
            refined.append(trimmed)
            continue

        refined.extend(
            _refine_detected_boxes(
                mask,
                valid_children,
                min_width=min_width,
                min_height=min_height,
                min_area=min_area,
                depth=depth + 1,
            )
        )

    return refined


def _find_relaxed_density_split(
    mask: List[List[int]],
    box: Tuple[int, int, int, int],
    *,
    min_width: int,
    min_height: int,
) -> Optional[Tuple[str, int, int]]:
    x0, y0, x1, y1 = box
    width = x1 - x0
    height = y1 - y0
    candidates = []

    horizontal_runs = _find_low_density_runs(
        [_row_sum(mask, y, x0, x1) for y in range(y0, y1)],
        start=y0,
        min_gap=max(3, int(height * 0.02)),
        threshold_ratio=INTERNAL_SPLIT_DENSITY_RATIO,
    )
    for run_start, run_end in horizontal_runs:
        if (run_start - y0) >= min_height and (y1 - run_end) >= min_height:
            candidates.append(("horizontal", run_start, run_end, run_end - run_start))

    vertical_runs = _find_low_density_runs(
        [_col_sum(mask, x, y0, y1) for x in range(x0, x1)],
        start=x0,
        min_gap=max(3, int(width * 0.02)),
        threshold_ratio=INTERNAL_SPLIT_DENSITY_RATIO,
    )
    for run_start, run_end in vertical_runs:
        if (run_start - x0) >= min_width and (x1 - run_end) >= min_width:
            candidates.append(("vertical", run_start, run_end, run_end - run_start))

    if not candidates:
        return None

    # Favor horizontal splits for tall stacked panels, vertical splits for wide rows.
    axis_bias = "horizontal" if height >= (width * 1.15) else "vertical"
    candidates.sort(
        key=lambda item: (
            item[0] != axis_bias,
            -(item[3]),
        )
    )
    axis, split_start, split_end, _ = candidates[0]
    return axis, split_start, split_end


def _find_whitespace_run(
    profile: List[int],
    *,
    start: int,
    min_gap: int,
    min_before: int,
    min_after: int,
    max_content: int,
) -> Optional[Tuple[int, int]]:
    best: Optional[Tuple[int, int]] = None
    run_start: Optional[int] = None

    for idx, value in enumerate(profile):
        if value <= max_content:
            if run_start is None:
                run_start = idx
            continue

        if run_start is not None:
            run_end = idx
            if _is_valid_gap(run_start, run_end, len(profile), min_gap, min_before, min_after):
                best = _pick_longer_gap(best, (start + run_start, start + run_end))
            run_start = None

    if run_start is not None:
        run_end = len(profile)
        if _is_valid_gap(run_start, run_end, len(profile), min_gap, min_before, min_after):
            best = _pick_longer_gap(best, (start + run_start, start + run_end))

    return best


def _find_whitespace_runs(
    profile: List[int],
    *,
    start: int,
    min_gap: int,
    max_content: int,
) -> List[Tuple[int, int]]:
    runs: List[Tuple[int, int]] = []
    run_start: Optional[int] = None

    for idx, value in enumerate(profile):
        if value <= max_content:
            if run_start is None:
                run_start = idx
            continue

        if run_start is not None:
            run_end = idx
            if (run_end - run_start) >= min_gap:
                runs.append((start + run_start, start + run_end))
            run_start = None

    if run_start is not None:
        run_end = len(profile)
        if (run_end - run_start) >= min_gap:
            runs.append((start + run_start, start + run_end))

    return runs


def _find_low_density_runs(
    profile: List[int],
    *,
    start: int,
    min_gap: int,
    threshold_ratio: float,
) -> List[Tuple[int, int]]:
    if not profile:
        return []

    max_value = max(profile)
    if max_value <= 0:
        return [(start, start + len(profile))]

    threshold = max_value * threshold_ratio
    runs: List[Tuple[int, int]] = []
    run_start: Optional[int] = None

    for idx, value in enumerate(profile):
        if value <= threshold:
            if run_start is None:
                run_start = idx
            continue

        if run_start is not None:
            run_end = idx
            if (run_end - run_start) >= min_gap:
                runs.append((start + run_start, start + run_end))
            run_start = None

    if run_start is not None:
        run_end = len(profile)
        if (run_end - run_start) >= min_gap:
            runs.append((start + run_start, start + run_end))

    return runs


def _segments_from_gaps(start: int, end: int, gaps: List[Tuple[int, int]], *, min_size: int) -> List[Tuple[int, int]]:
    segments: List[Tuple[int, int]] = []
    cursor = start

    for gap_start, gap_end in gaps:
        if (gap_start - cursor) >= min_size:
            segments.append((cursor, gap_start))
        cursor = max(cursor, gap_end)

    if (end - cursor) >= min_size:
        segments.append((cursor, end))

    return segments


def _is_valid_gap(run_start: int, run_end: int, total_length: int, min_gap: int, min_before: int, min_after: int) -> bool:
    gap_length = run_end - run_start
    return gap_length >= min_gap and run_start >= min_before and (total_length - run_end) >= min_after


def _pick_longer_gap(current: Optional[Tuple[int, int]], candidate: Tuple[int, int]) -> Tuple[int, int]:
    if current is None:
        return candidate
    current_length = current[1] - current[0]
    candidate_length = candidate[1] - candidate[0]
    return candidate if candidate_length > current_length else current


def _trim_box(mask: List[List[int]], box: Tuple[int, int, int, int]) -> Optional[Tuple[int, int, int, int]]:
    x0, y0, x1, y1 = box
    rows = [y for y in range(y0, y1) if _row_sum(mask, y, x0, x1) > 0]
    cols = [x for x in range(x0, x1) if _col_sum(mask, x, y0, y1) > 0]
    if not rows or not cols:
        return None
    return cols[0], rows[0], cols[-1] + 1, rows[-1] + 1


def _build_content_mask(image: Image.Image) -> List[List[int]]:
    grayscale = image.convert("L")
    binary = grayscale.point(lambda px: 1 if px < CONTENT_THRESHOLD else 0, mode="L")
    pixels = list(binary.getdata())
    width, height = binary.size
    return [pixels[row * width:(row + 1) * width] for row in range(height)]


def _row_sum(mask: List[List[int]], y: int, x0: int, x1: int) -> int:
    return sum(mask[y][x0:x1])


def _col_sum(mask: List[List[int]], x: int, y0: int, y1: int) -> int:
    return sum(mask[y][x] for y in range(y0, y1))


def _normalize_image_bytes(image_bytes: bytes) -> bytes:
    """
    Ensure the uploaded image fits size/color constraints and return as PNG.
    """
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")

    current_long_edge = max(image.size)
    if current_long_edge < MIN_VISION_LONG_EDGE:
        scale = MIN_VISION_LONG_EDGE / float(current_long_edge)
        resized = (
            max(1, int(round(image.width * scale))),
            max(1, int(round(image.height * scale))),
        )
        image = image.resize(resized, Image.Resampling.LANCZOS)

    if image.size[0] > MAX_IMAGE_SIZE[0] or image.size[1] > MAX_IMAGE_SIZE[1]:
        image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
