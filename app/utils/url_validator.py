"""URL validation for callback URLs."""
from urllib.parse import urlparse
import ipaddress


def validate_callback_url(url: str) -> tuple[bool, str | None]:
    """
    Validate callback URL for security.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        parsed = urlparse(str(url))
        
        # Check scheme
        if parsed.scheme not in ["http", "https"]:
            return False, f"Invalid scheme: {parsed.scheme}. Only http/https allowed."
        
        # Check hostname
        hostname = parsed.hostname
        if not hostname:
            return False, "Invalid URL: no hostname"
        
        # Block localhost if configured
        from ..config import get_settings
        settings = get_settings()
        
        if settings.block_localhost and hostname.lower() in ["localhost", "127.0.0.1", "::1"]:
            return False, "Localhost URLs are not allowed"
        
        # Try to parse as IP
        try:
            ip = ipaddress.ip_address(hostname)
            
            # Block private IPs
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False, f"Private/internal IP addresses are not allowed: {hostname}"
        
        except ValueError:
            # Not an IP, it's a domain name - that's fine
            pass
        
        return True, None
    
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"
