"""/admin/links (owner: Simrit). Needs ENABLE_ADMIN=1 and a valid API key."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from region import config
from region.auth import require_key
from region.sync import links

router = APIRouter(prefix="/admin", tags=["admin"])


def admin_guard(auth=Depends(require_key)):
    if not config.settings.enable_admin:
        raise HTTPException(403, "admin disabled")
    return auth


class LinkBody(BaseModel):
    mode: Literal["up", "down"]


@router.get("/links")
def get_links(_=Depends(admin_guard)):
    return links.all_modes()


@router.get("/links/{peer}")
def get_link(peer: str, _=Depends(admin_guard)):
    if peer not in config.settings.peers:
        raise HTTPException(404, "unknown peer")
    return {"peer": peer, "mode": links.mode(peer)}


@router.post("/links/{peer}")
def set_link(peer: str, body: LinkBody, _=Depends(admin_guard)):
    if peer not in config.settings.peers:
        raise HTTPException(404, "unknown peer")
    links.set_mode(peer, body.mode)
    return {"peer": peer, "mode": links.mode(peer)}
