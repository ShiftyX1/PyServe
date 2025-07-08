import os
import time

class VibeCache:
    def __init__(self, base_dir="./cache"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _path_for_url(self, url: str) -> str:
        if url == "/":
            url = "/index"
        path = os.path.join(self.base_dir, *url.strip("/").split("/"), "index.html")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    def get(self, url: str, ttl: int) -> str | None:
        path = self._path_for_url(url)
        if not os.path.exists(path):
            return None
        mtime = os.path.getmtime(path)
        if time.time() - mtime > ttl:
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def set(self, url: str, content: str):
        path = self._path_for_url(url)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
