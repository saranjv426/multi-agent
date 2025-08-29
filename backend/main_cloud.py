"""
Cloud-optimized FastAPI Backend for Roof Design Validation System
Optimized for Railway/Render deployment
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from typing import Optional, Dict, Any
import os
import logging
from datetime import datetime

from agents.orchestrator import RoofValidationOrchestrator
from agents.optimized_orchestrator import OptimizedRoofValidator
from config import settings
from utils.pdf_generator import ComplianceReportGenerator

# Configure logging for cloud
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Roof Design Validation API",
    description="AI-powered building code compliance checking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for cloud deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permissive for demo - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
orchestrator = None
optimized_validator = None
pdf_generator = ComplianceReportGenerator()

@app.on_event("startup")
async def startup_event():
    """Initialize the system with Navigator AI API key."""
    global orchestrator, optimized_validator
    
    logger.info("🚀 Starting Roof Design Validation API...")
    logger.info(f"Environment: {settings.environment}")
    
    try:
        orchestrator = RoofValidationOrchestrator(settings.navigator_api_key, settings.navigator_base_url)
        optimized_validator = OptimizedRoofValidator(settings.navigator_api_key, settings.navigator_base_url)
        logger.info("✅ System initialized successfully with Navigator AI")
    except Exception as e:
        logger.error(f"❌ Failed to initialize system: {e}")
        raise

@app.get("/")
async def root():
    """API health check and information."""
    return {
        "message": "🏠 Roof Design Validation API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for cloud platforms."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/validation/validate-optimized")
async def validate_roof_design_optimized(file: UploadFile = File(...)):
    """
    OPTIMIZED VALIDATION - Single AI call for analysis and validation
    Perfect for cloud deployment with faster processing
    """
    if not optimized_validator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        logger.info(f"🔍 Starting validation for: {file.filename}")
        
        # Validate file type
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Single optimized call
        result = optimized_validator.validate_roof_design_optimized(
            file_content, 
            filename=file.filename
        )
        
        if result['success']:
            logger.info(f"✅ Validation completed in {result['processing_time']:.1f}s")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post("/api/validation/validate")
async def validate_roof_design_detailed(
    file: UploadFile = File(...),
    validation_options: Optional[str] = None
):
    """Complete detailed validation workflow (2-agent process)."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        logger.info(f"🔍 Starting detailed validation for: {file.filename}")
        
        # Validate file type
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}"
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
        
        # Run detailed validation workflow
        result = await orchestrator.validate_roof_design(
            file_content, 
            filename=file.filename,
            validation_options=options
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Detailed validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.get("/api/system/status")
async def get_system_status():
    """Get current system status."""
    return {
        "status": "operational",
        "agents": {
            "optimized_validator": "ready" if optimized_validator else "not ready",
            "orchestrator": "ready" if orchestrator else "not ready"
        },
        "environment": settings.environment,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/generate-pdf-report")
async def generate_pdf_report(validation_data: Dict[str, Any]):
    """Generate a professional PDF compliance report."""
    try:
        logger.info("📄 Generating PDF compliance report...")
        
        # Generate PDF bytes
        pdf_bytes = pdf_generator.generate_report(validation_data)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"roof_compliance_report_{timestamp}.pdf"
        
        logger.info(f"✅ PDF report generated: {filename}")
        
        # Return PDF as downloadable file
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_bytes))
            }
        )
        
    except Exception as e:
        logger.error(f"❌ PDF generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

# For cloud platforms that need a specific app entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_cloud:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )
