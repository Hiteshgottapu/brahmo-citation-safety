"""
Async Supabase client singleton.
Lazily initialized on first call to get_supabase().
"""

from supabase import acreate_client, AsyncClient
from config import SUPABASE_URL, SUPABASE_KEY

_supabase_client: AsyncClient | None = None


async def get_supabase() -> AsyncClient:
    """Return the singleton async Supabase client, creating it on first use."""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in the environment / .env file."
            )
        _supabase_client = await acreate_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client
