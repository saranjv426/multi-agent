"""
Roof Design Analyzer - Agent 1
Extracts structural information from roof design drawings using GPT-4o Vision API
"""

import base64
import logging
import time
from typing import Dict, Optional, Any

from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .image_utils import document_bytes_to_image
from .openai_compat import chat_completions_create_compat

class RoofDesignAnalyzer:
    """
    Agent 1: Roof Design Analyzer
    Uses OpenAI GPT-5 Vision to extract detailed structural information from design drawings.
    Optimized for dense sheets with roof + wall section details.
    """
    
    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com/v1",
        vision_model: str = "gpt-5.1"
    ):
        """Initialize the roof design analyzer with OpenAI credentials."""
        self.client = OpenAI(api_key=api_key, base_url=api_base)
        self.analysis_cache = {}
        
        # Configuration
        self.vision_model = vision_model
        self.max_completion_tokens = 4500  # allow larger extractions with lower latency
        self.temperature = 0.1  # low temperature for consistent technical analysis
        
    def encode_image(self, image_file) -> Optional[str]:
        """Convert image/PDF file to base64 string for the Vision API."""
        try:
            upload_bytes = self._read_upload_bytes(image_file)
            normalized_bytes = document_bytes_to_image(upload_bytes)
            return base64.b64encode(normalized_bytes).decode("utf-8")
        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")

    @staticmethod
    def _read_upload_bytes(image_file) -> bytes:
        if hasattr(image_file, "read"):
            data = image_file.read()
            if hasattr(image_file, "seek"):
                image_file.seek(0)
            return data
        return image_file

    def analyze_roof_design(self, image_file, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze roof design image and extract structural information.
        
        Args:
            image_file: Image file (bytes or file-like object)
            filename: Optional filename for caching
            
        Returns:
            Dict containing analysis results and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting roof design analysis for file: {filename or 'uploaded_image'}")
            
            # Encode image for API
            base64_image = self.encode_image(image_file)
            if not base64_image:
                raise Exception("Failed to encode image")
            
            # Vision prompt tuned for roof detail extraction from architectural sections
            analysis_prompt = """
You are an expert structural engineer specializing in residential roof construction analysis.

TASK: Extract ALL roof-related information from this architectural drawing.

This drawing may show:
- Wall sections with roof details
- Roof framing plans
- Eave/overhang details  
- Roof-to-wall connections
- Multiple sections/details on one sheet

OUTPUT STRUCTURE (use exactly this format):

DRAWING_TYPE: [wall section / roof framing / eave detail / combination]

NUMBER_OF_SECTIONS: [how many distinct sections or details are visible]

---
SECTION_1:
  Label: [section identifier if visible, otherwise "Unlabeled Section 1"]
  
  ROOF_FRAMING:
    Type: [trusses / rafters / joists / not shown]
    Size: [dimensions if visible, e.g., "2x10", "prefab wood trusses"]
    Spacing: [e.g., "24" O.C.", "2'-0" O.C.", or "not shown"]
    Bearing_Elevation: [height if noted, e.g., "12'-0" A.F.F." or "not shown"]
    Notes: [any framing notes, bracing requirements, or "none"]
  
  ROOF_SHEATHING:
    Material: [OSB / plywood / not shown]
    Thickness: [e.g., "7/16"", "1/2"", or "not shown"]
    Fasteners: [type, size, pattern - e.g., "8D ring shank nails @ 6" O.C." or "not shown"]
    Notes: [any sheathing-specific callouts or "none"]
  
  ROOF_COVERING:
    Type: [asphalt shingles / metal / tile / not shown]
    Spec: [e.g., "Galvalume metal", "architectural shingles", or "not shown"]
    Underlayment: [e.g., "#15 felt", "self-adhering synthetic", or "not shown"]
    Installation_Notes: [manufacturer requirements, FBC references, or "none"]
  
  ROOF_SLOPE:
    Pitch: [e.g., "3:12", "5:12", "12/3", or "not shown"]
    Degrees: [if shown in degrees, or "not shown"]
  
  ROOF_TO_WALL_CONNECTION:
    Hardware: [e.g., "Simpson H10 hurricane ties", "metal straps", or "not shown"]
    Fastening: [connection details if visible, or "not shown"]
    Load_Path: [how roof loads transfer to wall, or "not shown"]
  
  ROOF_INSULATION:
    Type: [spray foam / batt / rigid / not shown]
    R_Value: [e.g., "R-38", "R-30", or "not shown"]
    Location: [attic space / roof deck / not shown]
    Ventilation: [vented / non-vented attic, or "not shown"]
  
  ROOF_EDGE_DETAILS:
    Fascia: [material and size, or "not shown"]
    Soffit: [material and width, or "not shown"]
    Drip_Edge: [type if specified, or "not shown"]
    Gutter: [if shown, or "not shown"]
  
  GENERAL_NOTES:
    - [list all visible notes, callouts, dimensions related to roof]
    - [code references: FBC, manufacturer requirements]
    - [field verification notes]
    - [if none: "No additional notes"]

---
SECTION_2:
  [repeat same structure if additional sections exist]

---
[Continue for all sections/details visible]

EXTRACTION_COMPLETENESS:
  Readable_Text: [percentage estimate of text you could read clearly]
  Missing_Information: [list what roof elements are typically shown but not visible here]
  Confidence: [HIGH / MEDIUM / LOW - based on drawing quality and completeness]

CRITICAL_SPECIFICATIONS:
  [List the 5-7 most important roof specifications extracted, with exact quoted values]

STRICT RULES:
- Quote text EXACTLY as it appears (preserve case, punctuation, units)
- Mark "not shown" for any missing information - never guess or assume
- If text is illegible, note "text present but illegible"
- Include ALL visible dimensions, elevations, and measurements
- Capture all code references (FBC 2023, manufacturer specs, etc.)
- For multiple sections, analyze each one separately and completely
"""

            # Prepare the API request
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": analysis_prompt
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    ]
                }
            ]
            
            response = chat_completions_create_compat(
                self.client,
                model=self.vision_model,
                max_completion_tokens=self.max_completion_tokens,
                messages=messages
            )
            
            # Extract response content directly
            analysis_result = response.choices[0].message.content
            if not analysis_result or not analysis_result.strip():
                raise RuntimeError(f"Vision model returned empty output")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            total_tokens = response.usage.total_tokens if response.usage else 0
            
            # Log performance metrics
            logger.info(f"Agent1 Analysis Complete:")
            logger.info(f"Tokens Used: {total_tokens}")
            logger.info(f"Processing Time: {processing_time:.2f}s")
            
            # Store in cache for follow-up questions
            cache_key = filename if filename else f"image_{len(self.analysis_cache)}"
            self.analysis_cache[cache_key] = {
                'analysis': analysis_result,
                'image_data': base64_image,
                'filename': filename,
                'cost_metrics': {
                    'total_tokens': total_tokens,
                    'estimated_cost': estimated_cost,
                    'processing_time': processing_time
                }
            }
            
            return {
                'analysis': analysis_result,
                'processing_time': processing_time,
                'cache_key': cache_key,
                'success': True
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }

    def ask_follow_up_question(self, question: str, cache_key: str) -> Dict[str, Any]:
        """
        Ask follow-up questions about a previously analyzed roof design.
        
        Args:
            question: User's follow-up question
            cache_key: Reference to cached analysis
            
        Returns:
            Dict containing answer and metadata
        """
        try:
            if cache_key not in self.analysis_cache:
                raise Exception("Analysis not found in cache")
            
            cached_data = self.analysis_cache[cache_key]
            
            follow_up_prompt = f"""
Based on the roof design information extraction, answer the user's specific question about the information visible in the drawing:
- Dimensions and measurements
- Material specifications
- Hardware details
- Connection types
- Spacing information
- Technical annotations

Previous Analysis:
{cached_data['analysis']}

User Question: {question}

Provide factual responses based only on what was extracted from the drawing.
            """
            
            # Call OpenAI API for follow-up
            response = chat_completions_create_compat(
                self.client,
                model=self.vision_model,
                max_completion_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": follow_up_prompt}]
                    }
                ]
            )
            
            answer_text = response.choices[0].message.content
            if not answer_text or not answer_text.strip():
                raise RuntimeError(f"Vision follow-up returned empty output")
            
            total_tokens = response.usage.total_tokens if response.usage else 0
            
            return {
                'answer': answer_text,
                'success': True
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }

    def validate_file_type(self, file) -> tuple[bool, str]:
        """
        Validate if uploaded file is a supported image type.
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (is_valid, file_type_message)
        """
        try:
            allowed_extensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'pdf']
            max_size_mb = 20
            
            filename = getattr(file, 'name', '') or str(file)
            file_extension = filename.lower().split('.')[-1]
            
            if file_extension not in allowed_extensions:
                return False, f"Unsupported file type: {file_extension}. Allowed: {', '.join(allowed_extensions)}"
            
            # Check file size if available
            if hasattr(file, 'size'):
                size_mb = file.size / (1024 * 1024)
                if size_mb > max_size_mb:
                    return False, f"File too large: {size_mb:.1f}MB. Maximum: {max_size_mb}MB"
            
            return True, file_extension.upper()
            
        except Exception as e:
            return False, f"Error validating file: {str(e)}"

    def extract_structured_data(self, analysis_text: str) -> Dict[str, Any]:
        """
        Extract structured data from analysis text for easier processing.
        
        Args:
            analysis_text: Raw analysis text from GPT-4o
            
        Returns:
            Dict with categorized extracted information
        """
        # This is a simplified version - could be enhanced with more sophisticated parsing
        structured_data = {
            "geometry": {},
            "structural_elements": {},
            "materials": {},
            "components": {}
        }
        
        # Basic parsing - could be enhanced with regex or ML-based extraction
        lines = analysis_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect sections
            if any(keyword in line.lower() for keyword in ['geometry', 'dimension']):
                current_section = 'geometry'
            elif any(keyword in line.lower() for keyword in ['structural', 'rafter', 'beam']):
                current_section = 'structural_elements'
            elif any(keyword in line.lower() for keyword in ['material', 'lumber', 'wood']):
                current_section = 'materials'
            elif any(keyword in line.lower() for keyword in ['component', 'gutter', 'vent']):
                current_section = 'components'
            
            # Extract information if in a section
            if current_section and ':' in line:
                key, value = line.split(':', 1)
                structured_data[current_section][key.strip()] = value.strip()
        
        return structured_data

    # Removed _extract_text - now using response.choices[0].message.content directly
