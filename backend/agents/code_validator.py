"""
Building Code Validator - Agent 2
Validates roof design specifications against Florida Building Code using GPT-4o
"""

from openai import OpenAI
from typing import Dict, Optional, Any
import re
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BuildingCodeValidator:
    """
    Agent 2: Building Code Validator
    Uses OpenAI GPT-5 for compliance analysis and GPT-5-mini for narrative summarization.
    """
    
    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com/v1",
        validation_model: str = "gpt-5.1",
        summary_model: str = "gpt-5-mini"
    ):
        """Initialize the building code validator with OpenAI credentials."""
        self.client = OpenAI(api_key=api_key, base_url=api_base)
        self.validation_cache = {}
        
        # Configuration
        self.validation_model = validation_model
        self.summary_model = summary_model
        self.max_completion_tokens = 4000
        self.temperature = 0.1  # Low temperature for consistent code validation
        
    def validate_roof_design(self, agent1_output: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Comprehensive validation of roof design against Florida Building Code.
        
        Args:
            agent1_output: Structured output from Agent 1 (roof design analysis)
            options: Optional validation parameters
            
        Returns:
            Dict containing detailed compliance validation report
        """
        start_time = time.time()
        
        try:
            logger.info("Starting building code validation with Mistral Small 3.1...")
            
            validation_prompt = f"""
You are a Florida Building Code expert specializing in residential roof construction compliance (FBC-R 2023).

TASK: Validate the roof design specifications below against Florida Residential Building Code 2023.

FOCUS: Primarily ROOF elements - sheathing, framing, connections, covering, wind resistance.

INPUT DATA (from structural analysis):
{agent1_output}

VALIDATION APPROACH:
For EACH SECTION extracted above, perform compliance checks on ALL roof elements.

OUTPUT STRUCTURE (use exactly this format):

================================================================================
OVERALL_COMPLIANCE_STATUS: [COMPLIANT / NON-COMPLIANT / REQUIRES FURTHER REVIEW / INSUFFICIENT DATA]
================================================================================

SECTION_BY_SECTION_VALIDATION:

---
SECTION: [section identifier from input]

ROOF_FRAMING_COMPLIANCE:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW / NOT APPLICABLE]
  Code_Reference: [specific FBC-R section, e.g., "FBC-R 2023 §R802.4, Table R802.4(1)"]
  Analysis: |
    [Detailed analysis of compliance]
    - Design specifies: [quote exact spec]
    - Code requires: [state requirement]
    - Determination: [explain why compliant/non-compliant]
  Required_Corrections: [specific fixes needed, or "None"]

ROOF_SHEATHING_COMPLIANCE:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW / NOT APPLICABLE]
  Code_Reference: [e.g., "FBC-R 2023 §R803.2.1, Table R803.2.1.1(1)"]
  Analysis: |
    - Sheathing specified: [quote spec]
    - Fastening specified: [quote pattern]
    - Code requirement: [state requirement]
    - Span rating: [if applicable]
    - Determination: [reasoning]
  Required_Corrections: [specific fixes, or "None"]

ROOF_TO_WALL_CONNECTION_COMPLIANCE:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW / NOT APPLICABLE]
  Code_Reference: [e.g., "FBC-R 2023 §R802.11, Table R802.11"]
  Analysis: |
    - Connection hardware: [quote spec]
    - Code requirement: [based on design wind speed, exposure]
    - Load path: [evaluation]
    - Determination: [reasoning]
  Required_Corrections: [specific fixes, or "None"]

ROOF_COVERING_COMPLIANCE:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW / NOT APPLICABLE]
  Code_Reference: [e.g., "FBC-R 2023 §R905.x (based on material type)"]
  Analysis: |
    - Roof covering: [quote spec]
    - Underlayment: [quote spec]
    - Installation requirements: [manufacturer, FBC notes]
    - Code requirement: [for this roof type and slope]
    - Wind resistance: [if HVHZ applicable]
    - Determination: [reasoning]
  Required_Corrections: [specific fixes, or "None"]

WIND_RESISTANCE_COMPLIANCE:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW / NOT APPLICABLE]
  Code_Reference: [e.g., "FBC-R 2023 §R301.2.1, ASCE 7"]
  Analysis: |
    - Design wind speed: [if noted, or "not specified"]
    - Exposure category: [if noted, or "not specified"]
    - Hurricane ties/straps: [quote spec]
    - Sheathing attachment: [evaluation for uplift]
    - Roof covering attachment: [wind rating if applicable]
    - Determination: [reasoning]
  Required_Corrections: [specific fixes, or "None"]

INSULATION_AND_VENTILATION:
  Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW / NOT APPLICABLE]
  Code_Reference: [e.g., "FBC-R 2023 §R806.5, §N1102"]
  Analysis: |
    - Insulation: [quote R-value and type]
    - Ventilation: [vented/non-vented attic]
    - Code requirement: [for climate zone]
    - Condensation control: [if applicable]
    - Determination: [reasoning]
  Required_Corrections: [specific fixes, or "None"]

SECTION_SUMMARY:
  Overall_Status: [COMPLIANT / NON-COMPLIANT / REQUIRES REVIEW]
  Critical_Issues: [list major violations, or "None"]
  Minor_Issues: [list items needing clarification, or "None"]

---
[Repeat for each section]

================================================================================
CRITICAL_FINDINGS_SUMMARY:
  Major_Violations: 
    - [list all NON-COMPLIANT items across all sections]
    - [if none: "No major code violations identified"]
  
  Items_Requiring_Review:
    - [list all REQUIRES REVIEW items]
    - [if none: "No items requiring further review"]
  
  Missing_Information:
    - [list critical specs not shown in drawings]
    - [if none: "All critical information provided"]

REQUIRED_CORRECTIONS:
  High_Priority:
    - [corrections needed for NON-COMPLIANT items]
    - [if none: "None required"]
  
  Recommended:
    - [suggested improvements for REQUIRES REVIEW items]
    - [best practices]
    - [if none: "None"]

PROFESSIONAL_RECOMMENDATION:
  [1-2 paragraph summary of overall compliance status, key issues, and recommended next steps for permit submission]

VALIDATION_METADATA:
  Code_Edition: Florida Building Code - Residential 2023
  Primary_Chapters: Chapter 8 (Roof-Ceiling Construction), Chapter 9 (Roof Assemblies)
  Sections_Analyzed: [count]
  Confidence_Level: [HIGH / MEDIUM / LOW - based on completeness of input data]

STRICT VALIDATION RULES:
1. Only validate what is explicitly shown - never assume missing details
2. Quote exact specifications from the input when analyzing
3. Cite specific FBC-R section numbers (not generic references)
4. Mark "REQUIRES REVIEW" when information is partial/ambiguous
5. Mark "NOT APPLICABLE" when a code section doesn't apply to this design
6. For wind resistance, note if design wind speed is not specified
7. Consider Florida's specific requirements (HVHZ zones, high wind, etc.)
8. Prioritize life safety issues (connections, uplift, structural adequacy)
"""
            
            response = self.client.responses.create(
                model=self.validation_model,
                max_completion_tokens=self.max_output_tokens,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": validation_prompt}
                        ]
                    }
                ]
            )
            
            # Extract response content directly
            validation_result = response.choices[0].message.content
            if not validation_result or not validation_result.strip():
                raise RuntimeError(f"Validation model returned empty output")
            
            processing_time = time.time() - start_time
            total_tokens = response.usage.total_tokens if response.usage else 0
            
            # Log performance metrics
            logger.info(f"Agent2 Validation Complete:")
            logger.info(f"Tokens Used: {total_tokens}")
            logger.info(f"Processing Time: {processing_time:.2f}s")
            
            # Parse the structured response
            parsed_report = self._parse_validation_report(validation_result)
            
            return {
                'validation_report': validation_result,
                'parsed_report': parsed_report,
                'processing_time': processing_time,
                'success': True
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }

    def validate_specific_element(self, agent1_output: str, element_type: str) -> Dict[str, Any]:
        """
        Validate a specific design element against building codes.
        
        Args:
            agent1_output: Design analysis from Agent 1
            element_type: Specific element to validate (e.g., 'sheathing', 'spacing', 'materials')
            
        Returns:
            Dict containing focused validation results
        """
        try:
            specific_prompt = f"""
You are a Florida Building Code - Residential (FBC-R) 2023 expert. Validate ONLY the {element_type} for the roof design below. Do not validate other elements.

ROOF DESIGN SPECIFICATIONS (verbatim source):
{agent1_output}

SCOPE & RULES
- Use only the text above. Do not assume typical values.
- Status meanings:
  COMPLIANT = meets cited FBC-R requirement(s)
  NON-COMPLIANT = violates cited requirement(s)
  REQUIRES FURTHER REVIEW = present but info is insufficient/ambiguous/contradictory OR exact section/table cannot be confirmed
  MISSING = element not mentioned at all
  N/A = not applicable per FBC-R (must cite why)
- Quote the design’s key values for this element before judging (e.g., “7/16 in OSB, 8d ring shank @ 6 in edge/field”).
- Cite precise sections/tables (e.g., “FBC-R 2023 R803.2.1; Table R802.4.1(1)”). Do not fabricate. If exact citation cannot be confirmed, set REQUIRES FURTHER REVIEW and say “Exact citation verification needed.”

TARGET SECTIONS BY ELEMENT (use the most relevant subset; do not list all):
- sheathing → R803.* and related fastening tables
- rafter spacing/spans → R802.* span tables (species/grade/size/spacing)
- fastening/connections → R803.*, R802.*, manufacturer/listed connectors as applicable
- underlayment → R905.x (and HVHZ provisions where applicable)
- insulation → applicable roof/ceiling/condensation/ventilation provisions
- wind resistance → R301.2.1 design wind (Vult, exposure), uplift/load path, roof covering wind attachment (incl. R905.x)

DATA NEEDED TO VALIDATE (mark each as “provided” or “missing” for this element):
- sheathing: type, thickness, span rating/edge support if shown, fastening size/pattern
- rafter spacing/spans: member size, species/grade, spacing, span
- fastening/connections: fastener type/size/spacing, connector types/locations
- underlayment: type/layers/laps/fastening, HVHZ or product-approval dependencies
- insulation: type, R-value, location, condensation/ventilation notes
- wind resistance: Vult, exposure category, risk category/site, roof zones, covering attachment class

OUTPUT (plain text only; exact structure):
ELEMENT: {element_type}
STATUS: [COMPLIANT/NON-COMPLIANT/REQUIRES FURTHER REVIEW/MISSING/N/A]

DESIGN EVIDENCE:
- [verbatim facts for this element only]

REQUIRED DATA TO VALIDATE:
- [item]: [provided/missing]
- [item]: [provided/missing]

CODE CHECKS:
- [Check #1] - [PASS/FAIL/REVIEW] - [FBC Reference] - [short analysis]
- [Check #2] - [PASS/FAIL/REVIEW] - [FBC Reference] - [short analysis]
- [Add checks as needed for this element only]

FINAL DETERMINATION:
- [one sentence explaining why the STATUS was set, referencing the most decisive check]

CORRECTIONS (if NON-COMPLIANT or REQUIRES FURTHER REVIEW):
- [precise fix or info needed with section/table reference]

            """
            
            response = self.client.chat.completions.create(
                model=self.validation_model,
                max_completion_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": specific_prompt}]
                    }
                ]
            )
            
            element_text = response.choices[0].message.content
            if not element_text or not element_text.strip():
                raise RuntimeError(f"Element validation returned empty output")
            
            total_tokens = response.usage.total_tokens if response.usage else 0
            
            return {
                'element_validation': element_text,
                'element_type': element_type,
                'success': True
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }

    def generate_compliance_report(self, validation_results: Dict) -> Dict[str, Any]:
        """
        Generate a compliance report.
        
        Args:
            validation_results: Results from validation process
            
        Returns:
            Dict containing formatted compliance report
        """
        try:
            report_prompt = f"""
Based on the building code validation results, generate a professional compliance report suitable for permit submission.

VALIDATION RESULTS:
{validation_results.get('validation_report', '')}

Generate a formal BUILDING CODE COMPLIANCE REPORT with:

1. PROJECT SUMMARY
   - Design type and scope
   - Code edition and jurisdiction
   - Date of review

2. EXECUTIVE SUMMARY
   - Overall compliance status
   - Summary of findings
   - Critical issues (if any)

3. DETAILED FINDINGS
   - Organized by building system
   - Code citations for each item
   - Compliance status for each element

4. RECOMMENDATIONS
   - Required corrections (if any)
   - Suggested improvements
   - Next steps for permit approval

5. PROFESSIONAL CERTIFICATION
   - Statement of review completeness
   - Limitations and assumptions
   - Reviewer qualifications

Format as a professional document suitable for official submission.
            """
            
            response = self.client.chat.completions.create(
                model=self.summary_model,
                max_completion_tokens=3000,
                messages=[
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": report_prompt}]
                    }
                ]
            )
            
            report_text = response.choices[0].message.content
            if not report_text or not report_text.strip():
                raise RuntimeError(f"Summary model returned empty output")
            
            total_tokens = response.usage.total_tokens if response.usage else 0
            
            return {
                'compliance_report': report_text,
                'success': True
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }

    def _parse_validation_report(self, validation_text: str) -> Dict[str, Any]:
        """
        Parse the structured validation report into components.
        
        Args:
            validation_text: Raw validation report from GPT-4o
            
        Returns:
            Dict with parsed report components
        """
        try:
            parsed = {
                'overall_status': 'UNKNOWN',
                'validations': [],
                'critical_violations': [],
                'recommendations': [],
                'confidence': {'level': 'Unknown', 'percentage': 0}
            }
            
            # Extract overall status
            status_match = re.search(r'OVERALL STATUS:\s*([A-Z_]+)', validation_text)
            if status_match:
                parsed['overall_status'] = status_match.group(1)
            
            # Extract individual validations (simplified parsing)
            validation_sections = re.findall(r'\d+\.\s*(.+?)(?=\d+\.|CRITICAL VIOLATIONS|RECOMMENDATIONS|$)', 
                                           validation_text, re.DOTALL)
            
            for section in validation_sections:
                # Basic parsing of validation items
                if '✅' in section or 'COMPLIES' in section:
                    status = 'COMPLIANT'
                elif '❌' in section or 'NON-COMPLIANT' in section:
                    status = 'NON_COMPLIANT'
                elif '⚠️' in section or 'REVIEW_REQUIRED' in section:
                    status = 'REVIEW_REQUIRED'
                else:
                    status = 'UNKNOWN'
                
                parsed['validations'].append({
                    'text': section.strip(),
                    'status': status
                })
            
            # Extract confidence level
            confidence_match = re.search(r'Overall Confidence:\s*(\w+).*?(\d+)%', validation_text)
            if confidence_match:
                parsed['confidence'] = {
                    'level': confidence_match.group(1),
                    'percentage': int(confidence_match.group(2))
                }
            
            return parsed
            
        except Exception as e:
            # Return basic structure on parsing error
            return {
                'overall_status': 'UNKNOWN',
                'validations': [],
                'critical_violations': [],
                'recommendations': [],
                'confidence': {'level': 'Unknown', 'percentage': 0},
                'parse_error': str(e)
            }

    def get_validation_summary(self, parsed_report: Dict) -> Dict[str, Any]:
        """
        Generate summary statistics from parsed validation report.
        
        Args:
            parsed_report: Parsed validation report
            
        Returns:
            Dict with summary statistics
        """
        validations = parsed_report.get('validations', [])
        total = len(validations)
        
        if total == 0:
            return {
                'total_checks': 0,
                'compliant': 0,
                'non_compliant': 0,
                'review_required': 0,
                'compliance_percentage': 0
            }
        
        compliant = sum(1 for v in validations if v['status'] == 'COMPLIANT')
        non_compliant = sum(1 for v in validations if v['status'] == 'NON_COMPLIANT')
        review_required = sum(1 for v in validations if v['status'] == 'REVIEW_REQUIRED')
        
        compliance_percentage = (compliant / total) * 100 if total > 0 else 0
        
        return {
            'total_checks': total,
            'compliant': compliant,
            'non_compliant': non_compliant,
            'review_required': review_required,
            'compliance_percentage': compliance_percentage
        }

    # Removed _extract_text - now using response.choices[0].message.content directly