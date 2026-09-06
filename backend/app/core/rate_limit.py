"""
Shared slowapi Limiter instance, keyed by client IP.

Lives in its own module (not main.py) so router files can import it and
decorate specific endpoints (e.g. auth.py's login/register) without a
circular import — main.py imports routers, so routers can't import
`limiter` back out of main.py.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(key_func=get_remote_address, enabled=settings.RATE_LIMIT_ENABLED)