"""
FastAPI application for JobSpy API
"""

import time
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
from jobspy import scrape_jobs

from .models import (
    JobSearchRequest, 
    JobSearchResponse, 
    ErrorResponse, 
    HealthResponse
)
from .services import JobSearchService
from .utils import get_version, cleanup_csv_file

# Create FastAPI app
app = FastAPI(
    title="JobSpy API",
    description="RESTful API for scraping job postings from multiple job boards",
    version=get_version(),
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track all incoming requests for monitoring"""
    client_ip = request.client.host if request.client else "unknown"
    endpoint = f"{request.method} {request.url.path}"
    
    # Update stats
    request_stats["total_requests"] += 1
    request_stats["endpoints"][endpoint] = request_stats["endpoints"].get(endpoint, 0) + 1
    request_stats["ips"][client_ip] = request_stats["ips"].get(client_ip, 0) + 1
    request_stats["last_request"] = {
        "timestamp": datetime.now().isoformat(),
        "ip": client_ip,
        "endpoint": endpoint,
        "user_agent": request.headers.get("user-agent", "unknown")
    }
    
    response = await call_next(request)
    return response

# Track app startup time for health endpoint
app_start_time = time.time()

# Request tracking
request_stats = {
    "total_requests": 0,
    "endpoints": {},
    "ips": {},
    "last_request": None
}


async def send_callback_notification(job_id: str, callback_url: str, payload: dict):
    """Send POST notification to callback URL when job completes"""
    import httpx
    import asyncio
    
    try:
        # Add timestamp and metadata
        payload["timestamp"] = datetime.now().isoformat()
        payload["callback_sent_at"] = time.time()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                callback_url,
                json=payload,
                headers={"Content-Type": "application/json", "User-Agent": "JobSpy-API-Callback/1.0"}
            )
            
        # Log callback result
        app.state.jobs[job_id]["callback_status"] = response.status_code
        app.state.jobs[job_id]["callback_sent"] = True
        
        if response.status_code not in range(200, 300):
            print(f"Callback failed for job {job_id}: HTTP {response.status_code}")
        else:
            print(f"Callback successful for job {job_id}")
            
    except Exception as e:
        print(f"Callback error for job {job_id}: {str(e)}")
        app.state.jobs[job_id]["callback_error"] = str(e)
        app.state.jobs[job_id]["callback_sent"] = False


async def process_job_async(job_id: str, request: JobSearchRequest):
    """Background task to process job search"""
    try:
        app.state.jobs[job_id]["status"] = "running"
        app.state.jobs[job_id]["started_at"] = time.time()
        
        # Execute job search in thread pool to avoid blocking event loop
        import asyncio
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            response = await asyncio.get_event_loop().run_in_executor(
                executor, JobSearchService.search_jobs, request
            )
        
        app.state.jobs[job_id]["status"] = "completed"
        app.state.jobs[job_id]["completed_at"] = time.time()

        # Serialize response to JSON-compatible format
        try:
            # Use model_dump for Pydantic v2 with JSON serialization
            serialized_result = response.model_dump(mode='json')
        except AttributeError:
            # Fallback for older Pydantic versions
            import json
            serialized_result = json.loads(response.json())

        app.state.jobs[job_id]["result"] = serialized_result

        # Send callback notification if URL provided
        if request.callback_url:
            await send_callback_notification(job_id, request.callback_url, {
                "job_id": job_id,
                "status": "completed",
                "result": serialized_result
            })
        
    except Exception as e:
        app.state.jobs[job_id]["status"] = "failed"
        app.state.jobs[job_id]["error"] = str(e)
        app.state.jobs[job_id]["failed_at"] = time.time()
        
        # Send callback notification for failed jobs too
        if request.callback_url:
            await send_callback_notification(job_id, request.callback_url, {
                "job_id": job_id,
                "status": "failed",
                "error": str(e)
            })


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to JobSpy API",
        "docs": "/docs",
        "health": "/health",
        "version": get_version()
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - app_start_time
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=get_version(),
        uptime_seconds=round(uptime, 2)
    )


@app.get("/stats")
async def get_request_stats():
    """Get API request statistics for monitoring"""
    uptime = time.time() - app_start_time
    
    return {
        "server": {
            "status": "running",
            "uptime_seconds": round(uptime, 2),
            "uptime_hours": round(uptime / 3600, 2),
            "started_at": datetime.fromtimestamp(app_start_time).isoformat()
        },
        "requests": {
            "total": request_stats["total_requests"],
            "rate_per_minute": round(request_stats["total_requests"] / (uptime / 60), 2) if uptime > 0 else 0,
            "endpoints": dict(sorted(request_stats["endpoints"].items(), key=lambda x: x[1], reverse=True)),
            "top_ips": dict(sorted(request_stats["ips"].items(), key=lambda x: x[1], reverse=True)[:10]),
            "last_request": request_stats["last_request"]
        },
        "jobs": {
            "active_jobs": len(getattr(app.state, 'jobs', {})),
            "job_statuses": {}
        }
    }


@app.post("/api/jobs/search", response_model=JobSearchResponse)
async def search_jobs(request: JobSearchRequest):
    """
    Search for jobs across multiple job boards
    
    This endpoint scrapes job postings from the specified job sites based on
    the search criteria provided in the request.
    """
    try:
        # Execute job search
        response = JobSearchService.search_jobs(request)
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@app.post("/api/jobs/search/async")
async def search_jobs_async(request: JobSearchRequest, background_tasks: BackgroundTasks):
    """
    Start an async job search and return job ID for polling
    
    Returns immediately with a job ID that can be used to check status and get results.
    """
    import uuid
    import time
    
    job_id = str(uuid.uuid4())
    
    # Store job status in memory (in production, use Redis/database)
    if not hasattr(app.state, 'jobs'):
        app.state.jobs = {}
    
    app.state.jobs[job_id] = {
        "status": "pending",
        "created_at": time.time(),
        "request": request.dict(),
        "callback_url": request.callback_url
    }
    
    # Start background task
    background_tasks.add_task(process_job_async, job_id, request)
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Job started. Use GET /api/jobs/status/{job_id} to check progress.",
        "poll_url": f"/api/jobs/status/{job_id}"
    }


@app.get("/api/jobs/status/{job_id}")
async def get_job_status(job_id: str):
    """Check the status of an async job"""
    if not hasattr(app.state, 'jobs') or job_id not in app.state.jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return app.state.jobs[job_id]


@app.post("/api/jobs/search/csv")
async def search_jobs_csv(
    request: JobSearchRequest, 
    background_tasks: BackgroundTasks,
    filename: Optional[str] = None
):
    """
    Search for jobs and return results as CSV file download
    
    This endpoint performs a job search and returns the results as a downloadable
    CSV file. The file is automatically cleaned up after download.
    """
    try:
        # Execute job search to get DataFrame
        jobs_df = scrape_jobs(
            site_name=request.sites,
            search_term=request.search_term,
            location=request.location,
            results_wanted=request.results_wanted,
            hours_old=request.hours_old,
            country_indeed=request.country_indeed,
            linkedin_fetch_description=request.linkedin_fetch_description,
            description_format=request.description_format,
            verbose=request.verbose
        )
        
        # Generate CSV file
        csv_filename = JobSearchService.export_to_csv(jobs_df, filename)
        
        # Schedule file cleanup after response
        background_tasks.add_task(cleanup_csv_file, csv_filename)
        
        return FileResponse(
            path=csv_filename,
            media_type='text/csv',
            filename=csv_filename,
            headers={"Content-Disposition": f"attachment; filename={csv_filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal Server Error", 
                "message": str(e)
            }
        )


@app.get("/api/jobs/sites")
async def get_supported_sites():
    """
    Get list of supported job sites
    
    Returns information about all job sites that can be scraped by the API.
    """
    sites = {
        "indeed": {
            "name": "Indeed",
            "description": "Global job board with positions worldwide",
            "supports_country_filter": True
        },
        "linkedin": {
            "name": "LinkedIn",
            "description": "Professional networking platform with job listings",
            "supports_description_fetch": True
        },
        "glassdoor": {
            "name": "Glassdoor", 
            "description": "Job listings with company reviews and salary information"
        },
        "google": {
            "name": "Google Jobs",
            "description": "Google's job search aggregator"
        },
        "ziprecruiter": {
            "name": "ZipRecruiter",
            "description": "US-focused job board"
        },
        "bayt": {
            "name": "Bayt",
            "description": "Middle East and North Africa job portal"
        },
        "naukri": {
            "name": "Naukri.com",
            "description": "India's leading job portal"
        },
        "bdjobs": {
            "name": "BDJobs",
            "description": "Bangladesh's premier job portal"
        },
        "wellfound": {
            "name": "Wellfound",
            "description": "Startup-focused job board (formerly AngelList Talent)"
        },
        "gupy": {
            "name": "Gupy",
            "description": "Brazilian job portal with opportunities from companies across Brazil",
            "supports_description_fetch": True
        }
    }
    
    return {
        "success": True,
        "total_sites": len(sites),
        "sites": sites
    }


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return Response(
        content=f'{{"success": false, "error": "{exc.status_code}", "message": "{exc.detail}"}}',
        status_code=exc.status_code,
        media_type="application/json"
    )


@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    """Handle internal server errors"""
    return Response(
        content='{"success": false, "error": "Internal Server Error", "message": "An unexpected error occurred"}',
        status_code=500,
        media_type="application/json"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )