"""Helpers for the TartuNLP TTS integration."""
from urllib.parse import urlparse


def get_domain_from_url(url: str) -> str:
    """Extract domain from URL."""
    parsed = urlparse(url)
    domain = parsed.netloc
    if not domain:  # Handle cases where URL might not have protocol
        domain = parsed.path.split('/')[0]
    return domain
