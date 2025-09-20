"""
PDF Report Generator
Creates professional compliance reports from validation results
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import io
import re
import base64
from typing import Dict, Any, Optional

class ComplianceReportGenerator:
    """
    Generate professional PDF compliance reports for roof design validation
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase separated by spaces"""
        # Remove asterisks and colons
        clean_text = text.replace('*', '').strip()
        
        # Split by spaces and capitalize each word
        words = clean_text.split()
        pascal_words = []
        
        for word in words:
            # Handle special cases
            if word.upper() in ['OSB', 'GYP', 'BD', 'FBC', 'HVHZ', 'O.C.', 'L.V.L.', 'MTL']:
                pascal_words.append(word.upper())
            elif word.lower() in ['and', 'or', 'at', 'with', 'per', 'as', 'of', 'in', 'on', 'to', 'for']:
                pascal_words.append(word.lower())
            else:
                pascal_words.append(word.capitalize())
        
        return ' '.join(pascal_words)
    
    def _setup_custom_styles(self):
        """Set up custom styles for the report with Arial font"""
        
        # Title style (16pt Arial Bold)
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.Color(0.1, 0.3, 0.6),  # Primary blue
            fontName='Helvetica-Bold'  # Using Helvetica as Arial equivalent
        ))
        
        # Section header style (13pt Bold - numbered sections in blue)
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=13,
            fontName='Helvetica-Bold',
            textColor=colors.Color(0.133, 0.4, 0.8),      # blue-600
            spaceBefore=16,
            spaceAfter=8,
            alignment=TA_LEFT,
            leading=19.5  # 1.5 line spacing
        ))
        
        # Subsection header style (12pt Bold) - with bullet (•)
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=colors.Color(0.2, 0.2, 0.2),        # dark gray
            spaceBefore=8,
            spaceAfter=4,
            alignment=TA_LEFT,
            leftIndent=24,  # Indent for sub headings
            leading=18      # 1.5 line spacing
        ))
        
        # Content style (11pt) - for content under subheadings with circle bullets (○)
        self.styles.add(ParagraphStyle(
            name='ContentBullet',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            textColor=colors.Color(0.3, 0.3, 0.3),        # gray-600
            spaceBefore=2,
            spaceAfter=2,
            leading=16.5,  # 1.5 line spacing (11pt * 1.5)
            alignment=TA_LEFT,
            leftIndent=48,  # More indent for content
            keepWithNext=1  # Prevent orphan lines
        ))
        
        # Regular content (11pt Arial) with 1.5 line spacing
        self.styles.add(ParagraphStyle(
            name='Content',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            textColor=colors.Color(0.3, 0.3, 0.3),        # gray-600
            spaceBefore=2,
            spaceAfter=2,
            leading=16.5,  # 1.5 line spacing (11pt * 1.5)
            alignment=TA_LEFT,
            keepWithNext=1  # Prevent orphan lines
        ))
        
        # Compliance status styles with 1.5 line spacing
        self.styles.add(ParagraphStyle(
            name='Compliant',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.Color(0.133, 0.545, 0.133),  # green-800
            fontName='Helvetica-Bold',
            leading=16.5,  # 1.5 line spacing (11pt * 1.5)
            keepWithNext=1  # Prevent orphan lines
        ))
        
        self.styles.add(ParagraphStyle(
            name='NonCompliant',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.Color(0.6, 0.133, 0.133),    # red-800
            fontName='Helvetica-Bold',
            leading=16.5,  # 1.5 line spacing (11pt * 1.5)
            keepWithNext=1  # Prevent orphan lines
        ))
        
        self.styles.add(ParagraphStyle(
            name='Review',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.Color(0.6, 0.4, 0.133),      # yellow-800
            fontName='Helvetica-Bold',
            leading=16.5,  # 1.5 line spacing (11pt * 1.5)
            keepWithNext=1  # Prevent orphan lines
        ))
        
        self.styles.add(ParagraphStyle(
            name='Missing',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.Color(0.6, 0.267, 0.133),    # orange-800
            fontName='Helvetica-Bold',
            leading=16.5,  # 1.5 line spacing (11pt * 1.5)
            keepWithNext=1  # Prevent orphan lines
        ))
    
    def generate_report(self, 
                       validation_data: Dict[str, Any], 
                       project_info: Optional[Dict] = None,
                       image_data: Optional[str] = None) -> bytes:
        """
        Generate a complete compliance report PDF
        
        Args:
            validation_data: Results from roof validation process
            project_info: Optional project metadata
            image_data: Optional base64 encoded image data
            
        Returns:
            bytes: PDF file content
        """
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build story
        story = []
        
        # Header
        story.extend(self._build_header(project_info))
        
        # Design section with image (if provided)
        if image_data:
            story.extend(self._build_design_section(image_data))
        
        # Main content (combines all sections like UI preview)
        story.extend(self._build_executive_summary(validation_data))
        
        # Footer
        story.extend(self._build_footer(validation_data))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _build_header(self, project_info: Optional[Dict] = None) -> list:
        """Build header section with table (no report ID)"""
        story = []
        # project_info is available for future use if needed
        
        # Title
        story.append(Paragraph("ROOF DESIGN COMPLIANCE REPORT", self.styles['CustomTitle']))
        story.append(Spacer(1, 8))
        
        # Header info table without Report ID
        data = [
            ['Report Date:', datetime.now().strftime('%B %d, %Y')],
            ['Generated By:', 'Roof Design Validator'],
            ['Code Reference:', 'Florida Residential Building Code 2023']
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.9)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 12))
        
        return story
    
    def _build_design_section(self, image_data: str) -> list:
        """Build design section with uploaded image"""
        story = []
        
        # Add section header following the same pattern as other sections
        story.append(Paragraph("1. Design", self.styles['SectionHeader']))
        
        try:
            # Decode base64 image data
            if image_data.startswith('data:image'):
                # Remove data URL prefix if present
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            
            # Create image from bytes
            image_buffer = io.BytesIO(image_bytes)
            img = Image(image_buffer)
            
            # Calculate optimal size for the image
            # Available width: 6.5 inches (8.5" - 2" margins)
            # We'll use 6 inches max width to leave some breathing room
            max_width = 6.0 * inch
            max_height = 4.5 * inch  # Reasonable max height to avoid overwhelming the page
            
            # Calculate scaling to fit within bounds while maintaining aspect ratio
            img_width, img_height = img.imageWidth, img.imageHeight
            
            # Calculate scale factors
            width_scale = max_width / img_width
            height_scale = max_height / img_height
            
            # Use the smaller scale to ensure image fits within both width and height limits
            scale = min(width_scale, height_scale, 1.0)  # Don't scale up, only down
            
            # Apply scaling
            img.drawWidth = img_width * scale
            img.drawHeight = img_height * scale
            
            # Center the image horizontally
            img.hAlign = 'CENTER'
            
            # Add some spacing before the image
            story.append(Spacer(1, 8))
            
            # Add the image
            story.append(img)
            
            # Add spacing after the image
            story.append(Spacer(1, 12))
            
        except Exception:
            # If image processing fails, add a placeholder message
            story.append(Spacer(1, 8))
            story.append(Paragraph("Image could not be processed for display.", self.styles['Content']))
            story.append(Spacer(1, 12))
        
        return story
    
    def _build_executive_summary(self, validation_data: Dict[str, Any]) -> list:
        """Build executive summary section with hierarchical structure"""
        story = []
        
        # Parse the validation report to match UI structure exactly
        validation_report = validation_data.get('validation_report', '')
        
        # Process the report line by line like the UI does
        lines = validation_report.split('\n')
        
        # Section counter for numbering
        section_counter = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 3))
                continue
                
            # Clean line of markdown formatting and remove quotes
            clean_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
            clean_line = re.sub(r'<[^>]*>', '', clean_line)
            # Remove quotes around specifications (e.g., "24" O.C." becomes 24 O.C.")
            clean_line = re.sub(r'"([^"]*)"', r'\1', clean_line)
            # Remove any remaining quotes
            clean_line = re.sub(r"'([^']*)'", r'\1', clean_line)
            # Remove trailing quotes at end of sentences
            clean_line = re.sub(r'["\']+$', '', clean_line)
            # Remove escaped quotes
            clean_line = clean_line.replace('\\"', '').replace("\\'", '')
            # Clean up any double spaces
            clean_line = re.sub(r'\s+', ' ', clean_line).strip()
            
            # Check for main section headers - convert to PascalCase and number them
            if re.match(r'^###\s*(.+)$', line) or \
               re.match(r'^\*\*(VALIDATION CHECKLIST|SUMMARY):\*\*\s*$', line) or \
               re.match(r'^(TECHNICAL SPECIFICATIONS|COMPLIANCE ASSESSMENT|CRITICAL FINDINGS|SUMMARY|OVERALL STATUS)', clean_line):
                
                display_text = re.sub(r'^###\s*', '', line)
                display_text = re.sub(r'^\*\*(.+):\*\*\s*$', r'\1', display_text)  # Remove colon for sections
                display_text = display_text.rstrip(':')  # Remove any trailing colon
                
                # Convert to PascalCase
                pascal_text = self._to_pascal_case(display_text)
                
                # Number the section
                section_counter += 1
                numbered_text = f"{section_counter}. {pascal_text}"
                
                story.append(Paragraph(numbered_text, self.styles['SectionHeader']))
                continue
                
            # Check for subsection headers - make them bulleted and convert to PascalCase with colon
            if re.match(r'^\*\*([^*]+):\*\*\s*$', line) or \
               re.match(r'^(DIMENSIONS FOUND|MATERIALS IDENTIFIED|SLOPE/PITCH DETAILS|STRUCTURAL ELEMENTS|CRITICAL FINDINGS|REQUIRED CORRECTIONS):$', clean_line):
                
                display_text = re.sub(r'^\*\*(.+):\*\*\s*$', r'\1', line)  # Remove markdown
                display_text = display_text.rstrip(':')  # Remove existing colon
                
                # Convert to PascalCase and add bullet point with colon (larger, more noticeable bullet)
                pascal_text = self._to_pascal_case(display_text)
                bulleted_text = f"<font size=16><b>•</b></font> {pascal_text}:"
                story.append(Paragraph(bulleted_text, self.styles['SubHeader']))
                continue
                
            # Check for content that should be indented (starts with -)
            if clean_line.startswith('-') and not re.match(r'^(Sheathing|Rafter Spacing/Spans|Fastening/Connections|Underlayment|Insulation|Wind Resistance):', clean_line):
                # Remove the dash and indent the content with small, subtle hollow circle bullet
                indented_text = clean_line[1:].strip()
                story.append(Paragraph(f"<font size=11>-</font> {indented_text}", self.styles['ContentBullet']))
                continue
                
            # Check for validation checklist items with color coding
            checklist_match = re.match(r'^(Sheathing|Rafter Spacing/Spans|Fastening/Connections|Underlayment|Insulation|Wind Resistance):\s*(COMPLIANT|NON-COMPLIANT|REQUIRES FURTHER REVIEW|MISSING)', clean_line)
            if checklist_match:
                _, status = checklist_match.groups()
                
                # Get appropriate style and background color based on status
                if status == 'COMPLIANT':
                    style_name = 'Compliant'
                    bg_color = colors.Color(0.9, 0.98, 0.9)        # light green
                    border_color = colors.Color(0.2, 0.7, 0.2)     # green border
                elif status == 'NON-COMPLIANT':
                    style_name = 'NonCompliant'
                    bg_color = colors.Color(0.98, 0.9, 0.9)        # light red
                    border_color = colors.Color(0.8, 0.2, 0.2)     # red border
                elif status == 'REQUIRES FURTHER REVIEW':
                    style_name = 'Review'
                    bg_color = colors.Color(0.98, 0.96, 0.87)      # light yellow
                    border_color = colors.Color(0.8, 0.6, 0.133)   # yellow border
                elif status == 'MISSING':
                    style_name = 'Missing'
                    bg_color = colors.Color(0.95, 0.95, 0.95)      # light gray
                    border_color = colors.Color(0.5, 0.5, 0.5)     # gray border
                else:
                    style_name = 'Normal'
                    bg_color = colors.white
                    border_color = colors.black
                
                # Create a table with filled background and rounded appearance
                validation_table = Table([[Paragraph(clean_line, self.styles[style_name])]], 
                                       colWidths=[7.5*inch])
                validation_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), bg_color),
                    ('BOX', (0, 0), (-1, -1), 1.5, border_color),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('ROUNDEDCORNERS', [3, 3, 3, 3]),  # Add rounded corners
                ]))
                
                story.append(validation_table)
                continue
                
            # Regular content
            if clean_line:
                story.append(Paragraph(clean_line, self.styles['Content']))
                
        return story
    
    def _build_design_analysis(self, validation_data: Dict[str, Any]) -> list:
        """Build design analysis section - this is now integrated into the main report parsing"""
        # This method is kept for compatibility but content is handled in _build_executive_summary
        # validation_data is available for future use if needed
        return []
    
    def _build_code_validation(self, validation_data: Dict[str, Any]) -> list:
        """Build code validation section - this is now integrated into the main report parsing"""
        # This method is kept for compatibility but content is handled in _build_executive_summary
        # validation_data is available for future use if needed
        return []
    
    def _build_recommendations(self, validation_data: Dict[str, Any]) -> list:
        """Build recommendations section - now integrated into main report parsing"""
        # This method is kept for compatibility but content is handled in _build_executive_summary
        # validation_data is available for future use if needed
        return []
    
    def _build_footer(self, validation_data: Dict[str, Any]) -> list:
        """Build simplified report footer"""
        story = []
        
        story.append(Spacer(1, 12))
        story.append(Paragraph("DISCLAIMER", self.styles['SectionHeader']))
        
        disclaimer = """
        This report is generated by an AI-powered building code compliance system. 
        While every effort has been made to ensure accuracy, this report should be 
        reviewed by a licensed professional engineer or architect before submission 
        for permits. The AI system is based on the Florida Building Code 2023 edition 
        and may not reflect the most current code amendments or local jurisdictional requirements.
        """
        
        story.append(Paragraph(disclaimer, self.styles['Normal']))
        
        return story
    
    def _determine_overall_status(self, validation_data: Dict[str, Any]) -> str:
        """Determine overall compliance status from validation report"""
        validation_report = validation_data.get('validation_report', '')
        
        # Look for overall status in the report
        if 'OVERALL STATUS: COMPLIANT' in validation_report:
            return 'COMPLIANT'
        elif 'OVERALL STATUS: NON-COMPLIANT' in validation_report:
            return 'NON-COMPLIANT'
        elif 'OVERALL STATUS: REQUIRES REVIEW' in validation_report or 'OVERALL STATUS: REQUIRES FURTHER REVIEW' in validation_report:
            return 'REQUIRES REVIEW'
        elif 'OVERALL STATUS: MISSING' in validation_report:
            return 'MISSING'
        else:
            # Fallback based on success flag
            return 'COMPLIANT' if validation_data.get('success', False) else 'REQUIRES REVIEW'