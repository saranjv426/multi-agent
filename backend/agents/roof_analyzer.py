"""
Roof Design Analyzer - Agent 1
Extracts structural information from roof design drawings using GPT-4o Vision API
"""

import base64
import io
import logging
import time
from PIL import Image
from openai import OpenAI
from typing import Dict, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RoofDesignAnalyzer:
    """
    Agent 1: Roof Design Analyzer
    Uses Mistral Small 3.1 Vision API to extract detailed structural information from design drawings
    Enhanced with specialized prompts for maximum accuracy on technical drawings
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.ai.it.ufl.edu"):
        """Initialize the roof design analyzer with Navigator AI API key."""
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.analysis_cache = {}
        
        # Configuration
        self.vision_model = "mistral-small-3.1"
        self.max_tokens = 6000  # Increased for detailed technical analysis
        self.temperature = 0.1  # Low temperature for consistent technical analysis
        self.max_image_size = (1024, 1024)
        
    def encode_image(self, image_file) -> Optional[str]:
        """Convert image file to base64 string for Navigator AI Vision API."""
        try:
            if hasattr(image_file, 'read'):
                # File-like object
                image_bytes = image_file.read()
                if hasattr(image_file, 'seek'):
                    image_file.seek(0)  # Reset file pointer
            else:
                # Already bytes
                image_bytes = image_file
                
            # Convert to PIL Image to ensure compatibility
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (OpenAI has size limits)
            if image.size[0] > self.max_image_size[0] or image.size[1] > self.max_image_size[1]:
                image.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
            
            # Convert back to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            image_bytes = buffer.getvalue()
            
            return base64.b64encode(image_bytes).decode('utf-8')
            
        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")

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
            
            # Optimized prompt for Mistral Small 3.1 - Enhanced accuracy and structure
            analysis_prompt = """
You are an expert structural engineer analyzing a roof design drawing. Your task is to extract ALL visible technical specifications with precision and detail.

ANALYSIS INSTRUCTIONS:
Study this architectural drawing carefully and identify every technical detail. Pay special attention to:

**DIMENSIONAL MEASUREMENTS:**
- Rafter spacing (look for "16" O.C.", "24" O.C.", "19.2" O.C.")
- Span lengths (measure between supports)
- Member sizes (2x4, 2x6, 2x8, 2x10, 2x12, etc.)
- Thickness measurements (7/16", 5/8", 15/32", etc.)
- Lumber beam dimensions (16" L.V.L. wood beam, etc.)

**MATERIAL SPECIFICATIONS:**
- Sheathing type and thickness (OSB, plywood, specific thickness)
- Lumber grades and species (SYP, etc.)
- Fastener specifications (8d ring shank nails, spacing patterns)
- Insulation details (R-38 spray foam, type, R-value, thickness)
- Underlayment specifications (self-adhering synthetic, etc.)
- Roofing materials (Galvalum metal roof, etc.)
- Hardware specifications (Simpson straps, metal drip edge, etc.)

**SLOPE/PITCH ANALYSIS:**
- Roof pitch ratios (look for slope indicators and report in standard rise:run format)
- Standard format is rise:run (3:12, 4:12, 6:12, 8:12) where first number is vertical rise
- Triangular pitch diagrams (often shown with slope indicators)
- Angle measurements in degrees
- Ridge and eave details
- CRITICAL: Use standard rise:run format (vertical:horizontal)

**STRUCTURAL CONNECTIONS:**
- Fastening patterns and schedules
- Hardware specifications (straps, hangers, clips)
- Connection details at critical points
- Load path elements

**TEXT ANNOTATIONS:**
- Read ALL text labels, dimensions, and specifications
- Note code references (FBC, IRC, etc.)
- Material callouts and notes

REQUIRED OUTPUT FORMAT:
Use this exact plain text structure (no markdown formatting):

DIMENSIONS FOUND:
- Rafter spacing: [spacing measurements]
- Spans: [span measurements or "not specified"]
- Lumber sizes: [sizes found]

MATERIALS IDENTIFIED:
- Sheathing: [type and thickness]
- Lumber grade: [grade if visible]
- Fasteners: [nail/screw specifications]
- Insulation: [R-value, type, thickness]
- Underlayment: [type and specifications]
- Roofing: [material type and specifications]

SLOPE/PITCH DETAILS:
- Pitch: [ratio in standard rise:run format (e.g., 3:12, 4:12) - vertical:horizontal]

STRUCTURAL ELEMENTS:
- Rafters: [rafter details]
- Connections: [connection hardware]
- Hardware: [straps, clips, other details]

TEXT ANNOTATIONS:
[List all visible text, labels, dimensions, notes]

CRITICAL OBSERVATIONS:
[Note important design features or concerns]

Use plain text only. No markdown symbols. Be precise and thorough.
            """
            
            # Prepare the API request
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": analysis_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            # Call Navigator AI Vision API
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            analysis_result = response.choices[0].message.content
            
            # Calculate processing time and cost
            processing_time = time.time() - start_time
            total_tokens = response.usage.total_tokens
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            
            # Navigator AI Mistral Small 3.1 - Free through university credit
            # Estimated equivalent value for tracking purposes
            estimated_cost = 0.0  # Free through Navigator AI
            
            # Log cost and performance metrics
            logger.info(f"Agent1 Analysis Complete:")
            logger.info(f"Tokens - Total: {total_tokens}, Input: {prompt_tokens}, Output: {completion_tokens}")
            logger.info(f"Estimated Cost: ${estimated_cost:.4f}")
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
                'tokens_used': total_tokens,
                'estimated_cost': estimated_cost,
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
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": follow_up_prompt
                    }
                ],
                max_tokens=1000,
                temperature=self.temperature
            )
            
            return {
                'answer': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
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