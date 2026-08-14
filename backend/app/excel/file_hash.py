import hashlib

def compute_file_hash(file_path: str) -> str:
    """
    Computes a SHA-256 hash of file content for identifying duplicate uploads.
    Same content -> same hash, regardless of filename.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()