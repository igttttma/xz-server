"""Audio and video files uploaded through the portal for the Blimp to play.

Files live in data/<kind>/<id><ext>, listed in data/<kind>/index.json. A
file never changes once stored (a new upload gets a new id), so the Blimp can
cache it by id.
"""

import json
import os
import secrets
import time

from config.config_loader import get_project_dir

CHUNK = 256 * 1024

AUDIO_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".oga": "audio/ogg",
    ".opus": "audio/ogg",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".flac": "audio/flac",
    ".webm": "audio/webm",
}

# What the Blimp's WebView (Chromium) plays: H.264/AAC MP4, VP8/VP9/AV1 WebM
VIDEO_TYPES = {
    ".mp4": "video/mp4",
    ".m4v": "video/mp4",
    ".webm": "video/webm",
}


def _looks_like(ext: str, head: bytes) -> bool:
    """Check the file's magic bytes against its extension."""
    if ext == ".mp3":
        return head[:3] == b"ID3" or (len(head) > 1 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0)
    if ext == ".aac":
        return head[:3] == b"ID3" or (len(head) > 1 and head[0] == 0xFF and head[1] & 0xF6 == 0xF0)
    if ext == ".wav":
        return head[:4] == b"RIFF" and head[8:12] == b"WAVE"
    if ext in (".ogg", ".oga", ".opus"):
        return head[:4] == b"OggS"
    if ext == ".flac":
        return head[:4] == b"fLaC"
    if ext in (".m4a", ".mp4", ".m4v"):
        return head[4:8] == b"ftyp"
    if ext == ".webm":
        return head[:4] == b"\x1a\x45\xdf\xa3"
    return False


class UploadError(ValueError):
    pass


class MediaLibrary:
    def __init__(self, kind: str, types: dict, max_mb: int):
        self.kind = kind  # "audio" | "video"; also the folder under data/
        self.types = types
        self.max_bytes = max_mb * 1024 * 1024
        self.dir = get_project_dir() + f"data/{kind}/"
        self.index_path = self.dir + "index.json"
        os.makedirs(self.dir, exist_ok=True)

    def _load(self) -> list:
        if not os.path.exists(self.index_path):
            return []
        with open(self.index_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, entries: list):
        tmp = self.index_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
        os.replace(tmp, self.index_path)

    def list(self) -> list:
        return sorted(self._load(), key=lambda e: -e["uploaded_at"])

    def get(self, clip_id: str):
        return next((e for e in self._load() if e["id"] == clip_id), None)

    def path(self, entry: dict) -> str:
        return self.dir + entry["file"]

    async def add(self, part) -> dict:
        """Store an uploaded multipart file field."""
        name = os.path.basename(part.filename or "")
        stem, ext = os.path.splitext(name)
        ext = ext.lower()
        if ext not in self.types:
            raise UploadError(f"{name}: unsupported type; use {', '.join(sorted(self.types))}")
        clip_id = secrets.token_hex(8)
        path = self.dir + clip_id + ext
        size = 0
        try:
            with open(path, "wb") as f:
                while chunk := await part.read_chunk(CHUNK):
                    if size == 0 and not _looks_like(ext, chunk[:16]):
                        raise UploadError(f"{name} is not a valid {ext[1:]} file")
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise UploadError(f"{name} is larger than {self.max_bytes // (1024 * 1024)} MB")
                    f.write(chunk)
            if size == 0:
                raise UploadError(f"{name} is empty")
        except BaseException:
            os.remove(path)
            raise
        entry = {
            "id": clip_id,
            "title": (stem.strip() or "Untitled")[:120],
            "file": clip_id + ext,
            "mime": self.types[ext],
            "size": size,
            "uploaded_at": time.time(),
        }
        entries = self._load()
        entries.append(entry)
        self._save(entries)
        return entry

    def delete(self, clip_id: str) -> bool:
        entries = self._load()
        entry = next((e for e in entries if e["id"] == clip_id), None)
        if entry is None:
            return False
        self._save([e for e in entries if e["id"] != clip_id])
        try:
            os.remove(self.path(entry))
        except FileNotFoundError:
            pass
        return True
