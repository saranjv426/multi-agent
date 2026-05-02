"""
Design Parser - Extract structured specifications from Agent1 output
Pure parsing logic for converting text analysis to structured data
"""

import re
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

@dataclass
class DesignSpecification:
    """Structured representation of a design element"""
    element_type: str  # "sheathing", "rafter", "span", etc.
    value: Union[float, str]
    unit: str
    material: Optional[str] = None
    spacing: Optional[float] = None
    additional_info: Optional[Dict] = None

class DesignParser:
    """
    Parse Agent1 roof design extraction into structured specifications.
    Focuses on extracting measurable values that need code validation.
    """
    
    def __init__(self):
        # Measurement conversion factors (to standardize units)
        self.unit_conversions = {
            'feet': 12.0,  # feet to inches
            'ft': 12.0,
            'foot': 12.0,
            'inch': 1.0,
            'in': 1.0,
            '"': 1.0,
            'inches': 1.0
        }
    
    def parse_agent1_output(self, agent1_text: str) -> List[DesignSpecification]:
        """
        Parse Agent1 roof analysis output into structured specifications.
        
        Args:
            agent1_text: Raw text output from Agent1 roof analysis
            
        Returns:
            List of DesignSpecification objects
        """
        specifications = []
        
        # Parse different types of specifications
        specifications.extend(self._parse_sheathing_specifications(agent1_text))
        specifications.extend(self._parse_rafter_specifications(agent1_text))
        specifications.extend(self._parse_span_specifications(agent1_text))
        specifications.extend(self._parse_spacing_specifications(agent1_text))
        specifications.extend(self._parse_material_specifications(agent1_text))
        specifications.extend(self._parse_fastening_specifications(agent1_text))
        specifications.extend(self._parse_slope_specifications(agent1_text))
        
        return specifications
    
    def _parse_sheathing_specifications(self, text: str) -> List[DesignSpecification]:
        """Parse roof sheathing thickness specifications."""
        specs = []
        
        # Patterns for sheathing thickness
        thickness_patterns = [
            r'(?:sheathing|decking).*?(\d+/\d+)\s*(?:inch|in\.?|")',
            r'(\d+/\d+)\s*(?:inch|in\.?|")\s*(?:plywood|OSB|sheathing)',
            r'(?:plywood|OSB).*?(\d+/\d+)\s*(?:inch|in\.?|")',
            r'(\d+/\d+)"\s*(?:plywood|OSB|sheathing)'
        ]
        
        for pattern in thickness_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                thickness_str = match.group(1)
                thickness_value = self._convert_fraction_to_decimal(thickness_str)
                
                if thickness_value:
                    # Extract material context
                    context = text[max(0, match.start()-50):match.end()+50]
                    material = self._extract_material_from_context(context, ['plywood', 'OSB', 'lumber'])
                    
                    specs.append(DesignSpecification(
                        element_type="sheathing_thickness",
                        value=thickness_value,
                        unit="inch",
                        material=material,
                        additional_info={"original_text": match.group(0)}
                    ))
        
        return specs
    
    def _parse_rafter_specifications(self, text: str) -> List[DesignSpecification]:
        """Parse rafter size and specifications."""
        specs = []
        
        # Patterns for rafter sizes
        rafter_patterns = [
            r'(?:rafter|joist)s?.*?(\d+x\d+)',
            r'(\d+x\d+)\s*(?:rafter|joist|lumber)',
            r'(\d+x\d+)\s*(?:S\.?Y\.?P\.?|southern yellow pine|SYP)'
        ]
        
        for pattern in rafter_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                size = match.group(1)
                
                # Extract material and spacing context
                context = text[max(0, match.start()-100):match.end()+100]
                material = self._extract_material_from_context(context, ['SYP', 'southern yellow pine', 'lumber'])
                spacing = self._extract_spacing_from_context(context)
                
                specs.append(DesignSpecification(
                    element_type="rafter_size",
                    value=size,
                    unit="nominal",
                    material=material,
                    spacing=spacing,
                    additional_info={"original_text": match.group(0)}
                ))
        
        return specs
    
    def _parse_span_specifications(self, text: str) -> List[DesignSpecification]:
        """Parse span measurements."""
        specs = []
        
        # Patterns for spans
        span_patterns = [
            r'(?:span|clear span).*?(\d+)\s*(?:feet|ft\.?)',
            r'(\d+)\s*(?:feet|ft\.?)\s*(?:span|clear)',
            r'(?:beam|rafter)\s*span.*?(\d+)\s*(?:feet|ft\.?)'
        ]
        
        for pattern in span_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                span_value = float(match.group(1))
                
                specs.append(DesignSpecification(
                    element_type="span",
                    value=span_value,
                    unit="feet",
                    additional_info={"original_text": match.group(0)}
                ))
        
        return specs
    
    def _parse_spacing_specifications(self, text: str) -> List[DesignSpecification]:
        """Parse spacing measurements (on center, etc.)."""
        specs = []
        
        # Patterns for spacing
        spacing_patterns = [
            r'(\d+)\s*(?:inch|in\.?|")\s*(?:o\.?c\.?|on center|OC)',
            r'(\d+)"\s*(?:o\.?c\.?|on center|OC)',
            r'at\s*(\d+)\s*(?:inch|in\.?|")\s*(?:centers?|spacing)'
        ]
        
        for pattern in spacing_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                spacing_value = float(match.group(1))
                
                # Determine what's being spaced from context
                context = text[max(0, match.start()-50):match.end()+50]
                element_type = "spacing"
                if any(word in context.lower() for word in ['rafter', 'joist']):
                    element_type = "rafter_spacing"
                elif any(word in context.lower() for word in ['fastener', 'nail', 'screw']):
                    element_type = "fastening_spacing"
                
                specs.append(DesignSpecification(
                    element_type=element_type,
                    value=spacing_value,
                    unit="inch",
                    additional_info={"original_text": match.group(0)}
                ))
        
        return specs
    
    def _parse_material_specifications(self, text: str) -> List[DesignSpecification]:
        """Parse material specifications."""
        specs = []
        
        # Common materials to look for
        materials = {
            'plywood': r'\bplywood\b',
            'OSB': r'\bOSB\b',
            'metal': r'\bmetal\s*(?:roof|panel)',
            'galvanized': r'\bgalvanized\b',
            'SYP': r'\b(?:S\.?Y\.?P\.?|southern yellow pine)\b'
        }
        
        for material_name, pattern in materials.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                specs.append(DesignSpecification(
                    element_type="material",
                    value=material_name,
                    unit="type",
                    additional_info={"original_text": match.group(0)}
                ))
        
        return specs
    
    def _parse_fastening_specifications(self, text: str) -> List[DesignSpecification]:
        """Parse fastening specifications."""
        specs = []
        
        # Patterns for fasteners
        fastener_patterns = [
            r'(\d+d)\s*(?:nail|screw)',
            r'(\d+)\s*(?:inch|in\.?|")\s*(?:nail|screw)',
            r'(?:nail|screw).*?(\d+)\s*(?:inch|in\.?|")\s*(?:o\.?c\.?|spacing)'
        ]
        
        for pattern in fastener_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                fastener_value = match.group(1)
                
                specs.append(DesignSpecification(
                    element_type="fastening",
                    value=fastener_value,
                    unit="size" if 'd' in fastener_value else "inch",
                    additional_info={"original_text": match.group(0)}
                ))
        
        return specs
    
    def _parse_slope_specifications(self, text: str) -> List[DesignSpecification]:
        """Parse roof slope/pitch specifications."""
        specs = []
        
        # Patterns for slope
        slope_patterns = [
            r'(?:Roof_Pitch|Pitch|Slope)\s*:\s*"?(\d+)\s*[:/]\s*(\d+)"?',
            r'(\d+):(\d+)\s*(?:slope|pitch)',
            r'(\d+)/(\d+)\s*(?:slope|pitch)',
            r'(\d+\.?\d*)\s*degrees?',
            r'(\d+)\s*in\s*(\d+)\s*(?:slope|pitch)'
        ]
        
        for pattern in slope_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if 'degree' in match.group(0).lower():
                    slope_value = float(match.group(1))
                    unit = "degrees"
                else:
                    # Rise over run
                    rise = float(match.group(1))
                    run = float(match.group(2))
                    slope_value = f"{rise}:{run}"
                    unit = "ratio"
                
                specs.append(DesignSpecification(
                    element_type="slope",
                    value=slope_value,
                    unit=unit,
                    additional_info={"original_text": match.group(0)}
                ))
        
        return specs
    
    def _convert_fraction_to_decimal(self, fraction_str: str) -> Optional[float]:
        """Convert fraction string (like '5/8') to decimal."""
        try:
            if '/' in fraction_str:
                numerator, denominator = fraction_str.split('/')
                return float(numerator) / float(denominator)
            else:
                return float(fraction_str)
        except (ValueError, ZeroDivisionError):
            return None
    
    def _extract_material_from_context(self, context: str, materials: List[str]) -> Optional[str]:
        """Extract material type from surrounding context."""
        for material in materials:
            if material.lower() in context.lower():
                return material
        return None
    
    def _extract_spacing_from_context(self, context: str) -> Optional[float]:
        """Extract spacing measurement from context."""
        spacing_match = re.search(r'(\d+)\s*(?:inch|in\.?|")\s*(?:o\.?c\.?|on center)', 
                                context, re.IGNORECASE)
        if spacing_match:
            return float(spacing_match.group(1))
        return None
    
    def get_specifications_by_type(self, specifications: List[DesignSpecification]) -> Dict[str, List[DesignSpecification]]:
        """Group specifications by element type."""
        grouped = {}
        for spec in specifications:
            if spec.element_type not in grouped:
                grouped[spec.element_type] = []
            grouped[spec.element_type].append(spec)
        return grouped
    
    def get_design_summary(self, specifications: List[DesignSpecification]) -> Dict:
        """Generate a summary of the parsed design specifications."""
        grouped = self.get_specifications_by_type(specifications)
        
        return {
            'total_specifications': len(specifications),
            'specifications_by_type': {k: [{'value': s.value, 'unit': s.unit, 'material': s.material} 
                                          for s in v] for k, v in grouped.items()},
            'element_types': list(grouped.keys())
        }
