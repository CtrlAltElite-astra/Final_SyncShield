"""Hybrid logical clock (owner: Rahil). Pure: caller supplies the wall clock.

State and results are (physical_ms, counter) tuples. The clock never goes
backwards even if the wall clock jumps back. It is used for tie-breaks and
display only, never to decide safety.
"""
from typing import Tuple

HLC = Tuple[int, int]


def tick(state: HLC, now_ms: int) -> HLC:
    """Local event or send."""
    l, c = state
    nl = max(l, now_ms)
    return (nl, c + 1 if nl == l else 0)


def receive(state: HLC, remote: HLC, now_ms: int) -> HLC:
    """Merge a remote timestamp into the local clock."""
    l, c = state
    rl, rc = remote
    nl = max(l, rl, now_ms)
    if nl == l and nl == rl:
        return (nl, max(c, rc) + 1)
    if nl == l:
        return (nl, c + 1)
    if nl == rl:
        return (nl, rc + 1)
    return (nl, 0)


def is_suspect(remote: HLC, now_ms: int, limit_ms: int = 60_000) -> bool:
    """True when a remote stamp is more than 60 s ahead of our clock."""
    return remote[0] - now_ms > limit_ms
