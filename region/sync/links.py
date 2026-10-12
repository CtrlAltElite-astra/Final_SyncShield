"""Link switch API (owner: Simrit). Thin wrapper over state.py.

One 'down' blocks BOTH directions on this region: outbound pulls are skipped
and /internal answers 503 to that peer.
"""
from region.sync import state

MODES = ("up", "down")  # 'slow' (delay_ms, rate_bps) arrives in PDF 2 Phase 2


def mode(peer: str) -> str:
    return state.link_mode(peer)


def is_down(peer: str) -> bool:
    return state.link_mode(peer) == "down"


def set_mode(peer: str, new_mode: str) -> None:
    if new_mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    state.set_link_mode(peer, new_mode)


def all_modes() -> dict:
    return state.all_links()
