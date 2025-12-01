"""
Roof Validation Orchestrator
Coordinates Agent 1 (Image Analysis) and Agent 2 (Code Validation) using GPT-4o
"""

from typing import Dict, Optional, Any, List
import asyncio
import time
from .roof_analyzer import RoofDesignAnalyzer
from .code_validator import BuildingCodeValidator
from .design_parser import DesignParser

class RoofValidationOrchestrator:
    """
    Master orchestrator that coordinates the complete validation workflow:
    Image Input → Agent1 Analysis → Agent2 Validation → Compliance Report
    """
    
    def __init__(
        self,
        openai_api_key: str,
        api_base: str = "https://api.openai.com/v1",
        main_model: str = "gpt-5",
        summary_model: str = "gpt-5-mini"
    ):
        """
        Initialize the orchestrator with OpenAI models.
        
        Args:
            openai_api_key: API key for OpenAI access
            api_base: Optional API base URL (for Azure/OpenAI routing)
            main_model: Vision-capable model for extraction/validation
            summary_model: Lightweight model for follow-up summarization
        """
        self.openai_api_key = openai_api_key
        self.api_base = api_base
        self.main_model = main_model
        self.summary_model = summary_model
        
        # Initialize agents
        self.agent1 = RoofDesignAnalyzer(
            openai_api_key,
            api_base,
            vision_model=main_model
        )
        self.agent2 = BuildingCodeValidator(
            openai_api_key,
            api_base,
            validation_model=main_model,
            summary_model=summary_model
        )
        self.design_parser = DesignParser()
        
        # System status
        self.system_status = {
            "agent1_ready": True,
            "agent2_ready": True,
            "system_ready": True
        }
        
        # Workflow tracking
        self.current_workflow = None
        self.workflow_history = []
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "system_status": self.system_status,
            "agents": {
                "agent1": {
                    "name": "Roof Design Analyzer",
                    "technology": f"OpenAI {self.main_model} Vision API",
                    "status": "ready" if self.system_status["agent1_ready"] else "not ready"
                },
                "agent2": {
                    "name": "Building Code Validator", 
                    "technology": f"OpenAI {self.main_model}",
                    "status": "ready" if self.system_status["agent2_ready"] else "not ready"
                }
            }
        }
    
    async def validate_roof_design(self, image_file, filename: Optional[str] = None, 
                                 validation_options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Complete end-to-end roof design validation workflow.
        
        Args:
            image_file: Roof design image file
            filename: Optional filename
            validation_options: Optional validation parameters
            
        Returns:
            Dict containing complete validation results
        """
        workflow_id = f"workflow_{int(time.time())}"
        start_time = time.time()
        
        self.current_workflow = {
            "id": workflow_id,
            "filename": filename,
            "start_time": start_time,
            "status": "in_progress",
            "current_step": "initializing"
        }
        
        try:
            # Step 1: Agent1 - Image Analysis
            self.current_workflow["current_step"] = "agent1_analysis"
            
            print(f"Step 1: Agent1 analyzing roof design image...")
            agent1_result = self.agent1.analyze_roof_design(image_file, filename)
            
            if not agent1_result.get('success'):
                raise Exception(f"Agent1 analysis failed: {agent1_result.get('error')}")
            
            agent1_output = agent1_result['analysis']
            agent1_tokens = agent1_result['tokens_used']
            
            # Step 2: Parse design specifications (optional, for structured data)
            self.current_workflow["current_step"] = "parsing_specifications"
            
            print(f"Step 2: Parsing design specifications...")
            try:
                design_specs = self.design_parser.parse_agent1_output(agent1_output)
                design_summary = self.design_parser.get_design_summary(design_specs)
            except Exception as e:
                print(f"Warning: Could not parse design specs: {e}")
                design_specs = []
                design_summary = {}
            
            # Step 3: Agent2 - Building Code Validation
            self.current_workflow["current_step"] = "agent2_validation"
            
            print(f"Step 3: Agent2 validating against building codes...")
            agent2_result = self.agent2.validate_roof_design(agent1_output, validation_options)
            
            if not agent2_result.get('success'):
                raise Exception(f"Agent2 validation failed: {agent2_result.get('error')}")
            
            validation_report = agent2_result['validation_report']
            parsed_report = agent2_result['parsed_report']
            agent2_tokens = agent2_result['tokens_used']
            
            # Step 4: Generate summary and compliance report
            self.current_workflow["current_step"] = "generating_report"
            
            print(f"Step 4: Generating compliance report...")
            validation_summary = self.agent2.get_validation_summary(parsed_report)
            
            # Calculate total processing time
            processing_time = time.time() - start_time
            
            # Complete workflow result
            workflow_result = {
                "workflow_id": workflow_id,
                "success": True,
                "processing_time": processing_time,
                "filename": filename,
                
                # Agent 1 Results
                "agent1_results": {
                    "analysis": agent1_output,
                    "tokens_used": agent1_tokens,
                    "design_specs": design_specs,
                    "design_summary": design_summary
                },
                
                # Agent 2 Results
                "agent2_results": {
                    "validation_report": validation_report,
                    "parsed_report": parsed_report,
                    "tokens_used": agent2_tokens,
                    "validation_summary": validation_summary
                },
                
                # Overall Summary
                "overall_summary": {
                    "compliance_status": parsed_report.get('overall_status', 'UNKNOWN'),
                    "total_tokens_used": agent1_tokens + agent2_tokens,
                    "validation_confidence": parsed_report.get('confidence', {}),
                    "critical_violations": len(parsed_report.get('critical_violations', [])),
                    **validation_summary
                },
                
                "timestamp": time.time()
            }
            
            # Update workflow status
            self.current_workflow["status"] = "completed"
            self.current_workflow["current_step"] = "completed"
            self.current_workflow["result"] = workflow_result
            
            # Add to history
            self.workflow_history.append(self.current_workflow.copy())
            
            print(f"Validation completed successfully in {processing_time:.2f} seconds")
            
            return workflow_result
            
        except Exception as e:
            # Handle workflow errors
            error_result = {
                "workflow_id": workflow_id,
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "filename": filename,
                "timestamp": time.time()
            }
            
            # Update workflow status
            self.current_workflow["status"] = "failed"
            self.current_workflow["error"] = str(e)
            self.current_workflow["result"] = error_result
            
            # Add to history
            self.workflow_history.append(self.current_workflow.copy())
            
            print(f"Validation failed: {str(e)}")
            
            return error_result
    
    def validate_specific_element(self, image_file, element_type: str, 
                                filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a specific design element.
        
        Args:
            image_file: Roof design image file
            element_type: Specific element to validate
            filename: Optional filename
            
        Returns:
            Dict containing element-specific validation results
        """
        try:
            # Step 1: Agent1 Analysis (same as full validation)
            agent1_result = self.agent1.analyze_roof_design(image_file, filename)
            
            if not agent1_result.get('success'):
                raise Exception(f"Agent1 analysis failed: {agent1_result.get('error')}")
            
            # Step 2: Element-specific validation
            agent2_result = self.agent2.validate_specific_element(
                agent1_result['analysis'], element_type
            )
            
            if not agent2_result.get('success'):
                raise Exception(f"Element validation failed: {agent2_result.get('error')}")
            
            return {
                "success": True,
                "element_type": element_type,
                "agent1_analysis": agent1_result['analysis'],
                "element_validation": agent2_result['element_validation'],
                "tokens_used": agent1_result['tokens_used'] + agent2_result['tokens_used']
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "element_type": element_type
            }
    
    def generate_compliance_report(self, validation_results: Dict) -> Dict[str, Any]:
        """
        Generate a professional compliance report.
        
        Args:
            validation_results: Results from validation workflow
            
        Returns:
            Dict containing formatted compliance report
        """
        try:
            if not validation_results.get('success'):
                raise Exception("Cannot generate report from failed validation")
            
            report_result = self.agent2.generate_compliance_report(
                validation_results['agent2_results']
            )
            
            return report_result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_workflow_history(self) -> List[Dict]:
        """Get history of validation workflows."""
        return self.workflow_history
    
    def get_current_workflow_status(self) -> Optional[Dict]:
        """Get status of current workflow."""
        return self.current_workflow
    
    def clear_workflow_history(self):
        """Clear workflow history."""
        self.workflow_history = []
        self.current_workflow = None