"""
Pydantic models for JobSpy API request and response validation
"""

from datetime import datetime
from typing import List, Optional, Literal
import re
from pydantic import BaseModel, Field, validator


class JobSearchRequest(BaseModel):
    """Request model for job search endpoint"""
    
    search_term: str = Field(..., description="Job title or keywords to search for")
    location: str = Field(..., description="Location to search jobs in")
    sites: List[str] = Field(
        default=["linkedin"],
        description="List of job sites to search (indeed, linkedin, glassdoor, google, ziprecruiter, bayt, naukri, bdjobs, wellfound, gupy)"
    )
    results_wanted: int = Field(
        default=30, 
        ge=1, 
        le=500, 
        description="Number of job results to fetch (1-500)"
    )
    hours_old: int = Field(
        default=168, 
        ge=1, 
        description="Only jobs posted within this many hours ago"
    )
    country_indeed: Optional[str] = Field(
        default=None,
        description="Country for Indeed searches (e.g., 'Portugal', 'USA')"
    )
    linkedin_fetch_description: bool = Field(
        default=True,
        description="Whether to fetch full job descriptions from LinkedIn"
    )
    description_format: Literal["markdown", "html", "plain"] = Field(
        default="markdown",
        description="Format for job descriptions (markdown, html, plain)"
    )
    verbose: int = Field(
        default=1,
        ge=0,
        le=2,
        description="Verbosity level (0=quiet, 1=normal, 2=detailed)"
    )
    
    # Proxy configuration options
    use_proxies: bool = Field(
        default=True,
        description="Enable automatic proxy rotation using default proxy pool (recommended for LinkedIn)"
    )
    proxies: Optional[List[str]] = Field(
        default=None,
        description="Custom list of proxies in format 'user:pass@host:port' or 'host:port'"
    )
    ca_cert: Optional[str] = Field(
        default=None,
        description="Path to CA certificate file for proxy SSL verification"
    )
    
    # Callback configuration
    callback_url: Optional[str] = Field(
        default=None,
        description="URL to POST results when job completes (webhook callback)"
    )

    @validator('sites')
    def validate_sites(cls, v):
        valid_sites = {
            "indeed", "linkedin", "glassdoor", "google",
            "ziprecruiter", "bayt", "naukri", "bdjobs", "wellfound", "gupy"
        }
        for site in v:
            if site not in valid_sites:
                raise ValueError(f"Invalid site: {site}. Valid sites: {valid_sites}")
        return v

    @validator('proxies')
    def validate_proxies(cls, v):
        if v is not None:
            from .proxy_config import validate_proxy_format
            for proxy in v:
                if not validate_proxy_format(proxy):
                    raise ValueError(f"Invalid proxy format: {proxy}. Use formats like 'user:pass@host:port' or 'host:port'")
        return v


class JobListing(BaseModel):
    """Model for individual job listing"""
    
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    date_posted: Optional[datetime] = None
    job_url: Optional[str] = None
    job_url_direct: Optional[str] = None
    description: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: Optional[str] = None
    interval: Optional[str] = None
    site: Optional[str] = None
    emails: Optional[List[str]] = None
    is_remote: Optional[bool] = None


class JobSearchStats(BaseModel):
    """Statistics about the job search results"""
    
    total_jobs: int
    jobs_by_site: dict
    job_types: Optional[dict] = None
    search_duration_seconds: Optional[float] = None
    proxies_used: Optional[int] = None
    proxy_enabled: Optional[bool] = None


class JobSearchResponse(BaseModel):
    """Response model for job search endpoint"""
    
    success: bool = True
    message: str = "Jobs retrieved successfully"
    total_jobs: int
    jobs: List[JobListing]
    stats: JobSearchStats
    search_parameters: JobSearchRequest


class ErrorResponse(BaseModel):
    """Error response model"""
    
    success: bool = False
    error: str
    message: str
    details: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response model"""
    
    status: Literal["healthy"] = "healthy"
    timestamp: datetime
    version: str
    uptime_seconds: float


class LinkedInBulkDescriptionRequest(BaseModel):
    """Request model for bulk LinkedIn job description fetching"""
    
    job_urls: List[str] = Field(
        ...,
        description="List of LinkedIn job URLs to fetch descriptions for",
        min_items=1,
        max_items=50  # Reasonable limit to prevent abuse
    )
    description_format: Literal["markdown", "html", "plain"] = Field(
        default="markdown",
        description="Format for job descriptions (markdown, html, plain)"
    )
    verbose: int = Field(
        default=1,
        ge=0,
        le=2,
        description="Verbosity level (0=quiet, 1=normal, 2=detailed)"
    )
    
    # Proxy configuration options
    use_proxies: bool = Field(
        default=True,
        description="Enable automatic proxy rotation using default proxy pool (recommended for LinkedIn)"
    )
    proxies: Optional[List[str]] = Field(
        default=None,
        description="Custom list of proxies in format 'user:pass@host:port' or 'host:port'"
    )
    ca_cert: Optional[str] = Field(
        default=None,
        description="Path to CA certificate file for proxy SSL verification"
    )

    @validator('job_urls')
    def validate_linkedin_urls(cls, v):
        linkedin_pattern = r'https://(?:www\.)?linkedin\.com/jobs/view/\d+'
        for url in v:
            # Extract job ID from URL - support both full URLs and just IDs
            if url.isdigit():
                # Just a job ID, convert to full URL
                continue
            elif re.match(linkedin_pattern, url):
                # Full LinkedIn URL
                continue
            else:
                raise ValueError(f"Invalid LinkedIn job URL: {url}. URLs must be in format 'https://linkedin.com/jobs/view/JOBID' or just the job ID")
        return v

    @validator('proxies')
    def validate_proxies(cls, v):
        if v is not None:
            from .proxy_config import validate_proxy_format
            for proxy in v:
                if not validate_proxy_format(proxy):
                    raise ValueError(f"Invalid proxy format: {proxy}. Use formats like 'user:pass@host:port' or 'host:port'")
        return v


class LinkedInJobDescription(BaseModel):
    """Model for individual LinkedIn job description result"""
    
    job_url: str = Field(..., description="Original LinkedIn job URL")
    job_id: str = Field(..., description="Extracted LinkedIn job ID")
    success: bool = Field(..., description="Whether description fetching was successful")
    title: Optional[str] = None
    company_name: Optional[str] = None
    company_url: Optional[str] = None
    company_logo: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    job_level: Optional[str] = None
    job_function: Optional[str] = None
    company_industry: Optional[str] = None
    description: Optional[str] = None
    job_url_direct: Optional[str] = None
    error: Optional[str] = Field(None, description="Error message if fetching failed")


class LinkedInBulkDescriptionResponse(BaseModel):
    """Response model for bulk LinkedIn description fetching"""
    
    success: bool = True
    message: str = "Job descriptions retrieved"
    total_requested: int
    total_successful: int
    total_failed: int
    results: List[LinkedInJobDescription]
    request_parameters: LinkedInBulkDescriptionRequest
