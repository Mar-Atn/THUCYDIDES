"""Async Supabase client for non-blocking DB operations.

Used by EventDispatcher and other async-native code that must not
block the event loop. The sync get_client() in supabase.py is
preserved for sync code (tool_executor, action_dispatcher, engines).
"""

import asyncio
import os
import logging

logger = logging.getLogger(__name__)

_async_client = None
_init_lock = asyncio.Lock()


async def get_async_client():
    """Get or create the async Supabase client (singleton with lock)."""
    global _async_client
    if _async_client is not None:
        return _async_client

    async with _init_lock:
        if _async_client is not None:
            return _async_client

        from supabase import create_async_client

        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

        if not url or not key:
            # Try loading from settings
            try:
                from engine.config.settings import settings
                url = settings.supabase_url
                key = settings.supabase_service_role_key
            except Exception:
                pass

        _async_client = await create_async_client(url, key)
        logger.info("Async Supabase client initialized")
        return _async_client
