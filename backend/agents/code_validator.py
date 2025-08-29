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
    Uses Mistral Small 3.1 to validate design specifications against Florida Building Code
    Enhanced with comprehensive prompts for thorough compliance checking
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.ai.it.ufl.edu"):
        """Initialize the building code validator with Navigator AI API key."""
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.validation_cache = {}
        
        # Configuration
        self.text_model = "mistral-small-3.1"
        self.max_tokens = 6000  # Increased for comprehensive compliance analysis
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
ROLE:
You are a certified building code compliance expert for Florida Building Code – Residential (FBC-R) 2023, focused on Chapter 8 (Roof-Ceiling Construction) and Chapter 9 (Roof Assemblies/Wind). Task: validate the roof design below for code compliance.

INPUT (design to validate):
{agent1_output}

STRICT BEHAVIOR:
- Work only from the provided specs; do not assume typical values.
- STATUS rules per element:
  COMPLIANT = meets cited FBC-R requirement(s).
  NON-COMPLIANT = violates cited requirement(s).
  REQUIRES REVIEW = element present but info is insufficient/ambiguous/contradictory OR exact code/table cannot be confirmed.
  MISSING = element not mentioned at all.
  N/A = not applicable per FBC-R (must cite why).
- Always cite precise FBC-R section/table (e.g., “FBC-R 2023 R803.2.1; Table R802.4.1(1)”). Do not fabricate citations.
- Brief analysis must quote key values from the input (e.g., “7/16 in OSB @ 24 in o.c., nails 8d @ 6/12 in.”) before judging status.

CRITICALITY MAP (governs OVERALL STATUS):
CRITICAL: Wind Resistance; Sheathing; Rafter Spacing/Spans; Fastening/Connections.
SIGNIFICANT: Underlayment (PROMOTE to CRITICAL if HVHZ or product approval/listing requires specific underlayment).
MINOR: Insulation (PROMOTE to SIGNIFICANT if condensation/ventilation control affects compliance).

OVERALL STATUS ALGORITHM (apply in order):
1) If any CRITICAL is NON-COMPLIANT → OVERALL = NON-COMPLIANT.
2) Else if any CRITICAL is MISSING → OVERALL = MISSING.
3) Else if any CRITICAL is REQUIRES REVIEW → OVERALL = REQUIRES REVIEW.
4) Else if any SIGNIFICANT is NON-COMPLIANT:
     - If ≥2 SIGNIFICANT non-compliances → OVERALL = NON-COMPLIANT
     - Else → OVERALL = REQUIRES REVIEW
5) Else if any SIGNIFICANT is MISSING → OVERALL = MISSING.
6) Else if any SIGNIFICANT is REQUIRES REVIEW → OVERALL = REQUIRES REVIEW.
7) Else if any MINOR is NON-COMPLIANT → OVERALL = REQUIRES REVIEW.
8) Else if only MINOR are MISSING/REQUIRES REVIEW and all others are COMPLIANT/N/A → OVERALL = COMPLIANT.

MISSING vs REQUIRES REVIEW DECISION:
- If an element is not mentioned at all → MISSING.
- If mentioned but key data is absent/unclear/contradictory (e.g., species/grade not given for span check; wind speed not stated; citation uncertain) → REQUIRES REVIEW with reason (“missing rafter grade”, “wind parameters not provided”, “exact table confirmation needed”).
- If wind parameters/site (Vult, exposure, HVHZ) are not present, mark Wind Resistance as MISSING.

VALIDATION CHECKLIST (cite exact sections/tables):
- Sheathing (R803.*; Tables R803.* / fastening tables)
- Rafter Spacing/Spans (R802.* span tables)
- Fastening/Connections (R8xx tables/sections referenced by sheathing/rafters/connectors)
- Underlayment (R905.x and related; HVHZ where applicable)
- Insulation (applicable roof/ceiling provisions; cite section used)
- Wind Resistance (R301.2.1 and applicable uplift/roof covering sections incl. R905.x, connectors/load path as applicable)

OUTPUT FORMAT (plain text only; exact structure):
OVERALL STATUS: [COMPLIANT/NON-COMPLIANT/REQUIRES REVIEW/MISSING]

ELEMENT ANALYSIS:
Sheathing: [STATUS] - [FBC Reference] - [Brief analysis]
Rafter Spacing/Spans: [STATUS] - [FBC Reference] - [Brief analysis]
Fastening: [STATUS] - [FBC Reference] - [Brief analysis]
Underlayment: [STATUS] - [FBC Reference] - [Brief analysis]
Insulation: [STATUS] - [FBC Reference] - [Brief analysis]
Wind Resistance: [STATUS] - [FBC Reference] - [Brief analysis]

CRITICAL FINDINGS:
Major Issues:
- [List issues with exact citations]

Required Corrections:
- [Precise fixes with table/section references]

Professional Recommendations:
- [Targeted engineering recs; e.g., connector upgrades, alternate fastening schedule, rafter size/species change, HVHZ-compliant underlayment]

SUMMARY:
[Overall assessment; list items marked MISSING; list reasons for any REQUIRES REVIEW; state if HVHZ/product-approval dependency elevated underlayment.]

            """
            
            # Call Navigator AI API
            response = self.client.chat.completions.create(
                model=self.text_model,
                messages=[
                    {
                        "role": "user",
                        "content": validation_prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            validation_result = response.choices[0].message.content
            
            # Calculate processing time and cost
            processing_time = time.time() - start_time
            total_tokens = response.usage.total_tokens
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            
            # Navigator AI Mistral Small 3.1 - Free through university credit
            # Estimated equivalent value for tracking purposes
            estimated_cost = 0.0  # Free through Navigator AI
            
            # Log cost and performance metrics
            logger.info(f"Agent2 Validation Complete:")
            logger.info(f"Tokens - Total: {total_tokens}, Input: {prompt_tokens}, Output: {completion_tokens}")
            logger.info(f"Estimated Cost: ${estimated_cost:.4f}")
            logger.info(f"Processing Time: {processing_time:.2f}s")
            
            # Parse the structured response
            parsed_report = self._parse_validation_report(validation_result)
            
            return {
                'validation_report': validation_result,
                'parsed_report': parsed_report,
                'tokens_used': total_tokens,
                'estimated_cost': estimated_cost,
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
  REQUIRES REVIEW = present but info is insufficient/ambiguous/contradictory OR exact section/table cannot be confirmed
  MISSING = element not mentioned at all
  N/A = not applicable per FBC-R (must cite why)
- Quote the design’s key values for this element before judging (e.g., “7/16 in OSB, 8d ring shank @ 6 in edge/field”).
- Cite precise sections/tables (e.g., “FBC-R 2023 R803.2.1; Table R802.4.1(1)”). Do not fabricate. If exact citation cannot be confirmed, set REQUIRES REVIEW and say “Exact citation verification needed.”

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
STATUS: [COMPLIANT/NON-COMPLIANT/REQUIRES REVIEW/MISSING/N/A]

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

CORRECTIONS (if NON-COMPLIANT or REQUIRES REVIEW):
- [precise fix or info needed with section/table reference]

            """
            
            response = self.client.chat.completions.create(
                model=self.text_model,
                messages=[
                    {
                        "role": "user",
                        "content": specific_prompt
                    }
                ],
                max_tokens=2000,
                temperature=self.temperature
            )
            
            return {
                'element_validation': response.choices[0].message.content,
                'element_type': element_type,
                'tokens_used': response.usage.total_tokens,
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
                model=self.text_model,
                messages=[
                    {
                        "role": "user",
                        "content": report_prompt
                    }
                ],
                max_tokens=3000,
                temperature=0.1
            )
            
            return {
                'compliance_report': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
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