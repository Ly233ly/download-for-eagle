from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: str | Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    file_path = Path(path)
    digest = hashlib.sha256()
    buffer = bytearray(chunk_size)
    view = memoryview(buffer)
    with file_path.open("rb") as stream:
        while size := stream.readinto(buffer):
            digest.update(view[:size])
    return digest.hexdigest()
