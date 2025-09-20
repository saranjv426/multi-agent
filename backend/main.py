"""
FastAPI Backend for Roof Design Validation System
RESTful API server for coordinating GPT-4o based validation workflow
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import os
import uvicorn
import logging
from datetime import datetime

from agents.orchestrator import RoofValidationOrchestrator
from agents.optimized_orchestrator import OptimizedRoofValidator
from config import settings
from utils.pdf_generator import ComplianceReportGenerator
from auth.routes import router as auth_router, init_auth_service
from auth.middleware import require_auth, set_auth_service
from database.connection import init_database

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Roof Design Validation API",
    description="API for automated building code compliance checking using Navigator AI GPT-4o",
    version="1.0.0"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)

# Global instances
orchestrator = None
optimized_validator = None
pdf_generator = ComplianceReportGenerator()

@app.on_event("startup")
async def startup_event():
    """Initialize the orchestrator and authentication system."""
    global orchestrator, optimized_validator
    
    logger.info("Starting Roof Design Validation API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Cost Tracking: {'Enabled' if settings.track_api_costs else 'Disabled'}")
    
    try:
        # Initialize database
        logger.info("🗄️ Initializing database...")
        db_connected = init_database()
        if db_connected:
            logger.info("✅ Database initialized successfully")
        else:
            logger.error("❌ Database connection failed")
            raise Exception("Database initialization failed")
        
        # Initialize authentication service
        logger.info("🔐 Initializing authentication service...")
        auth_service = init_auth_service(settings.jwt_secret_key, settings.frontend_url)
        set_auth_service(auth_service)
        logger.info("✅ Authentication service initialized")
        
        # Initialize orchestrators
        orchestrator = RoofValidationOrchestrator(settings.navigator_api_key, settings.navigator_base_url)
        optimized_validator = OptimizedRoofValidator(settings.navigator_api_key, settings.navigator_base_url)
        logger.info("✅ Orchestrator initialized successfully with Navigator AI")
        logger.info("✅ Optimized validator initialized successfully with Navigator AI")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise

@app.get("/")
async def root():
    """API health check and information."""
    return {
        "message": "Roof Design Validation API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/system/status")
async def get_system_status():
    """Get current system status."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return orchestrator.get_system_status()

@app.post("/api/validation/validate")
async def validate_roof_design(
    file: UploadFile = File(...),
    validation_options: Optional[str] = None,
    user: Dict[str, Any] = Depends(require_auth)
):
    """
    Complete roof design validation workflow.
    
    Args:
        file: Roof design image file (PNG, JPG, PDF)
        validation_options: Optional JSON string with validation parameters
        
    Returns:
        Complete validation results with compliance report
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        # Validate file type
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(allowed_types)}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Parse validation options if provided
        options = None
        if validation_options:
            try:
                import json
                options = json.loads(validation_options)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid validation_options JSON")
        
        # Run validation workflow
        result = await orchestrator.validate_roof_design(
            file_content, 
            filename=file.filename,
            validation_options=options
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post("/api/validation/validate-optimized")
async def validate_roof_design_optimized(
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(require_auth)
):
    """
    OPTIMIZED VALIDATION - Single GPT-4o call for both analysis and validation
    
    Performance improvements:
    - Processing time: ~43s → ~15s (65% faster)
    - Cost reduction: ~$0.035 → ~$0.020 (43% cheaper)
    - API calls: 2 → 1 (50% fewer calls)
    
    Args:
        file: Roof design image file (PNG, JPG, PDF)
        
    Returns:
        Complete validation results with performance metrics
    """
    if not optimized_validator:
        raise HTTPException(status_code=503, detail="Optimized validator not initialized")
    
    try:
        logger.info(f"Starting optimized validation for: {file.filename}")
        
        # Read file content
        file_content = await file.read()
        
        # Single optimized call
        result = optimized_validator.validate_roof_design_optimized(
            file_content, 
            filename=file.filename
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Optimized validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Optimized validation failed: {str(e)}")

@app.post("/api/validation/validate-element")
async def validate_specific_element(
    file: UploadFile = File(...),
    element_type: str = "sheathing"
):
    """
    Validate a specific design element.
    
    Args:
        file: Roof design image file
        element_type: Element to validate (sheathing, spacing, materials, etc.)
        
    Returns:
        Element-specific validation results
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Validate specific element
        result = orchestrator.validate_specific_element(
            file_content,
            element_type,
            filename=file.filename
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Element validation failed: {str(e)}")

@app.post("/api/reports/compliance")
async def generate_compliance_report(validation_results: Dict[str, Any]):
    """
    Generate a professional compliance report from validation results.
    
    Args:
        validation_results: Results from validation workflow
        
    Returns:
        Formatted compliance report
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        report = orchestrator.generate_compliance_report(validation_results)
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@app.get("/api/workflow/history")
async def get_workflow_history():
    """Get history of validation workflows."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return {
        "history": orchestrator.get_workflow_history(),
        "total_workflows": len(orchestrator.get_workflow_history())
    }

@app.get("/api/workflow/current")
async def get_current_workflow():
    """Get status of current workflow."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    current = orchestrator.get_current_workflow_status()
    return {"current_workflow": current}

@app.delete("/api/workflow/history")
async def clear_workflow_history():
    """Clear workflow history."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    orchestrator.clear_workflow_history()
    return {"message": "Workflow history cleared"}

@app.get("/api/agents/test")
async def test_agents():
    """Test agent connectivity and functionality."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        # Simple test - could be enhanced with actual test calls
        status = orchestrator.get_system_status()
        
        return {
            "agent1_status": "ready" if status["system_status"]["agent1_ready"] else "not ready",
            "agent2_status": "ready" if status["system_status"]["agent2_ready"] else "not ready",
            "system_ready": status["system_status"]["system_ready"],
            "test_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent test failed: {str(e)}")

@app.post("/generate-pdf-report")
async def generate_pdf_report(validation_data: Dict[str, Any]):
    """
    Generate a professional PDF compliance report from validation results.
    
    Args:
        validation_data: Complete validation results from roof analysis
        
    Returns:
        PDF file as downloadable attachment
    """
    try:
        logger.info("Generating PDF compliance report...")
        
        # Generate PDF bytes
        pdf_bytes = pdf_generator.generate_report(validation_data)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"roof_compliance_report_{timestamp}.pdf"
        
        logger.info(f"PDF report generated successfully: {filename}")
        
        # Return PDF as downloadable file
        from fastapi.responses import Response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_bytes))
            }
        )
        
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )