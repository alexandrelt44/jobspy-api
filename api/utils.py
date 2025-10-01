"""
Utility functions for JobSpy API
"""

import os
import asyncio
from pathlib import Path


def get_version() -> str:
    """
    Get the version from pyproject.toml
    
    Returns:
        Version string or 'unknown' if not found
    """
    try:
        # Try to read from pyproject.toml in parent directory
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        
        if pyproject_path.exists():
            with open(pyproject_path, "r") as f:
                content = f.read()
                # Simple regex to extract version
                import re
                match = re.search(r'version\s*=\s*"([^"]+)"', content)
                if match:
                    return match.group(1)
    except Exception:
        pass
    
    return "1.1.82"


async def cleanup_csv_file(filename: str, delay: int = 30):
    """
    Clean up CSV file after a delay (background task)
    
    Args:
        filename: Path to the CSV file to delete
        delay: Delay in seconds before deletion
    """
    try:
        # Wait for the specified delay
        await asyncio.sleep(delay)
        
        # Remove the file if it exists
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Cleaned up temporary CSV file: {filename}")
    except Exception as e:
        print(f"Error cleaning up CSV file {filename}: {e}")


def validate_search_parameters(search_term: str, location: str) -> tuple[bool, str]:
    """
    Validate search parameters
    
    Args:
        search_term: Job search term
        location: Job location
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not search_term or not search_term.strip():
        return False, "search_term cannot be empty"
    
    if not location or not location.strip():
        return False, "location cannot be empty"
    
    if len(search_term.strip()) < 2:
        return False, "search_term must be at least 2 characters long"
    
    if len(location.strip()) < 2:
        return False, "location must be at least 2 characters long"
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Ensure it's not empty
    if not filename:
        filename = "job_search_results"
    
    return filename


def format_job_count_message(total_jobs: int, sites: list) -> str:
    """
    Format a user-friendly message about job search results
    
    Args:
        total_jobs: Total number of jobs found
        sites: List of sites searched
        
    Returns:
        Formatted message string
    """
    sites_str = ", ".join(sites)
    
    if total_jobs == 0:
        return f"No jobs found on {sites_str}. Try adjusting your search parameters."
    elif total_jobs == 1:
        return f"Found 1 job on {sites_str}."
    else:
        return f"Found {total_jobs} jobs across {sites_str}."


def truncate_description(description: str, max_length: int = 300) -> str:
    """
    Truncate job description to specified length
    
    Args:
        description: Original job description
        max_length: Maximum length for truncated description
        
    Returns:
        Truncated description with ellipsis if needed
    """
    if not description:
        return ""
    
    if len(description) <= max_length:
        return description
    
    return description[:max_length].rstrip() + "..."