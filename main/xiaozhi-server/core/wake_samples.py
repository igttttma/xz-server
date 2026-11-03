"""Wake word samples recorded on the Blimp (portal "Wake word samples").

Each sample is a 16 kHz mono WAV from the Blimp's wake word microphone, with the
score the on-device model gave it, kept for retraining the wake word models with
real voices in the real room. Files: data/wake_samples/<label>/<id>.wav, plus
data/wake_samples/index.json (newest first).
"""

import io
import json
import os
import threading
import time
import uuid
import zipfile

from config.config_loader import get_project_dir

# What was said: the wake word, the call keyword, other speech (must not wake it),
# room sound without speech
LABELS = {
    "hey_blimp": "Hey Blimp",
    "answer": "Answer",
    "other": "Other speech",
    "background": "Background",
}


class WakeSamples:
    def __init__(self, root: str = None):
        self.root = root or os.path.join(get_project_dir(), "data", "wake_samples")
        self._index_path = os.path.join(self.root, "index.json")
        self._lock = threading.Lock()
        os.makedirs(self.root, exist_ok=True)
        self._entries = self._load()

    def _load(self) -> list:
        try:
            with open(self._index_path, encoding="utf-8") as f:
                entries = json.load(f)
            return [e for e in entries if os.path.isfile(self.path(e))]
        except (OSError, ValueError):
            return []

    def _save(self):
        tmp = self._index_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._entries, f, ensure_ascii=False, indent=1)
        os.replace(tmp, self._index_path)

    def path(self, entry: dict) -> str:
        return os.path.join(self.root, entry["label"], f"{entry['id']}.wav")

    def list(self) -> list:
        with self._lock:
            return list(self._entries)

    def counts(self) -> dict:
        counts = {label: 0 for label in LABELS}
        for e in self.list():
            counts[e["label"]] = counts.get(e["label"], 0) + 1
        return counts

    def get(self, sample_id: str):
        return next((e for e in self.list() if e["id"] == sample_id), None)

    def add(self, label: str, wav: bytes, **meta) -> dict:
        if label not in LABELS:
            raise ValueError(f"unknown label {label}")
        entry = {
            "id": time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6],
            "label": label,
            "created": time.time(),
            "seconds": round(max(len(wav) - 44, 0) / 32000, 2),
            **meta,
        }
        os.makedirs(os.path.join(self.root, label), exist_ok=True)
        with open(self.path(entry), "wb") as f:
            f.write(wav)
        with self._lock:
            self._entries.insert(0, entry)
            self._save()
        return entry

    def delete(self, sample_id: str) -> bool:
        with self._lock:
            entry = next((e for e in self._entries if e["id"] == sample_id), None)
            if entry is None:
                return False
            self._entries.remove(entry)
            self._save()
        try:
            os.remove(self.path(entry))
        except OSError:
            pass
        return True

    def zip_bytes(self) -> bytes:
        """Every sample in <label>/<id>.wav, plus index.json (scores, levels, times)."""
        buf = io.BytesIO()
        entries = self.list()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for e in entries:
                z.write(self.path(e), f"{e['label']}/{e['id']}.wav")
            z.writestr("index.json", json.dumps(entries, ensure_ascii=False, indent=1))
        return buf.getvalue()
