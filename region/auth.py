"""API key -> (actor, role). Actor comes from the key, never from the body.

Basic build: one key from config. Roles are enforced from PDF 2 Phase 1.
"""
from collections import namedtuple

from fastapi import Header, HTTPException

from region import config

Auth = namedtuple("Auth", "actor role")


def require_key(x_api_key: str = Header(None)) -> Auth:
    entry = config.settings.api_keys.get(x_api_key or "")
    if entry is None:
        raise HTTPException(401, "missing or unknown X-API-Key")
    return Auth(*entry)
