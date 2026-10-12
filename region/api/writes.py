"""The local write path (owner: Akshit, engine calls by Rahil).

Always local, always durable before the caller sees 201. Never calls a peer.
"""
from datetime import datetime, timezone

from region import config, store
from region.engine import canonical, hlc
from region.engine.derive import derive

class NotFound(Exception):
    pass


class StaleEdit(Exception):
    def __init__(self, live):
        self.live = live


def _wall() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def local_write(report_id, type_, field, value, actor, expected=None) -> dict:
    """Append one event and refresh the report view in the same transaction."""
    region = config.settings.region
    with store.tx() as conn:
        if type_ != "CREATE" and not store.report_exists(conn, report_id):
            raise NotFound(report_id)
        live = store.live_ids(conn, report_id, field) if (field and type_ != "CREATE") else []
        if expected is not None and sorted(expected) != sorted(live):
            raise StaleEdit(live)
        seq = store.next_seq(conn)
        if type_ == "CREATE":
            report_id = f"R-{region}-{seq}"
        h = hlc.tick(store.load_hlc(conn), store.now_ms())
        store.save_hlc(conn, h)
        ev = dict(
            v=1, event_id=f"{region}:{seq}", origin=region, seq=seq, report_id=report_id,
            type=type_, field=field, value=value, supersedes=live, hlc=[h[0], h[1]],
            priority=1, actor=actor, reason=None, wall=_wall(), sig=None,
        )
        ev["hash"] = canonical.event_hash(ev)
        store.insert_event(conn, ev)
        store.save_view(conn, report_id, derive(store.events_for(conn, report_id)))
    return ev  # committed
