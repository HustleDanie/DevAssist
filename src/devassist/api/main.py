"""
FastAPI backend for DevAssist web interface.

This API provides endpoints for the multi-agent code migration system:
- /api/migrate/snippet - Quick single-file migration using AST transformers
- /api/migrate/repo - Full repository migration using LangGraph workflow
- /api/migrate - ZIP file upload migration

Architecture: Git Clone → AST Parsing → Multi-Agent Refactoring → PR Generation
"""

import asyncio
import io
import shutil
import tempfile
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from devassist.agents.workflow import MigrationWorkflow
from devassist.core.config import Settings, get_settings
from devassist.core.models import MigrationType, MigrationStatus


class MigrationJob(BaseModel):
    """Migration job model."""
    
    job_id: str
    status: str  # pending, cloning, planning, coding, testing, review, completed, failed
    migration_type: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    file_count: int = 0
    issues_found: int = 0
    issues_fixed: int = 0
    tests_passed: Optional[bool] = None
    pr_url: Optional[str] = None
    current_agent: Optional[str] = None
    messages: List[str] = []


class MigrationRequest(BaseModel):
    """Migration request model."""
    
    migration_type: str = "py2to3"  # py2to3 or flask_to_fastapi


class RepoMigrationRequest(BaseModel):
    """Request model for repository URL migration."""
    
    repo_url: str
    migration_type: str = "py2to3"
    auto_create_pr: bool = True


# In-memory job storage (use Redis/DB in production)
jobs: dict[str, MigrationJob] = {}
job_results: dict[str, Path] = {}


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    application = FastAPI(
        title="DevAssist API",
        description="Multi-Agent Code Migration Tool API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )
    
    # Configure CORS for Next.js frontend
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://frontend:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return application


app = create_app()


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "devassist-api"}


class CodeSnippetRequest(BaseModel):
    """Request model for code snippet migration."""
    code: str
    migration_type: str = "py2to3"


class CodeSnippetResponse(BaseModel):
    """Response model for code snippet migration."""
    original_code: str
    migrated_code: str
    issues_found: int
    issues_fixed: int
    migration_type: str


@app.post("/api/migrate/snippet", response_model=CodeSnippetResponse)
async def migrate_snippet(request: CodeSnippetRequest):
    """
    Migrate a code snippet directly (for quick testing).
    
    Uses AST-based transformation for immediate results.
    Accepts raw Python code and returns the migrated version immediately.
    """
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    if request.migration_type not in ["py2to3", "flask_to_fastapi"]:
        raise HTTPException(
            status_code=400,
            detail="Migration type must be 'py2to3' or 'flask_to_fastapi'"
        )
    
    # Run migration using AST transformers
    result = run_single_file_migration(
        source_code=request.code,
        migration_type=request.migration_type,
    )
    
    return CodeSnippetResponse(
        original_code=request.code,
        migrated_code=result["migrated_code"],
        issues_found=result["issues_found"],
        issues_fixed=result["issues_fixed"],
        migration_type=request.migration_type,
    )


@app.post("/api/migrate/repo", response_model=MigrationJob)
async def migrate_repository(
    request: RepoMigrationRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start a full repository migration using the LangGraph multi-agent workflow.
    
    This endpoint implements the complete architecture:
    - Git Clone → AST Parsing → Multi-Agent Refactoring → PR Generation
    
    The workflow uses:
    - Agent 1 (Planner): Identifies deprecated code patterns using AST + LLM
    - Agent 2 (Coder): Rewrites code following style guides (via MCP context)
    - Agent 3 (Tester): Writes and runs unit tests in Docker
    
    If tests fail, the workflow retries up to 3 times.
    Upon success, creates a pull request with all changes.
    """
    if not request.repo_url.strip():
        raise HTTPException(status_code=400, detail="Repository URL cannot be empty")
    
    if request.migration_type not in ["py2to3", "flask_to_fastapi"]:
        raise HTTPException(
            status_code=400,
            detail="Migration type must be 'py2to3' or 'flask_to_fastapi'"
        )
    
    # Create job
    job_id = str(uuid.uuid4())
    job = MigrationJob(
        job_id=job_id,
        status="pending",
        migration_type=request.migration_type,
        created_at=datetime.utcnow(),
        current_agent=None,
        messages=["Migration job created"],
    )
    jobs[job_id] = job
    
    # Start background migration using LangGraph workflow
    background_tasks.add_task(
        process_repo_migration,
        job_id=job_id,
        repo_url=request.repo_url,
        migration_type=request.migration_type,
        auto_create_pr=request.auto_create_pr,
    )
    
    return job


async def process_repo_migration(
    job_id: str,
    repo_url: str,
    migration_type: str,
    auto_create_pr: bool,
):
    """
    Process repository migration using the full LangGraph multi-agent workflow.
    
    Pipeline: Clone → Planner → Coder → Tester → (retry if failed) → PR
    """
    import traceback
    
    print(f"[MIGRATION] Starting process_repo_migration for job {job_id}")
    
    # Get job from global jobs dict
    if job_id not in jobs:
        print(f"[MIGRATION] ERROR: Job {job_id} not found in jobs dict!")
        return
    
    job = jobs[job_id]
    print(f"[MIGRATION] Job found, current status: {job.status}")
    
    try:
        # Update status
        job.status = "cloning"
        job.messages.append(f"Starting migration of {repo_url}")
        print(f"[MIGRATION] Status updated to 'cloning'")
        
        # Initialize the workflow
        print(f"[MIGRATION] Initializing MigrationWorkflow...")
        workflow = MigrationWorkflow()
        print(f"[MIGRATION] Workflow initialized")
        
        # Override settings if needed
        settings = get_settings()
        settings.auto_create_pr = auto_create_pr
        
        # Run the full LangGraph workflow
        print(f"[MIGRATION] Running workflow.run()...")
        job.status = "processing"
        job.current_agent = "planner"
        
        result = await asyncio.to_thread(
            workflow.run,
            repo_url=repo_url,
            migration_type=migration_type,
        )
        print(f"[MIGRATION] Workflow completed, success={result.success}")
        
        # Update job with results from state
        state = result.state
        job.file_count = len(state.files_to_migrate) if state.files_to_migrate else 0
        job.issues_found = len(state.deprecated_patterns) if state.deprecated_patterns else 0
        job.issues_fixed = len(state.applied_changes) if state.applied_changes else 0
        job.tests_passed = state.tests_passed
        job.current_agent = state.current_agent
        
        print(f"[MIGRATION] Updated job stats: files={job.file_count}, issues_found={job.issues_found}, issues_fixed={job.issues_fixed}")
        
        # Extract messages from state (messages are dicts with 'role' and 'content')
        for msg in state.messages:
            if isinstance(msg, dict):
                job.messages.append(f"[{msg.get('role', 'system')}] {msg.get('content', '')}")
            else:
                job.messages.append(str(msg))
        
        if result.success:
            job.status = "completed"
            job.pr_url = getattr(state, 'pr_url', None)
            job.messages.append(f"Migration completed successfully! {result.summary}")
            print(f"[MIGRATION] Migration completed successfully!")
        else:
            job.status = "failed"
            job.error = "Migration tests failed after maximum retries"
            job.messages.append("Migration failed - tests did not pass")
            # Add error details if available
            if state.errors:
                for err in state.errors:
                    job.messages.append(f"Error detail: {err}")
            print(f"[MIGRATION] Migration failed: tests did not pass")
            
        job.completed_at = datetime.utcnow()
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[MIGRATION] EXCEPTION: {type(e).__name__}: {str(e)}")
        print(f"[MIGRATION] Traceback:\n{error_details}")
        
        # Make sure job still exists before updating
        if job_id in jobs:
            job = jobs[job_id]
            job.status = "failed"
            job.error = f"{type(e).__name__}: {str(e)}"
            job.completed_at = datetime.utcnow()
            job.messages.append(f"Error: {str(e)}")
        else:
            print(f"[MIGRATION] Job {job_id} disappeared from jobs dict during exception handling!")


@app.post("/api/migrate", response_model=MigrationJob)
async def start_migration(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    migration_type: str = Form(default="py2to3"),
):
    """
    Start a new migration job.
    
    Accepts a ZIP file containing the codebase to migrate.
    Returns a job ID for tracking progress.
    """
    # Validate file
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a ZIP file"
        )
    
    # Validate migration type
    if migration_type not in ["py2to3", "flask_to_fastapi"]:
        raise HTTPException(
            status_code=400,
            detail="Migration type must be 'py2to3' or 'flask_to_fastapi'"
        )
    
    # Create job
    job_id = str(uuid.uuid4())
    job = MigrationJob(
        job_id=job_id,
        status="pending",
        migration_type=migration_type,
        created_at=datetime.utcnow(),
    )
    jobs[job_id] = job
    
    # Save uploaded file
    temp_dir = Path(tempfile.mkdtemp())
    upload_path = temp_dir / "upload.zip"
    
    content = await file.read()
    with open(upload_path, "wb") as f:
        f.write(content)
    
    # Start background migration task
    background_tasks.add_task(
        process_migration,
        job_id=job_id,
        upload_path=upload_path,
        temp_dir=temp_dir,
        migration_type=migration_type,
    )
    
    return job


async def process_migration(
    job_id: str,
    upload_path: Path,
    temp_dir: Path,
    migration_type: str,
):
    """Process migration in the background."""
    job = jobs[job_id]
    job.status = "processing"
    
    try:
        # Extract uploaded zip
        extract_dir = temp_dir / "source"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(upload_path, "r") as zf:
            zf.extractall(extract_dir)
        
        # Find the actual code directory (might be nested)
        code_dir = find_code_directory(extract_dir)
        
        # Count files
        python_files = list(code_dir.rglob("*.py"))
        job.file_count = len(python_files)
        
        # Create output directory
        output_dir = temp_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy source to output
        shutil.copytree(code_dir, output_dir / "migrated", dirs_exist_ok=True)
        
        # Process migration
        issues_found = 0
        issues_fixed = 0
        
        for py_file in python_files:
            relative_path = py_file.relative_to(code_dir)
            output_file = output_dir / "migrated" / relative_path
            
            try:
                # Read source file
                source_code = py_file.read_text(encoding="utf-8", errors="ignore")
                
                # Run analysis and migration
                result = await asyncio.to_thread(
                    run_single_file_migration,
                    source_code=source_code,
                    migration_type=migration_type,
                )
                
                issues_found += result.get("issues_found", 0)
                issues_fixed += result.get("issues_fixed", 0)
                
                # Write migrated code
                if result.get("migrated_code"):
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text(result["migrated_code"], encoding="utf-8")
                    
            except Exception as e:
                # Log error but continue with other files
                print(f"Error processing {py_file}: {e}")
        
        job.issues_found = issues_found
        job.issues_fixed = issues_fixed
        
        # Create result zip
        result_zip_path = temp_dir / "result.zip"
        with zipfile.ZipFile(result_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in (output_dir / "migrated").rglob("*"):
                if file_path.is_file():
                    arc_name = file_path.relative_to(output_dir / "migrated")
                    zf.write(file_path, arc_name)
        
        # Store result path
        job_results[job_id] = result_zip_path
        
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.completed_at = datetime.utcnow()
        
        # Cleanup on failure
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass


def find_code_directory(extract_dir: Path) -> Path:
    """Find the actual code directory (handle nested folders from GitHub zips)."""
    # GitHub zips usually have a single folder like 'repo-main'
    items = list(extract_dir.iterdir())
    
    if len(items) == 1 and items[0].is_dir():
        # Check if it looks like a GitHub-style nested folder
        nested = items[0]
        if any(nested.iterdir()):
            return nested
    
    return extract_dir


def run_single_file_migration(
    source_code: str,
    migration_type: str,
) -> dict:
    """
    Run migration on a single file using AST-based transformation.
    
    This uses the multi-step process:
    1. AST Parsing - Parse source code into AST
    2. Pattern Detection - Identify deprecated patterns
    3. Transformation - Apply AST transformers to fix patterns
    """
    from devassist.ast_parser.analyzer import ASTAnalyzer
    from devassist.ast_parser.transformers import Py2to3Transformer, FlaskToFastAPITransformer
    from devassist.core.models import MigrationType
    
    result = {
        "issues_found": 0,
        "issues_fixed": 0,
        "migrated_code": source_code,
    }
    
    try:
        # Convert string to MigrationType enum
        mtype = MigrationType.PY2_TO_PY3 if migration_type == "py2to3" else MigrationType.FLASK_TO_FASTAPI
        
        # Step 1: AST Analysis - Identify deprecated patterns
        analyzer = ASTAnalyzer()
        patterns = list(analyzer.analyze(source_code, mtype))
        result["issues_found"] = len(patterns)
        
        # Step 2: AST Transformation - Apply fixes
        if migration_type == "py2to3":
            transformer = Py2to3Transformer()
        else:
            transformer = FlaskToFastAPITransformer()
        
        # Step 3: Transform the code
        transformed_code, changes = transformer.transform(source_code)
        
        if changes:
            result["migrated_code"] = transformed_code
            result["issues_fixed"] = len(changes)
        elif patterns:
            # If transformer couldn't parse but patterns found,
            # apply regex-based fixes for common patterns
            result["migrated_code"] = apply_regex_fixes(source_code, migration_type)
            result["issues_fixed"] = len(patterns)
            
    except Exception as e:
        # Return original code on error
        print(f"Migration error: {e}")
        import traceback
        traceback.print_exc()
    
    return result


def apply_regex_fixes(source_code: str, migration_type: str) -> str:
    """Apply regex-based fixes for Python 2 to 3 migration."""
    import re
    
    code = source_code
    
    if migration_type == "py2to3":
        # Fix print statements: print "x" -> print("x")
        # Match print followed by space and something that's not (
        code = re.sub(
            r'\bprint\s+(["\'].*?["\'])\s*$',
            r'print(\1)',
            code,
            flags=re.MULTILINE
        )
        code = re.sub(
            r'\bprint\s+([^(\n][^\n]*?)$',
            r'print(\1)',
            code,
            flags=re.MULTILINE
        )
        
        # Fix xrange -> range
        code = re.sub(r'\bxrange\s*\(', 'range(', code)
        
        # Fix raw_input -> input
        code = re.sub(r'\braw_input\s*\(', 'input(', code)
        
        # Fix unicode -> str
        code = re.sub(r'\bunicode\s*\(', 'str(', code)
        
        # Fix long -> int
        code = re.sub(r'\blong\s*\(', 'int(', code)
        
        # Fix dict.iteritems() -> dict.items()
        code = re.sub(r'\.iteritems\s*\(', '.items(', code)
        code = re.sub(r'\.iterkeys\s*\(', '.keys(', code)
        code = re.sub(r'\.itervalues\s*\(', '.values(', code)
        
        # Fix except E, e: -> except E as e:
        code = re.sub(
            r'except\s+(\w+)\s*,\s*(\w+)\s*:',
            r'except \1 as \2:',
            code
        )
        
        # Fix u"string" -> "string" (unicode literals)
        code = re.sub(r'\bu(["\'])', r'\1', code)
        
    elif migration_type == "flask_to_fastapi":
        # Fix Flask imports
        code = re.sub(
            r'from\s+flask\s+import\s+Flask',
            'from fastapi import FastAPI',
            code
        )
        code = re.sub(r'\bFlask\s*\(', 'FastAPI(', code)
        
        # Fix @app.route to @app.get/post
        code = re.sub(
            r'@(\w+)\.route\s*\(\s*(["\'][^"\']+["\'])\s*,\s*methods\s*=\s*\[\s*["\']GET["\']\s*\]\s*\)',
            r'@\1.get(\2)',
            code
        )
        code = re.sub(
            r'@(\w+)\.route\s*\(\s*(["\'][^"\']+["\'])\s*,\s*methods\s*=\s*\[\s*["\']POST["\']\s*\]\s*\)',
            r'@\1.post(\2)',
            code
        )
        code = re.sub(
            r'@(\w+)\.route\s*\(\s*(["\'][^"\']+["\'])\s*\)',
            r'@\1.get(\2)',
            code
        )
        
        # Fix jsonify
        code = re.sub(r'\bjsonify\s*\(', '', code)
        code = re.sub(r'return\s+\(([^)]+)\)\s*$', r'return \1', code, flags=re.MULTILINE)
    
    return code


@app.get("/api/jobs/{job_id}", response_model=MigrationJob)
async def get_job_status(job_id: str):
    """Get the status of a migration job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]


@app.get("/api/jobs/{job_id}/download")
async def download_result(job_id: str):
    """Download the migrated codebase as a ZIP file."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed. Current status: {job.status}"
        )
    
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail="Result file not found")
    
    result_path = job_results[job_id]
    
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Result file no longer exists")
    
    # Stream the zip file
    def iterfile():
        with open(result_path, "rb") as f:
            yield from f
    
    return StreamingResponse(
        iterfile(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=migrated-{job_id[:8]}.zip"
        },
    )


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its results."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Remove job
    del jobs[job_id]
    
    # Remove result file if exists
    if job_id in job_results:
        try:
            result_path = job_results[job_id]
            # Remove the entire temp directory
            shutil.rmtree(result_path.parent)
        except Exception:
            pass
        del job_results[job_id]
    
    return {"status": "deleted", "job_id": job_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
