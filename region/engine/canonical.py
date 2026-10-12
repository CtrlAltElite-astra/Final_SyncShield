"""Canonical JSON and event hashing (owner: Rahil). Pure, no I/O."""
import hashlib
import json

_HASH_EXCLUDED = ("hash", "sig")


def dumps(obj) -> str:
    """Canonical JSON: sorted keys, no spaces, UTF-8 safe."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def event_hash(ev: dict) -> str:
    """sha256 over the canonical JSON of every field except 'hash' and 'sig'."""
    body = {k: v for k, v in ev.items() if k not in _HASH_EXCLUDED}
    return hashlib.sha256(dumps(body).encode("utf-8")).hexdigest()
