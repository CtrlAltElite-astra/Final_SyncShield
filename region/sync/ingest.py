"""Idempotent ingest of events from a peer (owner: Simrit).

Used by pull now and by push in PDF 2. Applying a page twice inserts nothing.
Received events are checked for shape, hash and identity only, never against
the receiver's business rules.
"""
from contracts.schemas import EVENT_REQUIRED
from region import store
from region.engine import canonical
from region.engine.derive import derive
from region.sync import state


def ingest(events: list, source: str) -> dict:
    stats = {"new": 0, "dup": 0, "rejected": 0}
    with store.tx() as conn:
        dirty = set()
        for ev in events:
            if not isinstance(ev, dict) or any(k not in ev for k in EVENT_REQUIRED) \
                    or ev["event_id"] != f"{ev['origin']}:{ev['seq']}":
                store.quarantine(conn, ev, source, "bad_shape")
                stats["rejected"] += 1
                continue
            if canonical.event_hash(ev) != ev["hash"]:
                store.quarantine(conn, ev, source, "bad_hash")
                stats["rejected"] += 1
                continue
            r = store.insert_event_if_absent(conn, ev)
            if r == "mismatch":
                store.quarantine(conn, ev, source, "id_reused")
                stats["rejected"] += 1
            elif r == "new":
                state.advance(conn, ev["origin"], ev["seq"])
                store.hlc_receive(conn, ev["hlc"])
                dirty.add(ev["report_id"])
                stats["new"] += 1
            else:
                stats["dup"] += 1
        for rid in dirty:
            store.save_view(conn, rid, derive(store.events_for(conn, rid)))
    return stats
