# JobSpy API

A RESTful API wrapper for the JobSpy job scraping library, built with FastAPI.

## Quick Start

### 1. Install Dependencies

```bash
# Using pip
pip install fastapi uvicorn

# Or using poetry (if available)
poetry install
```

### 2. Start the API Server

```bash
# Using the run script (recommended)
python run_api.py --reload

# Or directly with uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access the API

- **API Base URL**: http://localhost:8000
- **Interactive Documentation**: http://localhost:8000/docs
- **Alternative Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### POST `/api/jobs/search`

Search for jobs across multiple job boards.

**Request Body:**
```json
{
  "search_term": "Product Owner",
  "location": "Porto, Portugal",
  "sites": ["indeed", "linkedin", "google"],
  "results_wanted": 30,
  "hours_old": 168,
  "country_indeed": "Portugal",
  "linkedin_fetch_description": true,
  "verbose": 1
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully found 25 jobs",
  "total_jobs": 25,
  "jobs": [
    {
      "title": "Product Owner",
      "company": "Tech Company",
      "location": "Porto, Portugal",
      "job_type": "Full-time",
      "date_posted": "2024-01-15T10:30:00Z",
      "job_url": "https://...",
      "description": "Job description...",
      "min_amount": 45000,
      "max_amount": 65000,
      "currency": "EUR",
      "interval": "yearly",
      "site": "linkedin"
    }
  ],
  "stats": {
    "total_jobs": 25,
    "jobs_by_site": {"linkedin": 15, "indeed": 10},
    "job_types": {"Full-time": 20, "Contract": 5},
    "search_duration_seconds": 12.34
  },
  "search_parameters": { /* original request */ }
}
```

### POST `/api/jobs/search/csv`

Search for jobs and download results as CSV file.

Same request body as above, returns a downloadable CSV file.

### GET `/api/jobs/sites`

Get information about supported job sites.

**Response:**
```json
{
  "success": true,
  "total_sites": 8,
  "sites": {
    "indeed": {
      "name": "Indeed",
      "description": "Global job board with positions worldwide",
      "supports_country_filter": true
    },
    "linkedin": {
      "name": "LinkedIn",
      "description": "Professional networking platform with job listings",
      "supports_description_fetch": true
    }
  }
}
```

### GET `/health`

Health check endpoint.

### GET `/`

Root endpoint with API information.

## Usage Examples

### Using cURL

```bash
# Search for jobs
curl -X POST "http://localhost:8000/api/jobs/search" \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "Python Developer",
    "location": "Lisboa, Portugal",
    "sites": ["linkedin", "indeed"],
    "results_wanted": 20
  }'

# Download CSV
curl -X POST "http://localhost:8000/api/jobs/search/csv" \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "Data Scientist",
    "location": "Porto, Portugal",
    "results_wanted": 50
  }' \
  --output jobs.csv
```

### Using Python

```python
import requests

# Search for jobs
response = requests.post("http://localhost:8000/api/jobs/search", json={
    "search_term": "Frontend Developer",
    "location": "Remote",
    "sites": ["linkedin", "indeed", "google"],
    "results_wanted": 30
})

if response.status_code == 200:
    data = response.json()
    print(f"Found {data['total_jobs']} jobs")
    for job in data['jobs'][:5]:  # Show first 5
        print(f"- {job['title']} at {job['company']}")
else:
    print(f"Error: {response.status_code}")
```

### Using JavaScript/Fetch

```javascript
// Search for jobs
const response = await fetch('http://localhost:8000/api/jobs/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    search_term: 'DevOps Engineer',
    location: 'Braga, Portugal',
    sites: ['indeed', 'linkedin'],
    results_wanted: 25
  })
});

const data = await response.json();
console.log(`Found ${data.total_jobs} jobs`);
```

## Parameters

### Required Parameters
- `search_term`: Job title or keywords to search for
- `location`: Location to search jobs in

### Optional Parameters
- `sites`: Array of job sites to search (default: ["indeed", "linkedin", "google"])
- `results_wanted`: Number of results (1-500, default: 30)
- `hours_old`: Only jobs posted within this many hours (default: 168 = 7 days)
- `country_indeed`: Country for Indeed searches
- `linkedin_fetch_description`: Fetch full descriptions from LinkedIn (default: true)
- `verbose`: Logging level (0-2, default: 1)

### Supported Job Sites
- `indeed` - Indeed.com
- `linkedin` - LinkedIn Jobs
- `glassdoor` - Glassdoor
- `google` - Google Jobs
- `ziprecruiter` - ZipRecruiter
- `bayt` - Bayt.com (Middle East)
- `naukri` - Naukri.com (India)
- `bdjobs` - BDJobs (Bangladesh)

## Testing

Run the test suite:

```bash
# Start the API server first
python run_api.py --reload

# In another terminal, run tests
python test_api.py
```

## Error Handling

The API returns structured error responses:

```json
{
  "success": false,
  "error": "Bad Request",
  "message": "search_term cannot be empty"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (validation error)
- `500` - Internal Server Error

## Rate Limiting

Be mindful of rate limits from job sites. The API inherits the same limitations as the underlying JobSpy library. Consider:
- Using fewer sites for faster responses
- Reducing `results_wanted` for quicker searches
- Adding delays between requests

## Converting from CLI Script

Your original script `search_product_owner_porto.py` can be converted to API calls:

**Original script:**
```python
jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "google"],
    search_term="Product Owner",
    location="Porto, Portugal",
    results_wanted=30
)
```

**API equivalent:**
```bash
curl -X POST "http://localhost:8000/api/jobs/search" \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "Product Owner",
    "location": "Porto, Portugal",
    "sites": ["indeed", "linkedin", "google"],
    "results_wanted": 30
  }'
```