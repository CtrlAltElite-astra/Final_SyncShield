"""Convergence digests (owner: Rahil). Pure.

Two regions that hold the same events must report identical values.
"""
import hashlib

from region.engine import canonical


def event_digest(pairs) -> str:
    """pairs: iterable of (event_id, hash). Order independent."""
    lines = sorted(f"{eid}:{h}" for eid, h in pairs)
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def state_hash(views: dict) -> str:
    """views: {report_id: derived view}. Local metadata must not be inside."""
    ordered = [[rid, views[rid]] for rid in sorted(views)]
    return hashlib.sha256(canonical.dumps(ordered).encode("utf-8")).hexdigest()
