"""
Optimized Roof Validation Orchestrator
Single GPT-5 call for extraction + compliance with wall-section awareness
"""

from typing import Dict, Optional, Any
import time
import logging
import base64

from openai import OpenAI

from .image_utils import document_bytes_to_image

logger = logging.getLogger(__name__)


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
        self.max_completion_tokens = 16000  # Increased for large PDFs and comprehensive reports
        logger.info(f"OptimizedRoofValidator initialized with model: {self.model}")
    
    def validate_roof_design_optimized(self, image_file, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Single optimized call using GPT-5 for both extraction AND validation.
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting optimized validation for: {filename or 'uploaded_image'}")
            
            # Normalize upload -> base64
            upload_bytes = self._read_upload_bytes(image_file)
            normalized_bytes = document_bytes_to_image(upload_bytes)
            base64_image = base64.b64encode(normalized_bytes).decode("utf-8")
            
            optimized_prompt = """
You are an expert structural engineer and Florida Building Code specialist.

TASK: Analyze this architectural drawing and validate roof design compliance with FBC-R 2023.

Complete BOTH steps in a single response:

================================================================================
STEP 1: ROOF DESIGN EXTRACTION
================================================================================

Extract all roof-related information. Format exactly as below:

DRAWING_TYPE: [wall section / roof framing / eave detail / combination]

NUMBER_OF_SECTIONS: [count of distinct sections/details]

---
SECTION_1:
  Label: [identifier or "Unlabeled Section 1"]
  
  ROOF_FRAMING:
    Type: [trusses/rafters/joists or "not shown"]
    Size: [dimensions]
    Spacing: [O.C. spacing]
    Bearing_Elevation: [height or "not shown"]
  
  ROOF_SHEATHING:
    Material: [OSB/plywood or "not shown"]
    Thickness: [measurement]
    Fasteners: [type, size, pattern]
  
  ROOF_COVERING:
    Type: [material]
    Underlayment: [type]
    Installation_Notes: [FBC refs, manufacturer specs]
  
  ROOF_SLOPE:
    Pitch: [ratio like "3:12"]
  
  ROOF_TO_WALL_CONNECTION:
    Hardware: [hurricane ties, straps, etc.]
    Fastening: [connection details]
  
  ROOF_INSULATION:
    Type: [material]
    R_Value: [R-value]
    Ventilation: [vented/non-vented]
  
  ROOF_EDGE_DETAILS:
    Fascia: [spec]
    Soffit: [spec]
    Drip_Edge: [type]
  
  GENERAL_NOTES:
    - [all visible notes, code refs, dimensions]

---
[Repeat for additional sections]

CRITICAL_SPECIFICATIONS:
  - [5-7 most important specs with exact quotes]

================================================================================
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
================================================================================

For EACH section above, validate against Florida Residential Building Code 2023:

---
SECTION: [identifier]

ROOF_FRAMING_COMPLIANCE:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
  Code_Reference: [FBC-R §R802.x, Table numbers]
  Analysis: |
    Design: [quote spec]
    Code Requires: [requirement]
    Determination: [why compliant/non-compliant]
  Required_Corrections: [fixes or "None"]

ROOF_SHEATHING_COMPLIANCE:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
  Code_Reference: [FBC-R §R803.x]
  Analysis: |
    Sheathing: [quote spec]
    Fastening: [quote pattern]
    Code Requires: [requirement]
    Determination: [reasoning]
  Required_Corrections: [fixes or "None"]

ROOF_TO_WALL_CONNECTION_COMPLIANCE:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
  Code_Reference: [FBC-R §R802.11]
  Analysis: |
    Hardware: [quote]
    Code Requires: [based on wind/loads]
    Determination: [reasoning]
  Required_Corrections: [fixes or "None"]

ROOF_COVERING_COMPLIANCE:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
  Code_Reference: [FBC-R §R905.x]
  Analysis: |
    Material: [quote]
    Underlayment: [quote]
    Code Requires: [for slope/type]
    Determination: [reasoning]
  Required_Corrections: [fixes or "None"]

WIND_RESISTANCE_COMPLIANCE:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
  Code_Reference: [FBC-R §R301.2.1]
  Analysis: |
    Hurricane ties: [quote]
    Uplift resistance: [evaluation]
    Determination: [reasoning]
  Required_Corrections: [fixes or "None"]

SECTION_SUMMARY:
  Overall: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
  Critical_Issues: [list or "None"]

---
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
  [1-2 paragraphs: overall status, key issues, permit readiness]

VALIDATION_METADATA:
  Code_Edition: Florida Building Code - Residential 2023
  Chapters: 8 (Roof-Ceiling), 9 (Roof Assemblies)
  Sections_Analyzed: [count]
  Confidence: [HIGH / MEDIUM / LOW]

STRICT RULES:
- Quote exact text from drawing
- Cite specific FBC-R section numbers
- Mark "not shown" for missing info - never guess
- Mark "REQUIRES REVIEW" for partial/ambiguous data
- Prioritize life safety (connections, uplift, wind)
- Focus on ROOF elements primarily
"""

            # Single API call for both analysis and validation
            response = self.client.chat.completions.create(
                model=self.model,
                max_completion_tokens=self.max_completion_tokens,
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
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ]
            )
            
            # Calculate metrics
            processing_time = time.time() - start_time
            total_tokens = response.usage.total_tokens if response.usage else 0
            
            # Log performance metrics
            logger.info(f"Optimized Validation Complete:")
            logger.info(f"Model: {self.model}")
            logger.info(f"Tokens Used: {total_tokens}")
            logger.info(f"Processing Time: {processing_time:.2f}s")
            logger.info(f"Finish Reason: {response.choices[0].finish_reason if response.choices else 'unknown'}")
            
            # Extract response content directly
            analysis_result = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            # Debug logging
            logger.info(f"Response content length: {len(analysis_result) if analysis_result else 0} chars")
            logger.info(f"Response preview: {analysis_result[:200] if analysis_result else 'EMPTY'}...")
            
            if not analysis_result or not analysis_result.strip():
                logger.error(f"Empty response from model {self.model}")
                logger.error(f"Finish reason: {finish_reason}")
                logger.error(f"Response has refusal: {hasattr(response.choices[0].message, 'refusal')}")
                if hasattr(response.choices[0].message, 'refusal') and response.choices[0].message.refusal:
                    logger.error(f"Refusal message: {response.choices[0].message.refusal}")
                raise RuntimeError(f"Optimized validator returned empty output. Finish reason: {finish_reason}")
            
            # Warn if response was truncated
            if finish_reason == 'length':
                logger.warning(f"Response was truncated due to length limit. Consider increasing max_completion_tokens.")
            
            analysis_text, validation_text = self._split_sections(analysis_result)
            
            return {
                "success": True,
                "analysis": analysis_text,
                "validation_report": validation_text,
                "compliance_report": analysis_result,
                "processing_time": processing_time,
                "cache_key": filename or f"optimized_{int(time.time())}"
            }
            
        except Exception as e:
            logger.error(f"Optimized validation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }

    @staticmethod
    def _read_upload_bytes(image_file) -> bytes:
        if hasattr(image_file, "read"):
            data = image_file.read()
            if hasattr(image_file, "seek"):
                image_file.seek(0)
            return data
        return image_file

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