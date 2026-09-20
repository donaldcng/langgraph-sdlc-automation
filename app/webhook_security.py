"""Small in-process protections for GitHub webhook delivery handling."""

from threading import Lock
from time import monotonic


class DeliveryReplayGuard:
    """Track recent delivery IDs to avoid duplicate workflow execution."""

    def __init__(self, *, ttl_seconds: int = 3600, max_entries: int = 10000) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._seen: dict[str, float] = {}
        self._lock = Lock()

    def claim(self, delivery_id: str) -> bool:
        """Claim an ID, returning False when it was seen within the TTL."""

        now = monotonic()
        with self._lock:
            expired = [key for key, timestamp in self._seen.items() if now - timestamp >= self.ttl_seconds]
            for key in expired:
                del self._seen[key]
            if delivery_id in self._seen:
                return False
            if len(self._seen) >= self.max_entries:
                oldest = min(self._seen, key=self._seen.get)
                del self._seen[oldest]
            self._seen[delivery_id] = now
            return True

    def release(self, delivery_id: str) -> None:
        """Allow a failed background delivery to be retried."""

        with self._lock:
            self._seen.pop(delivery_id, None)
