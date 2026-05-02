"""
Optimized Roof Validation Orchestrator
Single GPT-5 call for extraction + compliance with wall-section awareness
"""

from typing import Dict, Optional, Any, List
import time
import logging
import base64
import os
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI
from PIL import Image

from .image_utils import extract_document_drawings_with_diagnostics, ExtractedDrawing, ExtractionMode
from .openai_compat import chat_completions_create_compat
from .validation_report_formatter import (
    normalize_validation_report,
    apply_section_label_from_extraction,
)

logger = logging.getLogger(__name__)
REPORT_IMAGE_MAX_SIZE = (1100, 1100)
REPORT_IMAGE_QUALITY = 70
WALL_CLASSIFICATION_MAX_TOKENS = 80
NANO_MIN_COMPLETION_TOKENS = 6000


class OptimizedRoofValidator:
    """
    Optimized single-call validator using OpenAI GPT-5 for both image analysis and
    building-code validation. Intended for quick-turn demos where cost transparency
    and latency matter more than step-by-step orchestration.
    """
    
    def __init__(
        self,
        openai_api_key: str,
        api_base: str = "https://api.openai.com/v1",
        main_model: str = "gpt-5.1",
        summary_model: str = "gpt-5-mini"
    ):
        self.client = OpenAI(api_key=openai_api_key, base_url=api_base)
        self.model = main_model
        self.summary_model = summary_model
        self.max_completion_tokens = int(os.getenv("MAX_COMPLETION_TOKENS", "6000"))
        self.max_parallel_drawings = max(1, int(os.getenv("MAX_PARALLEL_DRAWING_VALIDATIONS", "6")))
        self.max_parallel_classifications = max(1, int(os.getenv("MAX_PARALLEL_DRAWING_CLASSIFICATIONS", "6")))
        logger.info(f"OptimizedRoofValidator initialized with model: {self.model}")
    
    def validate_roof_design_optimized(
        self,
        image_file,
        filename: Optional[str] = None,
        extraction_mode: ExtractionMode = "wall-sections",
    ) -> Dict[str, Any]:
        """
        Single optimized call using GPT-5 for both extraction AND validation.
        """
        document_result = self.validate_document_optimized(
            image_file,
            filename=filename,
            extraction_mode=extraction_mode,
        )
        if document_result["results"]:
            first_result = document_result["results"][0].copy()
            first_result["total_drawings"] = document_result["total_drawings"]
            first_result["successful_drawings"] = document_result["successful_drawings"]
            first_result["failed_drawings"] = document_result["failed_drawings"]
            first_result["results"] = document_result["results"]
            return first_result

        return {
            "success": False,
            "error": "No drawings were extracted from the uploaded document",
            "processing_time": document_result["processing_time"],
            "total_drawings": 0,
            "successful_drawings": 0,
            "failed_drawings": 0,
            "results": [],
        }

    def validate_document_optimized(
        self,
        image_file,
        filename: Optional[str] = None,
        extraction_mode: ExtractionMode = "wall-sections",
    ) -> Dict[str, Any]:
        """
        Validate each extracted drawing from an image or PDF independently.
        """
        start_time = time.time()

        try:
            logger.info(f"Starting optimized document validation for: {filename or 'uploaded_image'}")
            upload_bytes = self._read_upload_bytes(image_file)
            try:
                extracted_drawings, extraction_diagnostics = extract_document_drawings_with_diagnostics(
                    upload_bytes,
                    extraction_mode=extraction_mode,
                )
            except TypeError as exc:
                if "extraction_mode" not in str(exc):
                    raise
                extracted_drawings, extraction_diagnostics = extract_document_drawings_with_diagnostics(upload_bytes)
            filtered_drawings = self._filter_drawings_for_validation(
                extracted_drawings,
                extraction_diagnostics=extraction_diagnostics,
                filename=filename,
            )
            results = self._validate_drawings(filtered_drawings, filename=filename)
            page_diagnostics = {
                page.get("page_number"): page
                for page in extraction_diagnostics.get("pages", [])
                if isinstance(page, dict)
            }
            for result in results:
                page_number = result.get("source_page")
                if page_number in page_diagnostics:
                    result["extraction_page_diagnostics"] = page_diagnostics[page_number]

            successful_drawings = len([result for result in results if result.get("success")])
            return {
                "success": successful_drawings > 0,
                "filename": filename,
                "total_drawings": len(results),
                "successful_drawings": successful_drawings,
                "failed_drawings": len(results) - successful_drawings,
                "filtered_from_total_drawings": len(extracted_drawings),
                "extraction_mode": extraction_mode,
                "extraction_diagnostics": extraction_diagnostics,
                "results": results,
                "processing_time": time.time() - start_time,
            }

        except Exception as e:
            logger.error(f"Optimized document validation failed: {str(e)}")
            return {
                "success": False,
                "filename": filename,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "total_drawings": 0,
                "successful_drawings": 0,
                "failed_drawings": 0,
                "filtered_from_total_drawings": 0,
                "extraction_mode": extraction_mode,
                "extraction_diagnostics": {
                    "source_kind": "unknown",
                    "extraction_mode": extraction_mode,
                    "pages": [],
                    "total_drawings": 0,
                },
                "results": [],
            }

    def _filter_drawings_for_validation(
        self,
        drawings: List[ExtractedDrawing],
        *,
        extraction_diagnostics: Dict[str, Any],
        filename: Optional[str] = None,
    ) -> List[ExtractedDrawing]:
        source_kind = extraction_diagnostics.get("source_kind")
        extraction_mode = extraction_diagnostics.get("extraction_mode", "wall-sections")
        if extraction_mode == "direct":
            return drawings
        if source_kind != "pdf" or len(drawings) <= 1:
            return drawings

        page_strategies = {
            page.get("page_number"): page.get("strategy")
            for page in extraction_diagnostics.get("pages", [])
            if isinstance(page, dict)
        }
        title_filtered_drawings = [
            drawing for drawing in drawings
            if page_strategies.get(drawing.page_number) == "wall-title-regions"
        ]
        if title_filtered_drawings:
            logger.info(
                "Using deterministic wall-title extraction for %s drawing(s) from %s for %s",
                len(title_filtered_drawings),
                len(drawings),
                filename or "uploaded_pdf",
            )
            return title_filtered_drawings

        wall_drawings = self._select_wall_section_drawings(drawings, filename=filename)
        if wall_drawings:
            logger.info(
                "Selected %s wall-section drawing(s) from %s extracted PDF drawing(s) for %s",
                len(wall_drawings),
                len(drawings),
                filename or "uploaded_pdf",
            )
            return wall_drawings

        logger.warning(
            "No wall-section drawings detected in %s extracted PDF drawing(s) for %s",
            len(drawings),
            filename or "uploaded_pdf",
        )
        return []

    def _select_wall_section_drawings(
        self,
        drawings: List[ExtractedDrawing],
        *,
        filename: Optional[str] = None,
    ) -> List[ExtractedDrawing]:
        if len(drawings) <= 1:
            return drawings

        if self.max_parallel_classifications <= 1 or len(drawings) == 1:
            return [
                drawing for drawing in drawings
                if self._is_wall_section_drawing(drawing, filename=filename)
            ]

        selected: List[tuple[int, ExtractedDrawing]] = []
        max_workers = min(self.max_parallel_classifications, len(drawings))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(self._is_wall_section_drawing, drawing, filename=filename): index
                for index, drawing in enumerate(drawings)
            }
            for future in as_completed(future_map):
                if future.result():
                    index = future_map[future]
                    selected.append((index, drawings[index]))

        selected.sort(key=lambda item: item[0])
        return [drawing for _, drawing in selected]

    def _is_wall_section_drawing(self, drawing: ExtractedDrawing, *, filename: Optional[str] = None) -> bool:
        base64_image = base64.b64encode(drawing.image_bytes).decode("utf-8")
        prompt = """
You are classifying one extracted architectural panel from a larger PDF sheet.
The crop includes extra space below the panel so a title/label under the drawing may be visible.

Decide if this panel should be analyzed as a WALL SECTION.

Respond with exactly one label and nothing else:
- WALL_SECTION
- NOT_WALL_SECTION

Rules:
- Prefer the visible title/label under or above the panel over the drawing content.
- Use WALL_SECTION only when the visible title/label explicitly contains "wall" or the panel is unmistakably a wall section detail.
- If the title mentions roof, framing, truss, plan, eave, detail, or section without wall, respond NOT_WALL_SECTION.
- If the crop is ambiguous, respond NOT_WALL_SECTION.
"""

        try:
            response = chat_completions_create_compat(
                self.client,
                model=self.summary_model,
                max_completion_tokens=WALL_CLASSIFICATION_MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                        ],
                    }
                ],
            )
            content = response.choices[0].message.content or ""
            normalized = content.strip().upper()
            first_line = normalized.splitlines()[0].strip() if normalized else ""
            is_wall = first_line == "WALL_SECTION"
            logger.info(
                "Wall-section filter for %s (%s): %s",
                drawing.label,
                filename or "uploaded_pdf",
                first_line or "EMPTY",
            )
            return is_wall
        except Exception as exc:
            logger.warning(
                "Wall-section classifier failed for %s (%s): %s",
                drawing.label,
                filename or "uploaded_pdf",
                exc,
            )
            return False

    def _validate_drawings(
        self,
        drawings: List[ExtractedDrawing],
        *,
        filename: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if len(drawings) <= 1 or self.max_parallel_drawings <= 1:
            return [
                self._validate_extracted_drawing(drawing, filename=filename)
                for drawing in drawings
            ]

        max_workers = min(self.max_parallel_drawings, len(drawings))
        indexed_results: List[tuple[int, Dict[str, Any]]] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(self._validate_extracted_drawing, drawing, filename=filename): index
                for index, drawing in enumerate(drawings)
            }
            for future in as_completed(future_map):
                indexed_results.append((future_map[future], future.result()))

        indexed_results.sort(key=lambda item: item[0])
        return [result for _, result in indexed_results]

    def _validate_extracted_drawing(self, drawing: ExtractedDrawing, filename: Optional[str] = None) -> Dict[str, Any]:
        drawing_start_time = time.time()

        try:
            base64_image = base64.b64encode(drawing.image_bytes).decode("utf-8")
            report_image_data = self._build_report_image_data(drawing.image_bytes)
            optimized_prompt = self._build_validation_prompt(compact=self._should_use_compact_prompt())

            response = self._request_validation_response(
                optimized_prompt=optimized_prompt,
                base64_image=base64_image,
            )

            processing_time = time.time() - drawing_start_time
            total_tokens = response.usage.total_tokens if response.usage else 0

            analysis_result = self._extract_response_text(response)
            finish_reason = response.choices[0].finish_reason

            logger.info(
                "Validated %s with %s in %.2fs (%s tokens, finish=%s)",
                drawing.label,
                self.model,
                processing_time,
                total_tokens,
                finish_reason if response.choices else "unknown",
            )
            logger.debug(
                "Validation output for %s: %s chars",
                drawing.label,
                len(analysis_result) if analysis_result else 0,
            )
            logger.debug(
                "Validation preview for %s: %s",
                drawing.label,
                analysis_result[:200] if analysis_result else "EMPTY",
            )

            if not analysis_result or not analysis_result.strip():
                logger.error(f"Empty response from model {self.model}")
                logger.error(f"Finish reason: {finish_reason}")
                logger.error(f"Response has refusal: {hasattr(response.choices[0].message, 'refusal')}")
                if hasattr(response.choices[0].message, 'refusal') and response.choices[0].message.refusal:
                    logger.error(f"Refusal message: {response.choices[0].message.refusal}")
                raise RuntimeError(f"Optimized validator returned empty output. Finish reason: {finish_reason}")

            if finish_reason == 'length':
                logger.warning(f"Response was truncated due to length limit. Consider increasing max_completion_tokens.")

            analysis_text, validation_text = self._split_sections(analysis_result)
            validation_text = normalize_validation_report(validation_text, analysis_text)
            validation_text = apply_section_label_from_extraction(validation_text, analysis_text)

            display_name = filename or "uploaded_image"
            if drawing.source_kind == "pdf":
                display_name = f"{display_name} - {drawing.label}"

            return {
                "success": True,
                "filename": display_name,
                "source_filename": filename or "uploaded_image",
                "source_page": drawing.page_number,
                "drawing_index": drawing.drawing_index,
                "drawing_label": drawing.label,
                "validation_report": validation_text,
                "processing_time": processing_time,
                "cache_key": f"{filename or 'optimized'}_{drawing.page_number}_{drawing.drawing_index}_{int(time.time())}",
                "report_image_data": report_image_data,
            }

        except Exception as e:
            logger.error(f"Optimized validation failed: {str(e)}")
            return {
                "success": False,
                "filename": f"{filename or 'uploaded_image'} - {drawing.label}" if drawing.source_kind == "pdf" else (filename or "uploaded_image"),
                "source_filename": filename or "uploaded_image",
                "source_page": drawing.page_number,
                "drawing_index": drawing.drawing_index,
                "drawing_label": drawing.label,
                "error": str(e),
                "processing_time": time.time() - drawing_start_time
            }

    def _build_validation_prompt(self, *, compact: bool) -> str:
        if compact:
            return """
You are an expert structural engineer and Florida Building Code specialist.

TASK: Analyze this architectural drawing crop and validate roof design compliance with FBC-R 2023.

Return a concise response. Keep the total response under 900 words.
Focus only on the most important visible roof-related information.

Use exactly this format:

STEP 1: ROOF DESIGN EXTRACTION
DRAWING_TYPE: [wall section / roof framing / eave detail / combination]
VISIBLE_ROOF_ELEMENTS:
- Framing: [visible info or "not shown"]
- Sheathing: [exact sheathing note text copied verbatim from the drawing, including panel type, thickness, nail type, and spacing, or "not shown"]
- Covering: [visible info or "not shown"]
- Connections: [visible info or "not shown"]
- Roof_Pitch: [exact slope callout such as "3/12" or "not shown"]
- Edge_Details: [fascia/soffit/drip edge info or "not shown"]
- Critical_Specs: [up to 5 exact quotes or "not shown"]

STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
FRAMING:
- Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
- Code_Reference: [FBC-R section]
- Analysis: [1 short sentence]
- Required_Corrections: [fix or "None"]

SHEATHING:
- Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
- Code_Reference: [FBC-R section]
- Evidence: [repeat the exact sheathing note text verbatim from STEP 1 or "not shown"]
- Analysis: [1 short sentence]
- Required_Corrections: [fix or "None"]

CONNECTIONS_AND_WIND:
- Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
- Code_Reference: [FBC-R section]
- Analysis: [1 short sentence]
- Required_Corrections: [fix or "None"]

COVERING_AND_EDGE:
- Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
- Code_Reference: [FBC-R section]
- Analysis: [1 short sentence]
- Required_Corrections: [fix or "None"]

OVERALL_COMPLIANCE_STATUS: [COMPLIANT / NON-COMPLIANT / REQUIRES FURTHER REVIEW]
CRITICAL_FINDINGS: [short list or "None"]
REQUIRED_CORRECTIONS: [short list or "None"]
PROFESSIONAL_RECOMMENDATION: [2-3 short sentences]
VALIDATION_METADATA:
- Code_Edition: Florida Building Code - Residential 2023
- Confidence: [HIGH / MEDIUM / LOW]

STRICT RULES:
- Quote exact text only when visible
- Inspect roof-line annotations, rise/run triangles, and small callouts before writing "not shown"
- For Sheathing, copy the exact visible note text verbatim; do not summarize panel thickness, nail type, or spacing
- If a sheathing fastening schedule is visible, repeat the same exact text in SHEATHING Evidence
- If any pitch marker shows a ratio like 3/12 or 3:12, copy it exactly
- If Roof_Pitch is "not shown", mention that missing pitch explicitly in CRITICAL_FINDINGS and do not treat roof covering compliance as resolved
- Do not mark SHEATHING as COMPLIANT unless the drawing shows panel type/thickness, fastening, and at least one support-context fact such as spacing/span/edge support
- Allowed status words are exactly: COMPLIANT, NON-COMPLIANT, REQUIRES REVIEW
- Never invent variants such as "requisites review" or similar malformed labels
- Do not recommend products, connector types, member sizes, or thickness upgrades unless they are directly supported by visible evidence and code logic stated in the drawing context
- Cite specific FBC-R section numbers
- Mark "not shown" for missing info
- Mark "REQUIRES REVIEW" for ambiguity
- Output ONLY the requested format
"""

        return """
You are an expert structural engineer and Florida Building Code specialist.

TASK: Analyze this architectural drawing crop and validate roof design compliance with FBC-R 2023.

Complete BOTH steps in a single evidence-based response.
Be thorough rather than brief.
Include every visible roof-related specification that can materially affect code review.
Use exact quoted values from the drawing wherever they are visible.

================================================================================
STEP 1: ROOF DESIGN EXTRACTION
================================================================================

Extract only high-signal roof information. Format exactly as below:

DRAWING_TYPE: [wall section / roof framing / eave detail / combination]
SECTIONS_ANALYZED: [count]

SECTION_1:
  Label: [identifier or "Unlabeled Section 1"]
  Framing: [key visible framing info or "not shown"]
  Sheathing: [exact sheathing note text copied verbatim from the drawing, including panel type, thickness, nail type, spacing, and any T&G/edge/field wording, or "not shown"]
  Covering: [key visible roof covering/underlayment info or "not shown"]
  Connections: [key visible roof-to-wall/uplift info or "not shown"]
  Roof_Pitch: [exact slope callout such as "3/12" or "not shown"]
  Edge_Details: [fascia/soffit/drip edge info or "not shown"]
  Notes: [4-8 important visible notes/dimensions/code refs]

[Repeat only for additional clearly distinct sections]

CRITICAL_SPECIFICATIONS:
  - [6-10 most important visible specs with exact quotes]

================================================================================
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
================================================================================

For EACH section above, validate concisely against Florida Residential Building Code 2023:

SECTION: [identifier]

FRAMING:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
  Code_Reference: [FBC-R §R802.x]
  Evidence: [exact visible framing facts or "not shown"]
  Analysis: [specific reasoning tied to the visible facts]
  Required_Corrections: [fix or "None"]

SHEATHING:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
  Code_Reference: [FBC-R §R803.x]
  Evidence: [repeat the exact sheathing note text verbatim from STEP 1, not a summary, or "not shown"]
  Analysis: [specific reasoning tied to the visible facts]
  Required_Corrections: [fix or "None"]

CONNECTIONS_AND_WIND:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
  Code_Reference: [FBC-R §R802.11 / §R301.2.1]
  Evidence: [exact visible connection/wind facts or "not shown"]
  Analysis: [specific reasoning tied to the visible facts]
  Required_Corrections: [fix or "None"]

COVERING_AND_EDGE:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
  Code_Reference: [FBC-R §R905.x]
  Evidence: [exact visible covering/underlayment/edge facts or "not shown"]
  Analysis: [specific reasoning tied to the visible facts]
  Required_Corrections: [fix or "None"]

SECTION_SUMMARY:
  Overall: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
  Critical_Issues: [short list or "None"]

[Repeat for each section]

================================================================================
OVERALL_COMPLIANCE_STATUS: [COMPLIANT / NON-COMPLIANT / REQUIRES FURTHER REVIEW]
================================================================================

CRITICAL_FINDINGS:
  Major_Violations: [all NON-COMPLIANT items or "None"]
  Needs_Review: [all REQUIRES REVIEW items or "None"]
  Missing_Info: [critical specs not shown or "None"]

REQUIRED_CORRECTIONS:
  High_Priority: [fixes needed or "None"]
  Recommended: [improvements or "None"]

PROFESSIONAL_RECOMMENDATION:
  [3-5 sentences: overall status, key issues, permit readiness]

VALIDATION_METADATA:
  Code_Edition: Florida Building Code - Residential 2023
  Chapters: 8 (Roof-Ceiling), 9 (Roof Assemblies)
  Sections_Analyzed: [count]
  Confidence: [HIGH / MEDIUM / LOW]

STRICT RULES:
- Quote exact text from drawing
- Review every visible roof segment and section crop before deciding a spec is missing
- Inspect small roof-line annotations, slope triangles, and rise/run markers explicitly
- For Sheathing, copy the note verbatim from the drawing; do not paraphrase panel type, thickness, nail type, edge spacing, or field spacing
- If multiple sheathing notes are visible, include the full exact schedule text that governs the shown roof/wall section
- In SHEATHING Evidence, repeat the exact sheathing note text from STEP 1 verbatim rather than summarizing it
- If a pitch ratio such as 3/12 or 3:12 is visible anywhere in the section, include it exactly in Roof_Pitch and CRITICAL_SPECIFICATIONS
- If Roof_Pitch is "not shown", list that missing pitch explicitly in CRITICAL_FINDINGS.Missing_Info and do not treat roof covering compliance as resolved
- Do not use placeholders such as "exact citation verification needed" or generic filler text
- Do not claim a block was analyzed unless you provide visible evidence for it
- If information is incomplete, say exactly what is visible and exactly what remains missing
- Do not mark SHEATHING as COMPLIANT unless visible evidence includes panel type/thickness, fastening schedule, and support context such as spacing, span, or edge support
- Do not mark CONNECTIONS_AND_WIND as COMPLIANT unless the drawing shows an identifiable uplift connector/load-path basis, not just toe-nails
- Do not mark COVERING_AND_EDGE as COMPLIANT when low-slope roof approval, underlayment compliance, or current-code basis is missing or ambiguous
- Allowed status words are exactly: COMPLIANT, NON-COMPLIANT, REQUIRES REVIEW
- Never invent variants such as "requisites review" or similar malformed labels
- Do not prescribe upgrades, products, or connector systems unless they are directly justified by visible evidence and the cited code section
- Cite specific FBC-R section numbers
- Use roof-code chapters only for roof checks:
  - Framing: R802.*
  - Sheathing: R803.*
  - Covering/underlayment: R905.* (and R903.* if needed)
  - Wind: R301.* (and related roof load-path checks)
- Do NOT cite floor-framing sections (e.g., R502.*) for roof compliance.
- Mark "not shown" for missing info - never guess
- Mark "REQUIRES REVIEW" for partial/ambiguous data
- Prioritize life safety (connections, uplift, wind)
- Focus on ROOF elements primarily
- Treat this image as one isolated drawing/detail extracted from a larger plan sheet
- Output ONLY the requested format with exact section labels. Do not output alternative formats
  like "Validation Checklist" or renumbered headings.
"""

    def _request_validation_response(self, *, optimized_prompt: str, base64_image: str):
        response = chat_completions_create_compat(
            self.client,
            model=self.model,
            max_completion_tokens=self._completion_token_budget(),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": optimized_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                        }
                    ]
                }
            ]
        )

        finish_reason = response.choices[0].finish_reason if response.choices else None
        analysis_result = self._extract_response_text(response)
        if finish_reason == "length" and not (analysis_result or "").strip():
            logger.warning("Retrying validation with compact prompt after empty length-truncated response from %s", self.model)
            response = chat_completions_create_compat(
                self.client,
                model=self.model,
                max_completion_tokens=max(self._completion_token_budget(), NANO_MIN_COMPLETION_TOKENS),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self._build_validation_prompt(compact=True)
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                            }
                        ]
                    }
                ]
            )

        return response

    def _completion_token_budget(self) -> int:
        if "nano" in self.model.lower():
            return max(self.max_completion_tokens, NANO_MIN_COMPLETION_TOKENS)
        return self.max_completion_tokens

    def _should_use_compact_prompt(self) -> bool:
        # Use the same stricter compact prompt for all models to keep the
        # report schema consistent across providers and model sizes.
        return True

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        content = response.choices[0].message.content if response.choices else ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif hasattr(item, "type") and getattr(item, "type") == "text":
                    text_parts.append(getattr(item, "text", ""))
            return "".join(text_parts)
        return str(content or "")

    @staticmethod
    def _read_upload_bytes(image_file) -> bytes:
        if hasattr(image_file, "read"):
            data = image_file.read()
            if hasattr(image_file, "seek"):
                image_file.seek(0)
            return data
        return image_file

    @staticmethod
    def _build_report_image_data(image_bytes: bytes) -> str:
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        if image.size[0] > REPORT_IMAGE_MAX_SIZE[0] or image.size[1] > REPORT_IMAGE_MAX_SIZE[1]:
            image.thumbnail(REPORT_IMAGE_MAX_SIZE, Image.Resampling.LANCZOS)

        output = io.BytesIO()
        image.save(output, format="JPEG", quality=REPORT_IMAGE_QUALITY, optimize=True)
        encoded = base64.b64encode(output.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"

    @staticmethod
    def _split_sections(full_text: str) -> tuple[str, str]:
        # Updated for new roof-focused prompts
        step1_marker = "STEP 1: ROOF DESIGN EXTRACTION"
        step2_marker = "STEP 2: FBC-R 2023 COMPLIANCE VALIDATION"
        
        extraction_text = full_text
        validation_text = ""
        
        if step2_marker in full_text:
            parts = full_text.split(step2_marker, 1)
            extraction_text = parts[0].strip()
            validation_text = f"{step2_marker}{parts[1]}".strip()
        return extraction_text.strip(), validation_text.strip()

    # Removed _extract_text - now using response.choices[0].message.content directly
