"""
Proxy configuration management for JobSpy API
"""

import os
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def format_proxy_from_decodo(proxy_string: str) -> str:
    """
    Convert Decodo proxy format (host:port:user:pass) to JobSpy format (user:pass@host:port)
    
    Args:
        proxy_string: Proxy in format "host:port:user:pass"
        
    Returns:
        Proxy in format "user:pass@host:port"
    """
    parts = proxy_string.split(':')
    if len(parts) == 4:
        host, port, user, password = parts
        return f"{user}:{password}@{host}:{port}"
    elif len(parts) == 2:
        # Already in host:port format, assume no auth
        return proxy_string
    else:
        # Assume it's already in correct format
        return proxy_string


def get_decodo_proxies() -> List[str]:
    """
    Get the list of Decodo proxies in JobSpy format
    
    Returns:
        List of proxy strings in format "user:pass@host:port"
    """
    decodo_proxies_raw = [
        "gate.decodo.com:7000:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
        "gate.decodo.com:7000:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
        "gate.decodo.com:7000:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
        "gate.decodo.com:7000:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
        "gate.decodo.com:7000:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
        "gate.decodo.com:7000:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
        "gate.decodo.com:7000:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
        "gate.decodo.com:7000:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
        "gate.decodo.com:7000:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
        "gate.decodo.com:7000:spg83ur5k3:Cv~wjcw3h44h2UdUNf"
    ]
    
    # Convert to JobSpy format
    formatted_proxies = [format_proxy_from_decodo(proxy) for proxy in decodo_proxies_raw]
    
    logger.info(f"Loaded {len(formatted_proxies)} Decodo proxies for rotation")
    return formatted_proxies


def get_default_proxies() -> List[str]:
    """
    Get default proxy list. Can be overridden with environment variables.
    
    Returns:
        List of proxy strings ready for JobSpy
    """
    # Check if proxies are provided via environment variables
    env_proxies = os.environ.get("JOBSPY_PROXIES")
    if env_proxies:
        # Split by comma and clean up
        proxy_list = [proxy.strip() for proxy in env_proxies.split(",") if proxy.strip()]
        logger.info(f"Using {len(proxy_list)} proxies from environment")
        return proxy_list
    
    # Use default Decodo proxies
    return get_decodo_proxies()


def validate_proxy_format(proxy: str) -> bool:
    """
    Validate if proxy is in correct format for JobSpy
    
    Args:
        proxy: Proxy string to validate
        
    Returns:
        True if format is valid, False otherwise
    """
    # Check for common valid formats
    valid_formats = [
        # user:pass@host:port
        lambda p: "@" in p and ":" in p.split("@")[0] and ":" in p.split("@")[1],
        # host:port (no auth)
        lambda p: "@" not in p and p.count(":") == 1,
        # http://user:pass@host:port
        lambda p: p.startswith(("http://", "https://", "socks5://")),
        # localhost
        lambda p: p.lower() == "localhost"
    ]
    
    return any(format_check(proxy) for format_check in valid_formats)


def get_proxy_stats(proxies: List[str]) -> dict:
    """
    Get statistics about the proxy list
    
    Args:
        proxies: List of proxy strings
        
    Returns:
        Dictionary with proxy statistics
    """
    if not proxies:
        return {"total": 0, "authenticated": 0, "hosts": []}
    
    authenticated_count = sum(1 for proxy in proxies if "@" in proxy)
    hosts = list(set([
        proxy.split("@")[1].split(":")[0] if "@" in proxy 
        else proxy.split(":")[0] 
        for proxy in proxies 
        if proxy.lower() != "localhost"
    ]))
    
    return {
        "total": len(proxies),
        "authenticated": authenticated_count,
        "hosts": hosts,
        "unique_hosts": len(hosts)
    }


class ProxyManager:
    """
    Manage proxy configuration and rotation
    """
    
    def __init__(self, proxies: Optional[List[str]] = None):
        """
        Initialize proxy manager
        
        Args:
            proxies: Optional list of proxies. If None, uses default proxies.
        """
        self.proxies = proxies or get_default_proxies()
        self.stats = get_proxy_stats(self.proxies)
        
    def get_proxies_for_site(self, site: str) -> List[str]:
        """
        Get proxies optimized for specific job site
        
        Args:
            site: Job site name (linkedin, indeed, etc.)
            
        Returns:
            List of proxies suitable for the site
        """
        # LinkedIn is most restrictive, use all proxies
        if site.lower() == "linkedin":
            return self.proxies
        
        # For other sites, we can use fewer proxies or no proxies
        # Indeed and Google are less restrictive
        if site.lower() in ["indeed", "google"]:
            # Use every other proxy to save proxy usage
            return self.proxies[::2] if len(self.proxies) > 2 else self.proxies
        
        # For other sites, use default set
        return self.proxies
    
    def get_stats(self) -> dict:
        """Get proxy statistics"""
        return self.stats