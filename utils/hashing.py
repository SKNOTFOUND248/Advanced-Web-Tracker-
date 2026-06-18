import hashlib

def generate_hash(content: str) -> str:
    """
    Generates a SHA256 hash for the given content.
    Returns the hexadecimal digest.
    """
    if content is None:
        return ""
    
    # Encode string to bytes and generate hash
    hasher = hashlib.sha256()
    hasher.update(content.encode('utf-8'))
    return hasher.hexdigest()
