"""
Echo Service - Data processing and transformation
"""

import hashlib

from app import __service__


def process(body: bytes) -> dict:
    """
    Process and transform request body

    Args:
        body: Raw request body bytes

    Returns:
        dict with transformed data
    """
    text = body.decode("utf-8")

    # Calculate SHA256 hash (first 16 chars)
    sha = hashlib.sha256(text.encode()).hexdigest()[:16]

    # Count words
    words = text.split()

    return {
        "original_length": len(text),
        "word_count": len(words),
        "char_count": len(text.replace(" ", "")),
        "uppercase": text.upper(),
        "lowercase": text.lower(),
        "sha256_prefix": sha,
        "service": __service__
    }