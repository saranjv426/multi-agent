"""
Cloud-optimized FastAPI Backend for Roof Design Validation System
Optimized for Railway/Render deployment
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from typing import Optional, Dict, Any, List
import os
import re
import logging
from pathlib import Path
from datetime import datetime

from agents.orchestrator import RoofValidationOrchestrator
from agents.optimized_orchestrator import OptimizedRoofValidator
from config import settings
from utils.pdf_generator import ComplianceReportGenerator
from auth.routes import router as auth_router, init_auth_service
from auth.middleware import require_auth, set_auth_service
from database.connection import init_database

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
    allow_origins=settings.allowed_origins,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)

# Global instances
orchestrator = None
optimized_validator = None
optimized_validators: Dict[str, OptimizedRoofValidator] = {}
pdf_generator = ComplianceReportGenerator()

STATIC_MODEL_ALIASES = {
    "mistral": "mistral-small-3.1",
    "gpt52": "gpt-5.2",
    "llama": "llama-3.1-nemotron-nano-8B-v1",
}

EXTRACTION_MODE_ALIASES = {
    "wall-sections": "wall-sections",
    "wall_sections": "wall-sections",
    "extract": "wall-sections",
    "direct": "direct",
    "full-page": "direct",
    "full_page": "direct",
}


def normalize_model_choice(selected_model: str) -> str:
    normalized = (selected_model or "").strip()
    if normalized in optimized_validators:
        return normalized

    available_models = list(optimized_validators.keys())
    aliases = {model.lower(): model for model in available_models}
    aliases.update(
        {
            alias: model
            for alias, model in STATIC_MODEL_ALIASES.items()
            if model in optimized_validators
        }
    )
    return aliases.get(normalized.lower(), available_models[0] if available_models else "mistral-small-3.1")


def normalize_extraction_mode(extraction_mode: str) -> str:
    return EXTRACTION_MODE_ALIASES.get((extraction_mode or "").strip().lower(), "wall-sections")


def build_report_filename(selected_model: Optional[str]) -> str:
    model_name = (selected_model or "model").strip() or "model"
    safe_model_name = re.sub(r"[^A-Za-z0-9_-]+", "_", model_name).strip("_") or "model"
    return f"{safe_model_name}.pdf"


def _read_env_assignments() -> Dict[str, List[str]]:
    assignments: Dict[str, List[str]] = {}
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return assignments

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        assignments.setdefault(key, []).append(value)

    return assignments


def build_optimized_validators() -> Dict[str, OptimizedRoofValidator]:
    validators: Dict[str, OptimizedRoofValidator] = {}
    env_assignments = _read_env_assignments()

    def register_validator(
        *,
        api_key: Optional[str],
        api_base: Optional[str],
        main_model: Optional[str],
        summary_model: Optional[str],
    ) -> None:
        resolved_model = (main_model or "").strip()
        if not api_key or not resolved_model:
            return

        validators[resolved_model] = OptimizedRoofValidator(
            api_key,
            api_base or "https://api.openai.com/v1",
            resolved_model,
            (summary_model or resolved_model).strip() or resolved_model,
        )

    def get_assigned_values(name: str) -> List[str]:
        values = [value.strip() for value in env_assignments.get(name, []) if value.strip()]
        if values:
            return values

        current_value = (os.getenv(name) or "").strip()
        return [current_value] if current_value else []

    mistral_api_key = os.getenv("MISTRAL_API_KEY") or os.getenv("NAVIGATOR_API_KEY")
    if mistral_api_key:
        mistral_api_base = (
            os.getenv("MISTRAL_API_BASE")
            or os.getenv("NAVIGATOR_BASE_URL")
            or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        )
        mistral_models = get_assigned_values("MISTRAL_MAIN_MODEL") or ["mistral-small-3.1"]
        mistral_summaries = get_assigned_values("MISTRAL_SUMMARY_MODEL")
        for index, main_model in enumerate(mistral_models):
            register_validator(
                api_key=mistral_api_key,
                api_base=mistral_api_base,
                main_model=main_model,
                summary_model=mistral_summaries[index] if index < len(mistral_summaries) else main_model,
            )

    llama_api_key = os.getenv("LLAMA_API_KEY") or os.getenv("NAVIGATOR_API_KEY")
    llama_models = get_assigned_values("LLAMA_MAIN_MODEL")
    if llama_api_key and llama_models:
        llama_summaries = get_assigned_values("LLAMA_SUMMARY_MODEL")
        for index, main_model in enumerate(llama_models):
            register_validator(
                api_key=llama_api_key,
                api_base=(
                    os.getenv("LLAMA_API_BASE")
                    or os.getenv("NAVIGATOR_BASE_URL")
                    or os.getenv("OPENAI_API_BASE")
                    or "https://api.openai.com/v1"
                ),
                main_model=main_model,
                summary_model=llama_summaries[index] if index < len(llama_summaries) else main_model,
            )

    gpt52_api_key = os.getenv("GPT52_API_KEY") or os.getenv("OPENAI_API_KEY")
    gpt52_models = get_assigned_values("GPT52_MAIN_MODEL")
    if gpt52_api_key and gpt52_models:
        gpt52_summaries = get_assigned_values("GPT52_SUMMARY_MODEL")
        for index, main_model in enumerate(gpt52_models):
            register_validator(
                api_key=gpt52_api_key,
                api_base=(
                    os.getenv("GPT52_API_BASE")
                    or os.getenv("OPENAI_API_BASE")
                    or "https://api.openai.com/v1"
                ),
                main_model=main_model,
                summary_model=gpt52_summaries[index] if index < len(gpt52_summaries) else main_model,
            )

    legacy_models = get_assigned_values("MAIN_MODEL")
    legacy_summaries = get_assigned_values("SUMMARY_MODEL")
    if legacy_models:
        for index, main_model in enumerate(legacy_models):
            register_validator(
                api_key=os.getenv("OPENAI_API_KEY") or os.getenv("GPT52_API_KEY"),
                api_base=(
                    os.getenv("OPENAI_API_BASE")
                    or os.getenv("GPT52_API_BASE")
                    or "https://api.openai.com/v1"
                ),
                main_model=main_model,
                summary_model=legacy_summaries[index] if index < len(legacy_summaries) else main_model,
            )

    return validators


def resolve_validator(selected_model: str) -> tuple[str, OptimizedRoofValidator]:
    normalized_model = normalize_model_choice(selected_model)
    validator = optimized_validators.get(normalized_model)
    if validator is None:
        available = ", ".join(sorted(optimized_validators.keys())) or "none"
        raise HTTPException(
            status_code=503,
            detail=(
                f"Model '{normalized_model}' is not configured on the server. "
                f"Available models: {available}"
            ),
        )
    return normalized_model, validator


def _combine_document_results(
    document_result: Dict[str, Any],
    *,
    filename: str,
    selected_model: str,
    source_file_index: int,
) -> Dict[str, Any]:
    drawing_results = document_result.get("results") or []
    if not drawing_results:
        return {
            "filename": filename,
            "source_filename": filename,
            "source_file_index": source_file_index,
            "source_document_key": f"{source_file_index}:{filename}",
            "selected_model": selected_model,
            "success": False,
            "error": document_result.get("error", "No drawings extracted from document"),
            "processing_time": document_result.get("processing_time", 0),
            "results": [],
        }

    successful_results = [result for result in drawing_results if result.get("success")]
    summed_drawing_processing_time = sum(
        result.get("processing_time", 0) or 0 for result in drawing_results
    )
    combined_result: Dict[str, Any] = {
        "filename": filename,
        "source_filename": filename,
        "source_file_index": source_file_index,
        "source_document_key": f"{source_file_index}:{filename}",
        "selected_model": selected_model,
        "success": bool(successful_results),
        "processing_time": document_result.get("processing_time", 0) or summed_drawing_processing_time,
        "aggregate_drawing_processing_time": summed_drawing_processing_time,
        "total_drawings": len(drawing_results),
        "successful_drawings": len(successful_results),
        "failed_drawings": len(drawing_results) - len(successful_results),
        "raw_total_drawings": document_result.get("filtered_from_total_drawings", len(drawing_results)),
        "results": [],
    }

    for result in drawing_results:
        enriched = result.copy()
        enriched["source_filename"] = enriched.get("source_filename") or filename
        enriched["source_file_index"] = source_file_index
        enriched["source_document_key"] = f"{source_file_index}:{enriched['source_filename']}"
        enriched["selected_model"] = selected_model
        if document_result.get("extraction_diagnostics") and not enriched.get("extraction_diagnostics"):
            enriched["extraction_diagnostics"] = document_result["extraction_diagnostics"]
        combined_result["results"].append(enriched)

    if document_result.get("extraction_diagnostics"):
        extraction_diagnostics = document_result["extraction_diagnostics"].copy()
        extraction_diagnostics["raw_total_drawings"] = extraction_diagnostics.get(
            "total_drawings",
            document_result.get("filtered_from_total_drawings", len(drawing_results)),
        )
        extraction_diagnostics["filtered_total_drawings"] = len(drawing_results)
        combined_result["extraction_diagnostics"] = extraction_diagnostics

    primary_result = successful_results[0] if successful_results else drawing_results[0]
    for field in (
        "validation_report",
        "analysis",
        "compliance_report",
        "parsed_report",
        "report_image_data",
        "estimated_cost",
    ):
        if primary_result.get(field) is not None:
            combined_result[field] = primary_result[field]

    if not successful_results:
        combined_result["error"] = document_result.get("error") or primary_result.get("error")

    return combined_result

@app.on_event("startup")
async def startup_event():
    """Initialize the orchestrator and authentication system."""
    global orchestrator, optimized_validator, optimized_validators
    
    logger.info("🚀 Starting Roof Design Validation API...")
    logger.info(f"Environment: {settings.environment}")
    
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
        orchestrator = RoofValidationOrchestrator(
            settings.openai_api_key,
            settings.openai_api_base,
            settings.openai_main_model,
            settings.openai_summary_model
        )
        optimized_validators = build_optimized_validators()
        if not optimized_validators:
            raise Exception(
                "No AI validator models configured. Set MISTRAL_API_KEY and/or GPT52_API_KEY."
            )
        optimized_validator = (
            optimized_validators.get("mistral-small-3.1")
            or next(iter(optimized_validators.values()))
        )
        logger.info(
            f"✅ System initialized successfully with models: {', '.join(sorted(optimized_validators.keys()))}"
        )
        
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
async def validate_roof_design_optimized(
    file: UploadFile = File(...),
    selected_model: str = Form("mistral-small-3.1"),
    extraction_mode: str = Form("wall-sections"),
    user: Dict[str, Any] = Depends(require_auth)
):
    """
    OPTIMIZED VALIDATION - Single AI call for analysis and validation
    Perfect for cloud deployment with faster processing
    """
    if not optimized_validator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        normalized_model, validator = resolve_validator(selected_model)
        normalized_extraction_mode = normalize_extraction_mode(extraction_mode)
        logger.info(f"🔍 Starting validation for: {file.filename} with model: {normalized_model}")
        
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
        result = validator.validate_document_optimized(
            file_content, 
            filename=file.filename,
            extraction_mode=normalized_extraction_mode,
        )
        result["selected_model"] = normalized_model
        result["extraction_mode"] = normalized_extraction_mode
        
        if result['success']:
            logger.info(f"✅ Validation completed in {result['processing_time']:.1f}s")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post("/api/validation/validate-optimized-batch")
async def validate_roof_design_optimized_batch(
    files: List[UploadFile] = File(...),
    selected_model: str = Form("mistral-small-3.1"),
    extraction_mode: str = Form("wall-sections"),
    user: Dict[str, Any] = Depends(require_auth)
):
    """Batch optimized validation for up to 3 files in one request."""
    if not optimized_validators:
        raise HTTPException(status_code=503, detail="System not initialized")

    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    if len(files) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 files are allowed per request")

    allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf', 'image/gif']
    results = []
    file_statuses = []
    normalized_model, validator = resolve_validator(selected_model)
    normalized_extraction_mode = normalize_extraction_mode(extraction_mode)

    for file_index, file in enumerate(files):
        if file.content_type not in allowed_types:
            results.append({
                "filename": file.filename,
                "source_filename": file.filename,
                "source_file_index": file_index,
                "source_document_key": f"{file_index}:{file.filename}",
                "success": False,
                "error": f"Unsupported file type: {file.content_type}"
            })
            file_statuses.append(False)
            continue

        try:
            logger.info(f"🔍 Starting batch validation for: {file.filename} with model: {normalized_model}")
            file_content = await file.read()

            document_result = validator.validate_document_optimized(
                file_content,
                filename=file.filename,
                extraction_mode=normalized_extraction_mode,
            )
            combined_result = _combine_document_results(
                document_result,
                filename=file.filename,
                selected_model=normalized_model,
                source_file_index=file_index,
            )
            results.append(combined_result)
            file_statuses.append(combined_result.get("success", False))

            if combined_result.get('success'):
                logger.info(f"✅ Validation completed for {file.filename}")
        except Exception as e:
            logger.error(f"❌ Batch validation failed for {file.filename}: {str(e)}")
            results.append({
                "filename": file.filename,
                "source_filename": file.filename,
                "source_file_index": file_index,
                "source_document_key": f"{file_index}:{file.filename}",
                "success": False,
                "error": f"Validation failed: {str(e)}"
            })
            file_statuses.append(False)

    successful_drawings = sum(result.get("successful_drawings", 0) for result in results)
    total_drawings = sum(result.get("total_drawings", 1) for result in results)
    successful_files = len([status for status in file_statuses if status])
    return {
        "success": successful_files > 0,
        "selected_model": normalized_model,
        "extraction_mode": normalized_extraction_mode,
        "total_files": len(files),
        "successful_files": successful_files,
        "failed_files": len(files) - successful_files,
        "total_drawings": total_drawings,
        "successful_drawings": successful_drawings,
        "failed_drawings": total_drawings - successful_drawings,
        "results": results
    }

@app.post("/api/validation/validate")
async def validate_roof_design_detailed(
    file: UploadFile = File(...),
    validation_options: Optional[str] = None,
    user: Dict[str, Any] = Depends(require_auth)
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
async def get_system_status(user: Dict[str, Any] = Depends(require_auth)):
    """Get current system status."""
    return {
        "status": "operational",
        "agents": {
            "optimized_validator": "ready" if optimized_validator else "not ready",
            "orchestrator": "ready" if orchestrator else "not ready"
        },
        "available_models": sorted(list(optimized_validators.keys())),
        "default_model": (
            "mistral-small-3.1"
            if "mistral-small-3.1" in optimized_validators
            else (next(iter(optimized_validators.keys()), None))
        ),
        "environment": settings.environment,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/generate-pdf-report")
async def generate_pdf_report(
    request_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_auth)
):
    """Generate a professional PDF compliance report."""
    try:
        logger.info("📄 Generating PDF compliance report...")
        
        # Handle both legacy and wrapped payload formats
        if "validation_data" in request_data:
            validation_data = request_data["validation_data"]
            image_data = request_data.get("image_data")
            selected_model = request_data.get("selected_model") or validation_data.get("selected_model")
            logger.info("📦 Using wrapped validation payload")
        else:
            validation_data = request_data
            image_data = None
            selected_model = validation_data.get("selected_model")
            logger.info("📄 Using legacy format without image data")
        
        # Generate PDF bytes
        pdf_bytes = pdf_generator.generate_report(validation_data, image_data=image_data)
        
        filename = build_report_filename(selected_model)
        
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
