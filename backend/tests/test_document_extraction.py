import io

from PIL import Image, ImageDraw

import main
from agents import image_utils
from agents.optimized_orchestrator import OptimizedRoofValidator
from utils.pdf_generator import ComplianceReportGenerator


def _build_two_drawing_sheet() -> bytes:
    image = Image.new("RGB", (1200, 1600), "white")
    draw = ImageDraw.Draw(image)

    draw.rectangle((80, 90, 1080, 640), outline="black", width=8)
    draw.line((110, 180, 1050, 180), fill="black", width=4)
    draw.line((220, 120, 220, 610), fill="black", width=4)
    draw.text((120, 110), "ROOF DETAIL A", fill="black")

    draw.rectangle((80, 860, 1080, 1450), outline="black", width=8)
    draw.line((110, 980, 1050, 980), fill="black", width=4)
    draw.line((340, 890, 340, 1420), fill="black", width=4)
    draw.text((120, 880), "ROOF DETAIL B", fill="black")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_extract_document_drawings_splits_pdf_sheet(monkeypatch):
    page_bytes = _build_two_drawing_sheet()
    monkeypatch.setattr(image_utils, "_pdf_to_page_images", lambda _pdf_bytes: [page_bytes])

    drawings = image_utils.extract_document_drawings(b"%PDF synthetic")

    assert len(drawings) == 2
    assert [drawing.page_number for drawing in drawings] == [1, 1]
    assert [drawing.drawing_index for drawing in drawings] == [1, 2]
    assert all(drawing.source_kind == "pdf" for drawing in drawings)


def test_extract_document_drawings_with_diagnostics_for_image():
    image_bytes = _build_two_drawing_sheet()

    drawings, diagnostics = image_utils.extract_document_drawings_with_diagnostics(image_bytes)

    assert len(drawings) == 2
    assert diagnostics["source_kind"] == "image"
    assert diagnostics["total_drawings"] == 2
    assert diagnostics["pages"][0]["selected_region_count"] == 2
    assert diagnostics["pages"][0]["strategy"] == "image-drawings"
    assert all(drawing.source_kind == "image" for drawing in drawings)


def test_normalize_image_bytes_upscales_small_images_for_vision():
    image = Image.new("RGB", (582, 836), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    normalized = image_utils._normalize_image_bytes(buffer.getvalue())
    normalized_image = Image.open(io.BytesIO(normalized))

    assert normalized_image.format == "PNG"
    assert max(normalized_image.size) == image_utils.MIN_VISION_LONG_EDGE


def test_build_full_page_pdf_drawing_uses_original_page_bounds():
    page_bytes = _build_two_drawing_sheet()

    drawing = image_utils._build_full_page_pdf_drawing(page_bytes, page_number=3)

    assert drawing.page_number == 3
    assert drawing.drawing_index == 1
    assert drawing.source_kind == "pdf"
    assert drawing.bbox == (0, 0, 1200, 1600)


def test_expand_pdf_crop_bbox_includes_space_for_title_band():
    expanded = image_utils._expand_pdf_crop_bbox(
        (100.0, 200.0, 500.0, 700.0),
        page_width=1200.0,
        page_height=1600.0,
    )

    assert expanded == (64.0, 160.0, 536.0, 880.0)


def test_combine_document_results_keeps_nested_drawing_metadata():
    combined = main._combine_document_results(
        {
            "results": [
                {"filename": "sheet.pdf - Page 1 Drawing 1", "success": True, "drawing_index": 1},
                {"filename": "sheet.pdf - Page 1 Drawing 2", "success": True, "drawing_index": 2},
            ]
        },
        filename="sheet.pdf",
        selected_model="gpt-5.2",
        source_file_index=0,
    )

    assert combined["source_filename"] == "sheet.pdf"
    assert combined["source_file_index"] == 0
    assert combined["selected_model"] == "gpt-5.2"
    assert combined["total_drawings"] == 2
    assert combined["results"][1]["drawing_index"] == 2


def test_combine_document_results_keeps_extraction_diagnostics():
    combined = main._combine_document_results(
        {
            "results": [
                {"filename": "sheet.pdf - Page 1 Drawing 1", "success": True, "drawing_index": 1},
            ],
            "extraction_diagnostics": {
                "source_kind": "pdf",
                "total_drawings": 7,
                "pages": [{"page_number": 1, "selected_region_count": 7, "strategy": "fused-regions"}],
            },
        },
        filename="sheet.pdf",
        selected_model="mistral-small-3.1",
        source_file_index=0,
    )

    assert combined["extraction_diagnostics"]["total_drawings"] == 7
    assert combined["results"][0]["extraction_diagnostics"]["total_drawings"] == 7


def test_build_optimized_validators_includes_legacy_main_model(monkeypatch):
    class StubValidator:
        def __init__(self, api_key, api_base, main_model, summary_model):
            self.api_key = api_key
            self.api_base = api_base
            self.main_model = main_model
            self.summary_model = summary_model

    for env_var in (
        "MISTRAL_API_KEY",
        "NAVIGATOR_API_KEY",
        "MISTRAL_API_BASE",
        "MISTRAL_MAIN_MODEL",
        "MISTRAL_SUMMARY_MODEL",
        "LLAMA_API_KEY",
        "LLAMA_API_BASE",
        "LLAMA_MAIN_MODEL",
        "LLAMA_SUMMARY_MODEL",
        "GPT52_API_KEY",
        "GPT52_API_BASE",
        "GPT52_MAIN_MODEL",
        "GPT52_SUMMARY_MODEL",
        "OPENAI_API_KEY",
        "OPENAI_API_BASE",
        "MAIN_MODEL",
        "SUMMARY_MODEL",
    ):
        monkeypatch.delenv(env_var, raising=False)

    monkeypatch.setenv("MISTRAL_API_KEY", "mistral-key")
    monkeypatch.setenv("MISTRAL_MAIN_MODEL", "mistral-small-3.1")
    monkeypatch.setenv("MISTRAL_SUMMARY_MODEL", "mistral-small-3.1")
    monkeypatch.setenv("LLAMA_API_KEY", "llama-key")
    monkeypatch.setenv("LLAMA_MAIN_MODEL", "llama-3.1-nemotron-nano-8B-v1")
    monkeypatch.setenv("LLAMA_SUMMARY_MODEL", "llama-3.1-nemotron-nano-8B-v1")
    monkeypatch.setenv("GPT52_API_KEY", "openai-key")
    monkeypatch.setenv("GPT52_MAIN_MODEL", "gpt-5.2")
    monkeypatch.setenv("GPT52_SUMMARY_MODEL", "gpt-5.2")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    monkeypatch.setenv("MAIN_MODEL", "gpt-5-nano")
    monkeypatch.setenv("SUMMARY_MODEL", "gpt-5-nano")
    monkeypatch.setattr(main, "OptimizedRoofValidator", StubValidator)
    monkeypatch.setattr(
        main,
        "_read_env_assignments",
        lambda: {
            "MISTRAL_MAIN_MODEL": ["mistral-small-3.1"],
            "MISTRAL_SUMMARY_MODEL": ["mistral-small-3.1"],
            "LLAMA_MAIN_MODEL": ["llama-3.1-nemotron-nano-8B-v1"],
            "LLAMA_SUMMARY_MODEL": ["llama-3.1-nemotron-nano-8B-v1"],
            "GPT52_MAIN_MODEL": ["gpt-5.2"],
            "GPT52_SUMMARY_MODEL": ["gpt-5.2"],
            "MAIN_MODEL": ["gpt-5-nano"],
            "SUMMARY_MODEL": ["gpt-5-nano"],
        },
    )

    validators = main.build_optimized_validators()

    assert sorted(validators.keys()) == [
        "gpt-5-nano",
        "gpt-5.2",
        "llama-3.1-nemotron-nano-8B-v1",
        "mistral-small-3.1",
    ]
    assert validators["gpt-5-nano"].summary_model == "gpt-5-nano"
    assert validators["llama-3.1-nemotron-nano-8B-v1"].summary_model == "llama-3.1-nemotron-nano-8B-v1"


def test_single_detected_pdf_region_uses_full_page_original(monkeypatch):
    class StubPage:
        rect = type("Rect", (), {"width": 1200.0, "height": 1600.0})()

        def get_pixmap(self, matrix=None, clip=None, alpha=False):
            class StubPix:
                def tobytes(self, fmt):
                    return _build_two_drawing_sheet()

            return StubPix()

    monkeypatch.setattr(image_utils, "_extract_titled_regions_from_pdf_page", lambda _page: [])
    monkeypatch.setattr(image_utils, "_refine_pdf_region_bboxes", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        image_utils,
        "_extract_drawings_from_page",
        lambda _page_png, page_number: [
            image_utils.ExtractedDrawing(
                image_bytes=b"cropped",
                page_number=page_number,
                drawing_index=1,
                source_kind="pdf",
                bbox=(100, 100, 500, 500),
            )
        ],
    )

    drawings, diagnostics = image_utils._extract_drawings_from_pdf_page_with_diagnostics(
        StubPage(),
        page_number=1,
        matrix=type("Matrix", (), {"a": 1.0, "d": 1.0})(),
    )

    assert len(drawings) == 1
    assert drawings[0].bbox == (0, 0, 1200, 1600)
    assert diagnostics.selected_region_count == 1
    assert diagnostics.strategy == "single-page-original"


def test_build_regions_from_titles_creates_grid_aligned_regions():
    title_boxes = [
        (80.0, 700.0, 340.0, 740.0, "NEW ROOF FRAMING PLAN"),
        (420.0, 700.0, 700.0, 740.0, "NEW ROOF PLAN"),
        (980.0, 680.0, 1240.0, 720.0, "TYPICAL EXIST. INT. WALL SECTION"),
        (80.0, 1460.0, 320.0, 1500.0, "TYPICAL NEW WALL SECTION"),
        (380.0, 1460.0, 640.0, 1500.0, "TYPICAL EXIST. WALL SECTION"),
        (720.0, 1460.0, 980.0, 1500.0, "TYPICAL EXIST. WALL SECTION"),
        (1060.0, 1460.0, 1320.0, 1500.0, "TYPICAL NEW WALL SECTION"),
        (1400.0, 1460.0, 1660.0, 1500.0, "TYPICAL NEW WALL SECTION"),
    ]

    regions = image_utils._build_regions_from_titles(title_boxes, page_width=1728.0, page_height=2592.0)

    assert len(regions) == len(title_boxes)
    assert regions[0][0] <= 80.0
    assert regions[0][1] < 700.0
    assert regions[-1][2] >= 1660.0
    assert max(region[3] for region in regions[:3]) < min(region[1] for region in regions[3:])


def test_dedupe_title_boxes_removes_overlapping_duplicates():
    deduped = image_utils._dedupe_title_boxes([
        (100.0, 200.0, 360.0, 240.0, "NEW ROOF PLAN"),
        (110.0, 205.0, 355.0, 238.0, "NEW ROOF PLAN"),
        (500.0, 200.0, 760.0, 240.0, "TYPICAL WALL SECTION"),
    ])

    assert len(deduped) == 2


def test_grouped_report_detection_keeps_failed_drawings():
    generator = ComplianceReportGenerator()

    grouped = generator._extract_grouped_results({
        "results": [
            {
                "drawing_label": "Page 1 Drawing 1",
                "validation_report": "STEP 2: CHECKS",
                "success": True,
            },
            {
                "drawing_label": "Page 1 Drawing 2",
                "error": "Model output missing",
                "success": False,
            },
        ]
    })

    assert len(grouped) == 2


def test_grouped_report_detection_supports_single_wrapped_result():
    generator = ComplianceReportGenerator()

    grouped = generator._extract_grouped_results({
        "results": [
            {
                "drawing_label": "Page 1 Drawing 1",
                "validation_report": "STEP 2: CHECKS",
                "success": True,
            }
        ]
    })

    assert len(grouped) == 1


def test_rejects_single_titled_region_that_covers_most_of_page():
    assert image_utils._should_use_titled_regions(
        [(0.0, 0.0, 980.0, 980.0)],
        page_width=1000.0,
        page_height=1000.0,
    ) is False


def test_accepts_multiple_titled_regions():
    assert image_utils._should_use_titled_regions(
        [
            (0.0, 0.0, 400.0, 400.0),
            (420.0, 0.0, 820.0, 400.0),
        ],
        page_width=1000.0,
        page_height=1000.0,
    ) is True


def test_dedupe_title_boxes_preserves_distinct_line_titles():
    deduped = image_utils._dedupe_title_boxes([
        (100.0, 100.0, 300.0, 130.0, "NEW ROOF FRAMING PLAN"),
        (100.0, 150.0, 280.0, 180.0, "NEW ROOF PLAN"),
    ])

    assert len(deduped) == 2


def test_normalize_title_text_merges_letter_spaced_words():
    normalized = image_utils._normalize_title_text("N E W R O O F P L A N")

    assert normalized == "NEW ROOF PLAN"
    assert image_utils._looks_like_drawing_title(normalized) is True


def test_find_word_cluster_title_boxes_reconstructs_fragmented_titles():
    class StubPage:
        def get_text(self, mode):
            if mode == "words":
                return [
                    (100.0, 120.0, 120.0, 140.0, "NEW", 0, 0, 0),
                    (128.0, 120.0, 180.0, 140.0, "ROOF", 0, 0, 1),
                    (188.0, 120.0, 250.0, 140.0, "PLAN", 0, 0, 2),
                ]
            return []

    title_boxes = image_utils._find_word_cluster_title_boxes(StubPage())

    assert len(title_boxes) == 1
    assert title_boxes[0][4] == "NEW ROOF PLAN"


def test_select_major_image_boxes_rejects_oversplit_panel_set():
    primary_boxes = [
        (0, 0, 300, 220),
        (320, 0, 620, 220),
        (640, 0, 940, 220),
        (0, 260, 220, 520),
        (240, 260, 460, 520),
        (480, 260, 700, 520),
        (720, 260, 940, 520),
    ]
    panel_boxes = [
        (index * 50, 0, (index * 50) + 80, 90)
        for index in range(20)
    ]

    selected = image_utils._select_major_image_boxes(
        1000,
        600,
        primary_boxes=primary_boxes,
        grid_boxes=[],
        component_boxes=[],
        panel_boxes=panel_boxes,
    )

    assert len(selected) == len(primary_boxes)


def test_score_image_box_set_prefers_balanced_sheet_layout():
    fragmented = [
        (40, 15, 510, 525),
        (669, 15, 1078, 819),
        (1167, 15, 1589, 470),
        (1167, 539, 1589, 1057),
        (40, 586, 510, 819),
        (40, 910, 510, 1057),
        (669, 910, 1078, 1057),
    ]
    balanced = [
        (45, 26, 487, 501),
        (446, 25, 865, 490),
        (880, 33, 1176, 443),
        (1179, 65, 1492, 452),
        (48, 585, 361, 1016),
        (371, 585, 649, 1007),
        (641, 552, 936, 1007),
        (942, 537, 1227, 1015),
        (1216, 535, 1482, 781),
        (1261, 785, 1512, 978),
    ]

    fragmented_score = image_utils._score_image_box_set(
        fragmented,
        image_width=1600,
        image_height=1067,
    )
    balanced_score = image_utils._score_image_box_set(
        balanced,
        image_width=1600,
        image_height=1067,
    )

    assert balanced_score > fragmented_score


def test_detect_component_boxes_finds_sparse_panel_layout():
    image = Image.new("RGB", (1400, 900), "white")
    draw = ImageDraw.Draw(image)

    # Top row: 4 sparse panels
    top_boxes = [
        (40, 40, 320, 360),
        (360, 40, 680, 360),
        (740, 40, 1040, 360),
        (1080, 40, 1360, 360),
    ]
    # Bottom row: 5 sparse panels
    bottom_boxes = [
        (40, 480, 280, 840),
        (300, 480, 540, 840),
        (560, 480, 800, 840),
        (820, 480, 1060, 840),
        (1080, 480, 1320, 840),
    ]

    for x0, y0, x1, y1 in top_boxes + bottom_boxes:
        draw.line((x0, y0, x1, y0), fill="black", width=4)
        draw.line((x0, y0, x0, y1), fill="black", width=4)
        draw.line((x0, y1, x1, y1), fill="black", width=4)
        draw.line((x1, y0, x1, y1), fill="black", width=4)
        draw.line((x0 + 30, y0 + 80, x1 - 30, y1 - 60), fill="black", width=2)
        draw.line((x0 + 60, y0 + 40, x0 + 60, y1 - 40), fill="black", width=2)

    boxes = image_utils._detect_component_boxes(image)

    assert len(boxes) >= 8


def test_segments_from_gaps_returns_panels_between_whitespace_runs():
    segments = image_utils._segments_from_gaps(
        0,
        1000,
        [(200, 260), (520, 560)],
        min_size=120,
    )

    assert segments == [(0, 200), (260, 520), (560, 1000)]


def test_find_low_density_runs_detects_sparse_gutters():
    runs = image_utils._find_low_density_runs(
        [100, 110, 12, 9, 11, 95, 102, 8, 7, 9, 98],
        start=0,
        min_gap=2,
        threshold_ratio=0.14,
    )

    assert runs == [(2, 5), (7, 10)]


def test_find_relaxed_density_split_prefers_horizontal_split_for_tall_box():
    mask = []
    width = 20
    for row in range(30):
        if 12 <= row <= 15:
            mask.append([0] * width)
        else:
            mask.append([1] * width)

    split = image_utils._find_relaxed_density_split(
        mask,
        (0, 0, 20, 30),
        min_width=6,
        min_height=8,
    )

    assert split is not None
    assert split[0] == "horizontal"


def test_split_pdf_region_from_image_returns_multiple_children_for_large_stacked_region():
    image = Image.new("RGB", (600, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 40, 560, 360), outline="black", width=8)
    draw.rectangle((40, 500, 560, 840), outline="black", width=8)

    children = image_utils._split_pdf_region_from_image(
        image,
        (0.0, 0.0, 600.0, 900.0),
        scale_x=1.0,
        scale_y=1.0,
        page_width=600.0,
        page_height=900.0,
    )

    assert len(children) >= 2


def test_fuse_pdf_regions_keeps_unique_candidates_without_duplicates():
    class StubPage:
        class Rect:
            width = 1000.0
            height = 1000.0
        rect = Rect()

    class StubMatrix:
        a = 1.0
        d = 1.0

    image_drawings = [
        image_utils.ExtractedDrawing(b"", 1, 1, "pdf", bbox=(0, 0, 300, 300)),
        image_utils.ExtractedDrawing(b"", 1, 2, "pdf", bbox=(350, 0, 650, 300)),
    ]

    fused = image_utils._fuse_pdf_regions(
        [(0.0, 0.0, 300.0, 300.0)],
        image_drawings,
        StubPage(),
        StubMatrix(),
    )

    assert len(fused) == 2


def test_fuse_pdf_regions_prefers_specific_children_over_large_composite_region():
    class StubPage:
        class Rect:
            width = 1000.0
            height = 1000.0
        rect = Rect()

    class StubMatrix:
        a = 1.0
        d = 1.0

    image_drawings = [
        image_utils.ExtractedDrawing(b"", 1, 1, "pdf", bbox=(0, 0, 320, 320)),
        image_utils.ExtractedDrawing(b"", 1, 2, "pdf", bbox=(340, 0, 660, 320)),
    ]

    fused = image_utils._fuse_pdf_regions(
        [(0.0, 0.0, 700.0, 360.0)],
        image_drawings,
        StubPage(),
        StubMatrix(),
    )

    assert len(fused) == 2
    assert fused[0] == (0.0, 0.0, 320.0, 320.0)


def test_find_strong_line_runs_detects_panel_border_lines():
    runs = image_utils._find_strong_line_runs(
        [2, 3, 90, 95, 4, 5, 88, 92, 3],
        start=0,
        min_run=1,
        threshold_ratio=0.68,
    )

    assert runs == [(2, 4), (6, 8)]


def test_split_pdf_region_from_image_allows_four_detail_panels():
    image = Image.new("RGB", (1200, 420), "white")
    draw = ImageDraw.Draw(image)

    for index in range(4):
        x0 = 30 + (index * 290)
        x1 = x0 + 240
        draw.rectangle((x0, 40, x1, 360), outline="black", width=10)

    children = image_utils._split_pdf_region_from_image(
        image,
        (0.0, 0.0, 1200.0, 420.0),
        scale_x=1.0,
        scale_y=1.0,
        page_width=1200.0,
        page_height=420.0,
    )

    assert len(children) >= 4


def test_split_pdf_region_from_image_allows_seven_detail_panels():
    image = Image.new("RGB", (2100, 420), "white")
    draw = ImageDraw.Draw(image)

    for index in range(7):
        x0 = 25 + (index * 295)
        x1 = x0 + 230
        draw.rectangle((x0, 40, x1, 360), outline="black", width=10)

    children = image_utils._split_pdf_region_from_image(
        image,
        (0.0, 0.0, 2100.0, 420.0),
        scale_x=1.0,
        scale_y=1.0,
        page_width=2100.0,
        page_height=420.0,
    )

    assert len(children) >= 7


def test_extract_titled_regions_keeps_raw_regions_when_merge_collapses_everything(monkeypatch):
    class StubPage:
        class Rect:
            width = 1000.0
            height = 1000.0
        rect = Rect()

    raw_regions = [
        (0.0, 0.0, 520.0, 520.0),
        (480.0, 0.0, 1000.0, 520.0),
        (0.0, 480.0, 520.0, 1000.0),
    ]

    monkeypatch.setattr(
        image_utils,
        "_find_drawing_title_boxes",
        lambda _page: [(0.0, 0.0, 100.0, 20.0, "ROOF PLAN"), (500.0, 0.0, 600.0, 20.0, "WALL SECTION")],
    )
    monkeypatch.setattr(image_utils, "_build_regions_from_titles", lambda *_args: raw_regions)
    monkeypatch.setattr(image_utils, "_merge_overlapping_regions", lambda _regions: [(0.0, 0.0, 1000.0, 1000.0)])

    regions = image_utils._extract_titled_regions_from_pdf_page(StubPage())

    assert regions == raw_regions


def test_filter_wall_section_title_boxes_keeps_only_wall_titles():
    filtered = image_utils._filter_wall_section_title_boxes([
        (0.0, 0.0, 100.0, 20.0, "ROOF PLAN"),
        (120.0, 0.0, 240.0, 20.0, "TYPICAL NEW WALL SECTION"),
        (260.0, 0.0, 380.0, 20.0, "EAVE DETAIL"),
    ])

    assert filtered == [
        (120.0, 0.0, 240.0, 20.0, "TYPICAL NEW WALL SECTION"),
    ]


def test_single_wall_titled_region_stays_cropped_not_full_page(monkeypatch):
    class StubPage:
        class Rect:
            width = 1200.0
            height = 1600.0

        rect = Rect()

        def get_pixmap(self, matrix=None, clip=None, alpha=False):
            class StubPix:
                def __init__(self, bounds):
                    self.bounds = bounds

                def tobytes(self, fmt):
                    width = max(1, int(self.bounds[2] - self.bounds[0]))
                    height = max(1, int(self.bounds[3] - self.bounds[1]))
                    image = Image.new("RGB", (width, height), "white")
                    buffer = io.BytesIO()
                    image.save(buffer, format="PNG")
                    return buffer.getvalue()

            if clip is None:
                return StubPix((0, 0, 1200, 1600))
            return StubPix((clip.x0, clip.y0, clip.x1, clip.y1))

    monkeypatch.setattr(
        image_utils,
        "_find_drawing_title_boxes",
        lambda _page: [
            (10.0, 10.0, 110.0, 30.0, "ROOF PLAN"),
            (510.0, 10.0, 650.0, 30.0, "TYPICAL WALL SECTION"),
        ],
    )
    monkeypatch.setattr(
        image_utils,
        "_extract_drawings_from_page",
        lambda _page_png, page_number: [
            image_utils.ExtractedDrawing(
                image_bytes=b"panel-a",
                page_number=page_number,
                drawing_index=1,
                source_kind="pdf",
                bbox=(50, 50, 450, 450),
            ),
            image_utils.ExtractedDrawing(
                image_bytes=b"panel-b",
                page_number=page_number,
                drawing_index=2,
                source_kind="pdf",
                bbox=(500, 50, 900, 450),
            ),
        ],
    )
    monkeypatch.setattr(image_utils, "_refine_pdf_region_bboxes", lambda _page_png, regions, *_args: regions)

    drawings, diagnostics = image_utils._extract_drawings_from_pdf_page_with_diagnostics(
        StubPage(),
        page_number=1,
        matrix=type("Matrix", (), {"a": 1.0, "d": 1.0})(),
    )

    assert len(drawings) == 1
    assert drawings[0].bbox != (0, 0, 1200, 1600)
    assert diagnostics.strategy == "wall-title-regions"


def test_validate_drawings_parallel_keeps_original_order():
    validator = OptimizedRoofValidator("test-key", "https://example.com", "test-model", "test-model")
    validator.max_parallel_drawings = 3

    drawings = [
        image_utils.ExtractedDrawing(b"a", 1, 1, "pdf"),
        image_utils.ExtractedDrawing(b"b", 1, 2, "pdf"),
        image_utils.ExtractedDrawing(b"c", 1, 3, "pdf"),
    ]

    def fake_validate(drawing, filename=None):
        return {
            "success": True,
            "filename": filename,
            "drawing_index": drawing.drawing_index,
        }

    validator._validate_extracted_drawing = fake_validate  # type: ignore[method-assign]

    results = validator._validate_drawings(drawings, filename="sheet.pdf")

    assert [result["drawing_index"] for result in results] == [1, 2, 3]


def test_select_wall_section_drawings_keeps_only_classified_wall_panels():
    validator = OptimizedRoofValidator("test-key", "https://example.com", "test-model", "test-model")
    validator.max_parallel_classifications = 3

    drawings = [
        image_utils.ExtractedDrawing(b"a", 1, 1, "pdf"),
        image_utils.ExtractedDrawing(b"b", 1, 2, "pdf"),
        image_utils.ExtractedDrawing(b"c", 1, 3, "pdf"),
    ]

    def fake_is_wall(drawing, filename=None):
        return drawing.drawing_index != 2

    validator._is_wall_section_drawing = fake_is_wall  # type: ignore[method-assign]

    selected = validator._select_wall_section_drawings(drawings, filename="sheet.pdf")

    assert [drawing.drawing_index for drawing in selected] == [1, 3]


def test_filter_drawings_for_validation_applies_only_to_multi_drawing_pdfs():
    validator = OptimizedRoofValidator("test-key", "https://example.com", "test-model", "test-model")
    drawings = [
        image_utils.ExtractedDrawing(b"a", 1, 1, "pdf"),
        image_utils.ExtractedDrawing(b"b", 1, 2, "pdf"),
    ]

    validator._select_wall_section_drawings = lambda items, filename=None: [items[1]]  # type: ignore[method-assign]

    filtered_pdf = validator._filter_drawings_for_validation(
        drawings,
        extraction_diagnostics={"source_kind": "pdf"},
        filename="sheet.pdf",
    )
    filtered_image = validator._filter_drawings_for_validation(
        drawings,
        extraction_diagnostics={"source_kind": "image"},
        filename="image.png",
    )

    assert [drawing.drawing_index for drawing in filtered_pdf] == [2]
    assert [drawing.drawing_index for drawing in filtered_image] == [1, 2]


def test_filter_drawings_for_validation_trusts_wall_title_region_strategy():
    validator = OptimizedRoofValidator("test-key", "https://example.com", "test-model", "test-model")
    drawings = [
        image_utils.ExtractedDrawing(b"a", 1, 1, "pdf"),
        image_utils.ExtractedDrawing(b"b", 1, 2, "pdf"),
        image_utils.ExtractedDrawing(b"c", 2, 1, "pdf"),
    ]

    validator._select_wall_section_drawings = lambda items, filename=None: []  # type: ignore[method-assign]

    filtered = validator._filter_drawings_for_validation(
        drawings,
        extraction_diagnostics={
            "source_kind": "pdf",
            "pages": [
                {"page_number": 1, "strategy": "wall-title-regions"},
                {"page_number": 2, "strategy": "image-drawings"},
            ],
        },
        filename="sheet.pdf",
    )

    assert [(drawing.page_number, drawing.drawing_index) for drawing in filtered] == [(1, 1), (1, 2)]


def test_validate_document_optimized_uses_wall_only_filtered_drawings(monkeypatch):
    validator = OptimizedRoofValidator("test-key", "https://example.com", "test-model", "test-model")
    drawings = [
        image_utils.ExtractedDrawing(b"a", 1, 1, "pdf"),
        image_utils.ExtractedDrawing(b"b", 1, 2, "pdf"),
    ]

    monkeypatch.setattr(
        validator,
        "_read_upload_bytes",
        lambda image_file: b"pdf-bytes",
    )
    monkeypatch.setattr(
        "agents.optimized_orchestrator.extract_document_drawings_with_diagnostics",
        lambda _bytes: (
            drawings,
            {"source_kind": "pdf", "pages": [{"page_number": 1}]},
        ),
    )
    monkeypatch.setattr(
        validator,
        "_filter_drawings_for_validation",
        lambda items, extraction_diagnostics, filename=None: [items[1]],
    )
    monkeypatch.setattr(
        validator,
        "_validate_drawings",
        lambda items, filename=None: [{
            "success": True,
            "drawing_index": items[0].drawing_index,
            "source_page": 1,
            "processing_time": 1.0,
        }],
    )

    result = validator.validate_document_optimized(b"input", filename="sheet.pdf")

    assert result["total_drawings"] == 1
    assert result["filtered_from_total_drawings"] == 2
    assert result["results"][0]["drawing_index"] == 2


def test_nano_models_use_compact_prompt_and_larger_token_budget():
    validator = OptimizedRoofValidator("test-key", "https://example.com", "gpt-5-nano", "gpt-5-nano")
    validator.max_completion_tokens = 4000

    assert validator._should_use_compact_prompt() is True
    assert validator._completion_token_budget() == 6000
    assert "Keep the total response under 900 words." in validator._build_validation_prompt(compact=True)


def test_request_validation_response_retries_after_empty_length_truncation(monkeypatch):
    validator = OptimizedRoofValidator("test-key", "https://example.com", "gpt-4.1", "gpt-4.1")
    validator.max_completion_tokens = 4000
    calls = []

    class DummyMessage:
        def __init__(self, content):
            self.content = content
            self.refusal = None

    class DummyChoice:
        def __init__(self, content, finish_reason):
            self.message = DummyMessage(content)
            self.finish_reason = finish_reason

    class DummyUsage:
        total_tokens = 123

    class DummyResponse:
        def __init__(self, content, finish_reason):
            self.choices = [DummyChoice(content, finish_reason)]
            self.usage = DummyUsage()

    responses = [
        DummyResponse("", "length"),
        DummyResponse("STEP 2: FBC-R 2023 COMPLIANCE VALIDATION\nOVERALL_COMPLIANCE_STATUS: REQUIRES FURTHER REVIEW", "stop"),
    ]

    def fake_chat_completions_create_compat(client, **kwargs):
        calls.append(kwargs)
        return responses[len(calls) - 1]

    monkeypatch.setattr("agents.optimized_orchestrator.chat_completions_create_compat", fake_chat_completions_create_compat)

    response = validator._request_validation_response(
        optimized_prompt="initial prompt",
        base64_image="abc123",
    )

    assert len(calls) == 2
    assert calls[0]["max_completion_tokens"] == 4000
    assert calls[1]["max_completion_tokens"] == 6000
    assert "Keep the total response under 900 words." in calls[1]["messages"][0]["content"][0]["text"]
    assert response.choices[0].finish_reason == "stop"
