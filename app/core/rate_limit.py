from slowapi import Limiter
from slowapi.util import get_remote_address

# storage_uri="memory://" uses an in-memory store for development/single-process.
# Replace with "redis://host:6379" in production for multi-process support.
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
