# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JobSpy is a Python job scraping library that aggregates job postings from multiple job boards (LinkedIn, Indeed, Glassdoor, Google, ZipRecruiter, Bayt, Naukri, BDJobs, Wellfound) into a single pandas DataFrame. The library uses concurrent scraping with ThreadPoolExecutor for performance.

## Development Commands

### Package Management
- `poetry install` - Install dependencies
- `poetry add <package>` - Add new dependency
- `poetry build` - Build the package
- `poetry publish` - Publish to PyPI

### Code Quality
- `black .` - Format code (line length: 88)
- `pre-commit run --all-files` - Run pre-commit hooks

### Testing
- Test files are located in the root directory (e.g., `test_*.py`)
- No formal test framework configured - tests are standalone Python scripts
- Run individual tests with: `python test_<name>.py`

### API Server
- `python run_api.py` - Start the FastAPI server (default: localhost:8000)
- `python run_api.py --host 0.0.0.0 --port 8000 --reload` - Development mode with auto-reload
- API implementation located in `api/` directory

## API Documentation

### Base URL
- Local development: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs` (Swagger UI)
- Alternative docs: `http://localhost:8000/redoc`

### Endpoints

#### GET `/health`
Health check endpoint
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.1.82",
  "uptime_seconds": 3600.0
}
```

#### GET `/api/jobs/sites`
Get supported job board sites
```json
{
  "success": true,
  "total_sites": 8,
  "sites": {
    "linkedin": {
      "name": "LinkedIn",
      "description": "Professional networking platform with job listings",
      "supports_description_fetch": true
    }
  }
}
```

#### POST `/api/jobs/search`
Search for jobs (synchronous)

**Request:**
```json
{
  "search_term": "software engineer",
  "location": "San Francisco, CA",
  "sites": ["linkedin", "indeed"],
  "results_wanted": 50,
  "hours_old": 168,
  "country_indeed": "USA",
  "linkedin_fetch_description": true,
  "description_format": "markdown",
  "verbose": 1,
  "use_proxies": true,
  "proxies": ["user:pass@host:port"],
  "ca_cert": "/path/to/cert.pem",
  "callback_url": "https://webhook.site/unique-id"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully found 45 jobs",
  "total_jobs": 45,
  "jobs": [
    {
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "job_type": "fulltime",
      "date_posted": "2024-01-01T10:00:00Z",
      "job_url": "https://linkedin.com/jobs/view/123",
      "job_url_direct": "https://company.com/careers/123",
      "description": "**Job Description**\n\nWe are looking for...",
      "min_amount": 120000,
      "max_amount": 180000,
      "currency": "USD",
      "interval": "yearly",
      "site": "linkedin",
      "emails": ["hr@company.com"],
      "is_remote": false
    }
  ],
  "stats": {
    "total_jobs": 45,
    "jobs_by_site": {"linkedin": 25, "indeed": 20},
    "job_types": {"fulltime": 40, "parttime": 5},
    "search_duration_seconds": 12.5,
    "proxies_used": 3,
    "proxy_enabled": true
  },
  "search_parameters": { /* original request */ }
}
```

#### POST `/api/jobs/search/async`
Start asynchronous job search

**Request:** Same as synchronous search

**Response:**
```json
{
  "job_id": "uuid-123-456",
  "status": "pending",
  "message": "Job started. Use GET /api/jobs/status/{job_id} to check progress.",
  "poll_url": "/api/jobs/status/uuid-123-456"
}
```

#### GET `/api/jobs/status/{job_id}`
Check async job status

**Response (pending):**
```json
{
  "status": "pending",
  "created_at": 1704110400.0,
  "request": { /* original request */ }
}
```

**Response (completed):**
```json
{
  "status": "completed",
  "created_at": 1704110400.0,
  "started_at": 1704110410.0,
  "completed_at": 1704110430.0,
  "result": { /* JobSearchResponse */ },
  "callback_sent": true,
  "callback_status": 200
}
```

**Response (failed):**
```json
{
  "status": "failed",
  "created_at": 1704110400.0,
  "started_at": 1704110410.0,
  "failed_at": 1704110415.0,
  "error": "Connection timeout",
  "callback_sent": true,
  "callback_error": "Connection refused"
}
```

#### POST `/api/jobs/search/csv`
Search and download results as CSV

**Request:** Same as synchronous search + optional `filename` parameter

**Response:** CSV file download with headers:
```
Content-Type: text/csv
Content-Disposition: attachment; filename=job_search_results_20240101_120000.csv
```

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search_term` | string | ✓ | - | Job title or keywords |
| `location` | string | ✓ | - | Location to search |
| `sites` | array | ❌ | ["linkedin"] | Job boards to search |
| `results_wanted` | integer | ❌ | 30 | Number of results (1-500) |
| `hours_old` | integer | ❌ | 168 | Job age in hours |
| `country_indeed` | string | ❌ | null | Country for Indeed/Glassdoor |
| `linkedin_fetch_description` | boolean | ❌ | true | Fetch full LinkedIn descriptions |
| `description_format` | string | ❌ | "markdown" | Format: markdown/html/plain |
| `verbose` | integer | ❌ | 1 | Verbosity level (0-2) |
| `use_proxies` | boolean | ❌ | true | Enable automatic proxy rotation |
| `proxies` | array | ❌ | null | Custom proxy list |
| `ca_cert` | string | ❌ | null | CA certificate path |
| `callback_url` | string | ❌ | null | Webhook URL for async jobs |

### Error Responses

**Validation Error (400):**
```json
{
  "success": false,
  "error": "400",
  "message": "Invalid site: facebook. Valid sites: {linkedin, indeed, ...}"
}
```

**Server Error (500):**
```json
{
  "success": false,
  "error": "Internal Server Error",
  "message": "Job search failed: Connection timeout"
}
```

### Webhook Callbacks (Async Jobs)

When using async job search (`/api/jobs/search/async`), you can provide a `callback_url` to receive notifications when jobs complete.

#### Callback Setup
Include `callback_url` in your async job request:
```json
{
  "search_term": "software engineer",
  "location": "San Francisco, CA",
  "sites": ["linkedin"],
  "callback_url": "https://your-server.com/webhook/jobspy"
}
```

#### Callback Request (Success)
JobSpy will POST to your callback URL when the job completes:
```http
POST https://your-server.com/webhook/jobspy
Content-Type: application/json
User-Agent: JobSpy-API-Callback/1.0

{
  "job_id": "uuid-123-456",
  "status": "completed",
  "timestamp": "2024-01-01T12:30:00Z",
  "callback_sent_at": 1704110400.0,
  "result": {
    "success": true,
    "message": "Successfully found 25 jobs",
    "total_jobs": 25,
    "jobs": [ /* job listings */ ],
    "stats": { /* search statistics */ },
    "search_parameters": { /* original request */ }
  }
}
```

#### Callback Request (Failure)
```http
POST https://your-server.com/webhook/jobspy
Content-Type: application/json
User-Agent: JobSpy-API-Callback/1.0

{
  "job_id": "uuid-123-456",
  "status": "failed",
  "timestamp": "2024-01-01T12:15:00Z",
  "callback_sent_at": 1704110400.0,
  "error": "Connection timeout after 30 seconds"
}
```

#### Callback Requirements
- Your webhook endpoint must accept POST requests
- Respond with HTTP 200-299 status codes for success
- JobSpy uses 30-second timeout for callback requests
- Failed callbacks are logged but don't retry automatically
- Callback status is tracked in job status endpoint

#### Security Considerations
- Use HTTPS URLs for sensitive data
- Implement webhook signature verification if needed
- Consider rate limiting your webhook endpoint
- Validate incoming payloads before processing

### Running the Library
```python
from jobspy import scrape_jobs
jobs = scrape_jobs(
    site_name=["indeed", "linkedin"],
    search_term="software engineer",
    location="San Francisco, CA",
    results_wanted=20
)
```

## Architecture

### Core Structure
- `jobspy/__init__.py` - Main entry point with `scrape_jobs()` function and SCRAPER_MAPPING
- `jobspy/model.py` - Pydantic models and enums (JobType, Site, Country, ScraperInput, etc.)
- `jobspy/util.py` - Shared utilities (logging, proxy rotation, salary extraction, RotatingProxySession)
- `jobspy/exception.py` - Custom exceptions

### Scraper Modules
Each job board has its own module following the pattern:
- `jobspy/{site}/` directory structure:
  - `__init__.py` - Main scraper class implementation inheriting from Scraper base class
  - `constant.py` - Site-specific constants and configurations
  - `util.py` - Site-specific utility functions

Supported sites: `linkedin/`, `indeed/`, `glassdoor/`, `google/`, `ziprecruiter/`, `bayt/`, `naukri/`, `bdjobs/`, `wellfound/`

### Key Components
- **Concurrent Scraping**: Uses ThreadPoolExecutor to scrape multiple sites simultaneously
- **Proxy Support**: RotatingProxySession class for proxy rotation and rate limiting avoidance
- **Data Models**: Pydantic models for type safety and validation (JobPost, Location, Compensation)
- **Salary Extraction**: Regex-based salary parsing from job descriptions when direct data unavailable
- **Multi-language Support**: JobType enum supports job types in multiple languages
- **Abstract Base Class**: Scraper ABC defines common interface for all site scrapers

### Data Flow
1. `scrape_jobs()` function validates inputs and creates ScraperInput
2. ThreadPoolExecutor spawns workers for each requested site using SCRAPER_MAPPING
3. Each scraper class inherits from Scraper ABC and implements site-specific logic
4. Results are aggregated into a single pandas DataFrame with standardized columns
5. Salary information is extracted from descriptions when not directly available (US only)
6. Final DataFrame is sorted by site and date_posted

### Adding New Scrapers
When adding a new job board:
1. Create `jobspy/{site}/` directory with `__init__.py`, `constant.py`, `util.py`
2. Implement scraper class inheriting from Scraper abstract base class
3. Add Site enum value in `model.py`
4. Update SCRAPER_MAPPING in `__init__.py`
5. Update `__all__` export list

### Configuration
- Python 3.10+ required
- Dependencies managed with Poetry
- Black code formatting with 88 character line length
- Pre-commit hooks for code quality (black only)
- Browser automation dependencies: Selenium, Playwright, undetected-chromedriver