"""
Business logic services for JobSpy API
"""

import time
import re
from typing import Dict, Any, List
import pandas as pd
from jobspy import scrape_jobs
from .models import (
    JobSearchRequest, JobListing, JobSearchStats, JobSearchResponse,
    LinkedInBulkDescriptionRequest, LinkedInJobDescription, LinkedInBulkDescriptionResponse
)


class JobSearchService:
    """Service class for handling job search operations"""
    
    @staticmethod
    def sanitize_markdown_description(description: str) -> str:
        """
        Sanitize broken markdown descriptions to fix formatting issues
        
        This function fixes common issues with LinkedIn markdown output:
        - Bold text split across lines
        - Missing spaces around bold text
        - Excessive newlines
        - Malformed headers
        
        Args:
            description: Raw markdown description
            
        Returns:
            Cleaned markdown description
        """
        if not description or not isinstance(description, str):
            return description
            
        # Fix bold text split across lines - merge lines that end/start with bold markers
        # Pattern: "**text**\nmore text" -> "**text** more text" 
        description = re.sub(r'\*\*([^*\n]*)\*\*\n([^\n*]+)', r'**\1** \2', description)
        description = re.sub(r'([^\n*]+)\n\*\*([^*\n]*)\*\*', r'\1 **\2**', description)
        
        # Fix broken bold formatting where line breaks appear inside text flow
        # Pattern: "word\n **text**" -> "word **text**"
        description = re.sub(r'(\w+)\n\s+\*\*([^*]+)\*\*', r'\1 **\2**', description)
        
        # Fix pattern: "**text**\nis" -> "**text** is"
        description = re.sub(r'\*\*([^*]+)\*\*\n([a-z])', r'**\1** \2', description)
        
        # Fix bold text immediately followed by text (missing space)
        # Pattern: "**text**word" -> "**text** word"
        description = re.sub(r'\*\*([^*]+)\*\*([A-Z][a-z])', r'**\1** \2', description)
        
        # Fix multiple consecutive bold elements (missing space/newline)
        # Pattern: "**text1****text2**" -> "**text1**\n\n**text2**"
        description = re.sub(r'\*\*([^*]+)\*\*\*\*([^*]+)\*\*', r'**\1**\n\n**\2**', description)
        
        # Fix extra spaces inside bold markers (but preserve spaces outside)
        # Only fix spaces that are immediately inside the ** markers
        description = re.sub(r'(^|\s)\*\* ([^*]+)\*\*', r'\1**\2**', description)
        description = re.sub(r'\*\*([^*]+) \*\*(\s|$)', r'**\1**\2', description)
        
        # Fix consecutive bold with excessive spacing
        # Pattern: "**text.**   **text**" -> "**text.**\n\n**text**"
        description = re.sub(r'\*\*([^*]+)\*\*\s{2,}\*\*([^*]+)\*\*', r'**\1**\n\n**\2**', description)
        
        # Fix multiple consecutive newlines (more than 2)
        description = re.sub(r'\n{3,}', '\n\n', description)
        
        # Remove leading/trailing whitespace
        description = description.strip()
        
        return description

    @staticmethod
    def search_jobs(request: JobSearchRequest) -> JobSearchResponse:
        """
        Execute job search based on request parameters
        
        Args:
            request: JobSearchRequest with search parameters
            
        Returns:
            JobSearchResponse with results and metadata
        """
        start_time = time.time()
        
        try:
            # Validate and clean input parameters
            search_term = request.search_term.strip() if request.search_term else None
            location = request.location.strip() if request.location else None
            
            if not search_term or not location:
                raise ValueError("search_term and location cannot be empty")
            
            # Determine which proxies to use
            proxies_to_use = None
            if request.use_proxies:
                # Use automatic proxy rotation with default Decodo proxies
                from .proxy_config import ProxyManager
                proxy_manager = ProxyManager()
                
                # Get optimized proxies based on sites being scraped
                if "linkedin" in [site.lower() for site in request.sites]:
                    # LinkedIn needs all proxies due to strict rate limiting
                    proxies_to_use = proxy_manager.get_proxies_for_site("linkedin")
                else:
                    # Other sites can use fewer proxies
                    proxies_to_use = proxy_manager.get_proxies_for_site(request.sites[0])
                
                print(f"Using {len(proxies_to_use)} proxies for automatic rotation")
                
            elif request.proxies:
                # Use manually provided proxies
                proxies_to_use = request.proxies
                print(f"Using {len(proxies_to_use)} manually provided proxies")
            
            # Execute the job search using JobSpy
            jobs_df = scrape_jobs(
                site_name=request.sites,
                search_term=search_term,
                location=location,
                results_wanted=request.results_wanted,
                hours_old=request.hours_old,
                country_indeed=request.country_indeed or "usa",  # Default to USA if None
                linkedin_fetch_description=request.linkedin_fetch_description,
                description_format=request.description_format,
                verbose=request.verbose,
                proxies=proxies_to_use,
                ca_cert=request.ca_cert
            )
            
            end_time = time.time()
            search_duration = end_time - start_time
            
            # Handle empty results
            if jobs_df is None or jobs_df.empty:
                return JobSearchResponse(
                    success=True,
                    message="No jobs found matching your criteria",
                    total_jobs=0,
                    jobs=[],
                    stats=JobSearchStats(
                        total_jobs=0,
                        jobs_by_site={},
                        search_duration_seconds=round(search_duration, 2),
                        proxies_used=len(proxies_to_use) if proxies_to_use else 0,
                        proxy_enabled=bool(proxies_to_use)
                    ),
                    search_parameters=request
                )
            
            # Convert DataFrame to list of JobListing models
            jobs_list = JobSearchService._dataframe_to_job_listings(jobs_df)
            
            # Generate statistics
            stats = JobSearchService._generate_stats(
                jobs_df, 
                search_duration,
                proxies_used=len(proxies_to_use) if proxies_to_use else 0,
                proxy_enabled=bool(proxies_to_use)
            )
            
            return JobSearchResponse(
                success=True,
                message=f"Successfully found {len(jobs_list)} jobs",
                total_jobs=len(jobs_list),
                jobs=jobs_list,
                stats=stats,
                search_parameters=request
            )
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Detailed error in JobSearchService: {error_details}")
            
            # Check if it's a proxy-related error
            error_str = str(e).lower()
            if any(term in error_str for term in ['proxy', 'ssl', 'handshake', 'timeout', 'connection']):
                raise Exception(f"Connection/Proxy error: {str(e)}. Try disabling proxies with 'use_proxies: false' or check your network connection.")
            
            raise Exception(f"Job search failed: {str(e)}")

    @staticmethod
    def _dataframe_to_job_listings(df: pd.DataFrame) -> List[JobListing]:
        """
        Convert pandas DataFrame to list of JobListing models
        
        Args:
            df: pandas DataFrame with job data
            
        Returns:
            List of JobListing objects
        """
        jobs = []
        
        for _, row in df.iterrows():
            # Handle emails - convert string representation to list if needed
            emails = None
            if pd.notna(row.get('emails')):
                emails_str = str(row['emails'])
                if emails_str and emails_str != 'nan':
                    # Simple parsing - in real scenarios might need more robust parsing
                    emails = [email.strip() for email in emails_str.split(',') if email.strip()]
            
            # Get description and sanitize if it's markdown
            description = row.get('description') if pd.notna(row.get('description')) else None
            if description and isinstance(description, str):
                # Check if description looks like markdown (contains ** for bold)
                if '**' in description:
                    description = JobSearchService.sanitize_markdown_description(description)
            
            job = JobListing(
                title=row.get('title') if pd.notna(row.get('title')) else None,
                company=row.get('company') if pd.notna(row.get('company')) else None,
                location=row.get('location') if pd.notna(row.get('location')) else None,
                job_type=row.get('job_type') if pd.notna(row.get('job_type')) else None,
                date_posted=row.get('date_posted') if pd.notna(row.get('date_posted')) else None,
                job_url=row.get('job_url') if pd.notna(row.get('job_url')) else None,
                job_url_direct=row.get('job_url_direct') if pd.notna(row.get('job_url_direct')) else None,
                description=description,
                min_amount=row.get('min_amount') if pd.notna(row.get('min_amount')) else None,
                max_amount=row.get('max_amount') if pd.notna(row.get('max_amount')) else None,
                currency=row.get('currency') if pd.notna(row.get('currency')) else None,
                interval=row.get('interval') if pd.notna(row.get('interval')) else None,
                site=row.get('site') if pd.notna(row.get('site')) else None,
                emails=emails,
                is_remote=row.get('is_remote') if pd.notna(row.get('is_remote')) else None,
            )
            jobs.append(job)
        
        return jobs

    @staticmethod
    def _generate_stats(df: pd.DataFrame, search_duration: float, proxies_used: int = 0, proxy_enabled: bool = False) -> JobSearchStats:
        """
        Generate statistics from the job search results
        
        Args:
            df: pandas DataFrame with job data
            search_duration: Time taken for the search in seconds
            
        Returns:
            JobSearchStats object
        """
        # Jobs by site
        jobs_by_site = df['site'].value_counts().to_dict() if 'site' in df.columns else {}
        
        # Job types (if available)
        job_types = None
        if 'job_type' in df.columns and df['job_type'].notna().any():
            job_types = df['job_type'].value_counts().to_dict()
            # Remove None/empty values
            job_types = {k: v for k, v in job_types.items() if k and str(k).lower() != 'nan'}
        
        return JobSearchStats(
            total_jobs=len(df),
            jobs_by_site=jobs_by_site,
            job_types=job_types,
            search_duration_seconds=round(search_duration, 2),
            proxies_used=proxies_used,
            proxy_enabled=proxy_enabled
        )

    @staticmethod
    def export_to_csv(jobs_df: pd.DataFrame, filename: str = None) -> str:
        """
        Export job search results to CSV file
        
        Args:
            jobs_df: pandas DataFrame with job data
            filename: Optional filename, auto-generated if not provided
            
        Returns:
            Path to the created CSV file
        """
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"job_search_results_{timestamp}.csv"
        
        # Use the same CSV export logic as the original script
        jobs_df.to_csv(filename, quoting=1, escapechar="\\", index=False)  # quoting=1 is csv.QUOTE_NONNUMERIC
        
        return filename
    
    @staticmethod
    def fetch_linkedin_descriptions(request: LinkedInBulkDescriptionRequest) -> LinkedInBulkDescriptionResponse:
        """
        Fetch job descriptions for multiple LinkedIn job URLs
        
        Args:
            request: LinkedInBulkDescriptionRequest with job URLs and options
            
        Returns:
            LinkedInBulkDescriptionResponse with results and metadata
        """
        import re
        from jobspy.linkedin import LinkedIn
        from jobspy.model import DescriptionFormat, ScraperInput
        
        results = []
        successful_count = 0
        failed_count = 0
        
        # Determine which proxies to use
        proxies_to_use = None
        if request.use_proxies:
            # Use automatic proxy rotation with default Decodo proxies
            try:
                from .proxy_config import ProxyManager
                proxy_manager = ProxyManager()
                proxies_to_use = proxy_manager.get_proxies_for_site("linkedin")
                print(f"Using {len(proxies_to_use)} proxies for LinkedIn description fetching")
            except Exception as e:
                print(f"Failed to load proxy manager: {e}. Proceeding without proxies.")
                proxies_to_use = None
        elif request.proxies:
            # Use manually provided proxies
            proxies_to_use = request.proxies
            print(f"Using {len(proxies_to_use)} manually provided proxies")
        
        # Initialize LinkedIn scraper
        try:
            linkedin_scraper = LinkedIn(
                proxies=proxies_to_use,
                ca_cert=request.ca_cert
            )
            
            # Set up scraper input for description format
            scraper_input = ScraperInput(
                search_term="dummy",  # Not used for direct description fetching
                site_name="linkedin",
                results_wanted=1,
                description_format=DescriptionFormat.from_string(request.description_format)
            )
            linkedin_scraper.scraper_input = scraper_input
            
        except Exception as e:
            # If we can't initialize the scraper, return all as failed
            error_msg = f"Failed to initialize LinkedIn scraper: {str(e)}"
            results = [
                LinkedInJobDescription(
                    job_url=url,
                    job_id=JobSearchService._extract_job_id_from_url(url),
                    success=False,
                    error=error_msg
                )
                for url in request.job_urls
            ]
            return LinkedInBulkDescriptionResponse(
                success=False,
                message=f"Failed to initialize scraper: {str(e)}",
                total_requested=len(request.job_urls),
                total_successful=0,
                total_failed=len(request.job_urls),
                results=results,
                request_parameters=request
            )
        
        # Process each URL
        for url in request.job_urls:
            try:
                job_id = JobSearchService._extract_job_id_from_url(url)
                
                if request.verbose >= 1:
                    print(f"Fetching description for LinkedIn job ID: {job_id}")
                
                # Use the LinkedIn scraper's internal method to get job details
                job_details = linkedin_scraper._get_job_details(job_id)
                
                if job_details and job_details.get('description'):
                    # Sanitize description if it's markdown
                    description = job_details.get('description')
                    if description and '**' in description:
                        description = JobSearchService.sanitize_markdown_description(description)
                        job_details['description'] = description
                    
                    result = LinkedInJobDescription(
                        job_url=url,
                        job_id=job_id,
                        success=True,
                        title=job_details.get('title'),
                        company_name=job_details.get('company_name'),
                        company_url=job_details.get('company_url'),
                        company_logo=job_details.get('company_logo'),
                        location=job_details.get('location'),
                        job_type=job_details.get('job_type'),
                        job_level=job_details.get('job_level'),
                        job_function=job_details.get('job_function'),
                        company_industry=job_details.get('company_industry'),
                        description=description,
                        job_url_direct=job_details.get('job_url_direct')
                    )
                    successful_count += 1
                else:
                    result = LinkedInJobDescription(
                        job_url=url,
                        job_id=job_id,
                        success=False,
                        error="No description found or job may be expired/private"
                    )
                    failed_count += 1
                    
            except Exception as e:
                error_msg = f"Failed to fetch description: {str(e)}"
                if request.verbose >= 1:
                    print(f"Error fetching job {job_id}: {error_msg}")
                
                result = LinkedInJobDescription(
                    job_url=url,
                    job_id=JobSearchService._extract_job_id_from_url(url),
                    success=False,
                    error=error_msg
                )
                failed_count += 1
            
            results.append(result)
            
            # Add small delay between requests to be respectful
            if len(request.job_urls) > 1:
                time.sleep(1)
        
        success_rate = successful_count / len(request.job_urls) * 100
        message = f"Retrieved descriptions for {successful_count}/{len(request.job_urls)} jobs ({success_rate:.1f}% success rate)"
        
        return LinkedInBulkDescriptionResponse(
            success=True,
            message=message,
            total_requested=len(request.job_urls),
            total_successful=successful_count,
            total_failed=failed_count,
            results=results,
            request_parameters=request
        )
    
    @staticmethod
    def _extract_job_id_from_url(url: str) -> str:
        """
        Extract LinkedIn job ID from URL or return as-is if it's already just an ID
        
        Args:
            url: LinkedIn job URL or job ID
            
        Returns:
            Job ID string
        """
        if url.isdigit():
            return url
        
        # Extract job ID from LinkedIn URL
        import re
        match = re.search(r'/jobs/view/(\d+)', url)
        if match:
            return match.group(1)
        
        # If no match, try to extract any digits at the end
        match = re.search(r'(\d+)/?$', url)
        if match:
            return match.group(1)
        
        # Fallback - just return the original URL (will likely fail)
        return url
