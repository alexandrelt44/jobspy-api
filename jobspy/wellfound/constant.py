"""
Constants and configuration for Wellfound scraper
"""

# Headers to mimic a real browser and bypass basic bot detection
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}

# Location mappings for Wellfound URLs
LOCATION_MAPPINGS = {
    # Portugal
    "Porto, Portugal": "porto",
    "Lisbon, Portugal": "lisbon", 
    "Portugal": "portugal",
    "Lisboa, Portugal": "lisbon",
    
    # Spain
    "Madrid, Spain": "madrid",
    "Barcelona, Spain": "barcelona",
    "Spain": "spain",
    
    # Europe regions
    "Europe": "europe",
    "Western Europe": "europe",
    "European Union": "europe",
    
    # Remote work
    "Remote": "remote",
    "Worldwide": "remote",
    "Global": "remote",
    
    # Major European cities
    "Berlin, Germany": "berlin",
    "Paris, France": "paris", 
    "Amsterdam, Netherlands": "amsterdam",
    "London, UK": "london",
    "Milan, Italy": "milan",
    "Stockholm, Sweden": "stockholm",
    "Copenhagen, Denmark": "copenhagen",
    "Zurich, Switzerland": "zurich",
}

# Job title normalization for URL building
JOB_TITLE_MAPPINGS = {
    "Product Owner": "product-manager",
    "Product Manager": "product-manager", 
    "Senior Product Manager": "product-manager",
    "Product Management": "product-manager",
    
    "Software Engineer": "software-engineer",
    "Software Developer": "software-engineer",
    "Full Stack Developer": "software-engineer",
    "Backend Developer": "software-engineer",
    "Frontend Developer": "frontend-engineer",
    "Front End Developer": "frontend-engineer",
    
    "Data Scientist": "data-scientist",
    "Data Engineer": "data-engineer",
    "Machine Learning Engineer": "machine-learning-engineer",
    "ML Engineer": "machine-learning-engineer",
    
    "DevOps Engineer": "devops-engineer",
    "Site Reliability Engineer": "devops-engineer",
    "Infrastructure Engineer": "devops-engineer",
    
    "UX Designer": "designer",
    "UI Designer": "designer",
    "Product Designer": "designer",
    "Graphic Designer": "designer",
    
    "Marketing Manager": "marketing",
    "Digital Marketing": "marketing",
    "Growth Manager": "marketing",
    
    "Sales Manager": "sales",
    "Account Manager": "sales",
    "Business Development": "sales",
}

# Common job categories on Wellfound
WELLFOUND_CATEGORIES = [
    "software-engineer",
    "product-manager", 
    "designer",
    "data-scientist",
    "marketing",
    "sales",
    "devops-engineer",
    "frontend-engineer",
    "backend-engineer",
    "mobile-engineer",
    "security-engineer",
    "data-engineer",
    "machine-learning-engineer",
    "growth",
    "operations",
    "finance",
    "legal",
    "hr",
    "customer-success"
]

# Base URLs for different search types
BASE_URLS = {
    "role": "/role/l/{job_title}/{location}",
    "location": "/jobs/{location}",
    "remote": "/remote/{job_title}-jobs"
}

# Request configuration
REQUEST_CONFIG = {
    "timeout": 15,
    "max_retries": 3,
    "retry_delay": 2,
    "delay_between_requests": 1,
}

# scrape.do API configuration  
SCRAPE_DO_TOKEN = "1badeb624be04cdfb4bc798a2c53e9c93728941d41e"