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
You are a certified building code compliance expert specializing in Florida Building Code (FBC) Chapter 8 (Roof-Ceiling Construction) and Chapter 9 (Wind Resistance). 

TASK: Perform comprehensive compliance validation of the roof design specifications below.

DESIGN SPECIFICATIONS TO VALIDATE:
{agent1_output}

COMPLIANCE VALIDATION REQUIREMENTS:
Systematically check each element against current Florida Building Code requirements:

**1. SHEATHING COMPLIANCE (FBC Section 8.1-8.2):**
- Check sheathing type and thickness against Table 803.2
- Verify edge support requirements (Section 803.2.1)
- Validate fastening to framing (Table 803.2.1)
- Confirm span ratings and load capacities

**2. RAFTER SPACING AND SPANS (FBC Section 8.3):**
- Verify rafter spacing against Table 802.4
- Check span limits for lumber species and grade (Table 802.4.1)
- Validate size vs. span relationships
- Confirm load path continuity

**3. FASTENING REQUIREMENTS (FBC Section 8.4):**
- Check nail/screw specifications against Table 803.2.1
- Verify fastening schedules and patterns
- Confirm edge distance and spacing requirements
- Validate connection capacities

**4. WIND RESISTANCE (FBC Chapter 9):**
- Check wind load design requirements (Section 902)
- Verify uplift resistance provisions (Section 903)
- Confirm hurricane clip/strap requirements if applicable
- Validate high wind zone requirements (if applicable)

**5. GENERAL STRUCTURAL REQUIREMENTS:**
- Verify all materials meet code specifications
- Check dimensional requirements and tolerances
- Confirm proper installation methods
- Validate structural adequacy

REQUIRED OUTPUT FORMAT:
Use this exact plain text structure (no markdown formatting):

OVERALL STATUS: [COMPLIANT/NON-COMPLIANT/REQUIRES REVIEW]

ELEMENT ANALYSIS:
Sheathing: [STATUS] - [FBC Reference] - [Brief analysis]
Rafter Spacing/Spans: [STATUS] - [FBC Reference] - [Brief analysis]
Fastening: [STATUS] - [FBC Reference] - [Brief analysis]
Underlayment: [STATUS] - [FBC Reference] - [Brief analysis]
Insulation: [STATUS] - [FBC Reference] - [Brief analysis]
Wind Resistance: [STATUS] - [FBC Reference] - [Brief analysis]

CRITICAL FINDINGS:
Major Issues:
- [List critical compliance issues]

Required Corrections:
- [List necessary modifications]

Professional Recommendations:
- [Engineering recommendations]

SUMMARY:
[Overall assessment and next steps]

Use plain text only. No markdown symbols. Cite specific FBC sections.
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
You are a Florida Building Code expert. Focus specifically on validating the {element_type} requirements for this roof design.

ROOF DESIGN SPECIFICATIONS:
{agent1_output}

FOCUSED VALIDATION FOR: {element_type.upper()}

Provide a detailed analysis of only the {element_type} requirements:
1. Extract all {element_type}-related specifications from the design
2. Identify specific Florida Building Code requirements for {element_type}
3. Compare design vs. requirements
4. Determine compliance status
5. Provide specific code citations

FORMAT:
ELEMENT: {element_type.title()}
DESIGN SPECIFICATION: [what the design shows]
CODE REQUIREMENT: [specific Florida Building Code requirement]
COMPLIANCE: [COMPLIES/NON-COMPLIANT/REVIEW_REQUIRED]
CODE CITATION: [specific section/table reference]
ANALYSIS: [detailed explanation of the validation]
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