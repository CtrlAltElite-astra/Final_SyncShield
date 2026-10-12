"""Engine tests (owner: Rahil). Pure, no I/O."""
import itertools
import random

from region.engine import canonical, hlc
from region.engine.derive import derive
from region.engine.digest import event_digest, state_hash


def mk(origin, seq, type_, field=None, value=None, supersedes=(), hlc_=None, report="R-mum-1"):
    ev = dict(v=1, event_id=f"{origin}:{seq}", origin=origin, seq=seq, report_id=report, type=type_,
              field=field, value=value, supersedes=list(supersedes), hlc=list(hlc_ or (1000 + seq, 0)),
              priority=1, actor="t", reason=None, wall="x", sig=None)
    ev["hash"] = canonical.event_hash(ev)
    return ev


CREATE = mk("mum", 1, "CREATE", value={"title": "Wall", "severity": 3, "status": "open"}, hlc_=(1000, 0))


# ---- canonical / hash ----------------------------------------------------
def test_canonical_is_key_order_independent():
    assert canonical.dumps({"b": 1, "a": 2}) == canonical.dumps({"a": 2, "b": 1}) == '{"a":2,"b":1}'


def test_hash_stable_and_ignores_hash_and_sig():
    ev = dict(CREATE)
    h = canonical.event_hash(ev)
    ev["hash"], ev["sig"] = "zzz", "sig"
    assert canonical.event_hash(ev) == h == CREATE["hash"]


def test_hash_changes_with_content():
    ev = dict(CREATE, value={"title": "Other"})
    assert canonical.event_hash(ev) != CREATE["hash"]


# ---- HLC -----------------------------------------------------------------
def test_hlc_never_goes_backwards_when_wall_clock_jumps_back():
    s = hlc.tick((0, 0), 1_000_000)
    s2 = hlc.tick(s, 1_000_000 - 10_000)
    assert s2 > s
    assert hlc.tick(s2, 1_000_000 - 10_000) > s2


def test_hlc_receive_is_after_both():
    local, remote = (100, 5), (500, 2)
    r = hlc.receive(local, remote, 50)
    assert r > local and r > remote


def test_hlc_suspect_clock():
    assert hlc.is_suspect((200_000, 0), 0) and not hlc.is_suspect((30_000, 0), 0)


# ---- derive --------------------------------------------------------------
def test_sequential_edit_is_not_a_conflict():
    a = mk("mum", 2, "SET", "severity", 4, supersedes=["mum:1"])
    b = mk("mum", 3, "SET", "severity", 5, supersedes=["mum:2"])
    v = derive([CREATE, a, b])
    assert v["state"]["severity"] == 5 and v["conflicts"] == [] and v["live"]["severity"] == ["mum:3"]


def test_concurrent_edit_is_a_conflict_and_deterministic():
    m = mk("mum", 2, "SET", "severity", 5, supersedes=["mum:1"], hlc_=(2000, 0))
    p = mk("pun", 1, "SET", "severity", 4, supersedes=["mum:1"], hlc_=(2001, 0))
    v = derive([CREATE, m, p])
    assert [c["field"] for c in v["conflicts"]] == ["severity"]
    assert sorted(v["conflicts"][0]["values"]) == [4, 5]
    assert v["state"]["severity"] == 4  # latest by hlc in v0


def test_disjoint_fields_do_not_conflict():
    a = mk("mum", 2, "SET", "status", "closed", supersedes=["mum:1"])
    b = mk("pun", 1, "SET", "severity", 5, supersedes=["mum:1"])
    v = derive([CREATE, a, b])
    assert v["conflicts"] == [] and v["state"]["status"] == "closed" and v["state"]["severity"] == 5


def test_equal_concurrent_values_are_not_a_conflict():
    a = mk("mum", 2, "SET", "severity", 4, supersedes=["mum:1"])
    b = mk("pun", 1, "SET", "severity", 4, supersedes=["mum:1"])
    assert derive([CREATE, a, b])["conflicts"] == []


def test_notes_union_and_incomplete_flag():
    n = mk("pun", 1, "NOTE", value={"text": "two trapped"})
    assert derive([n])["incomplete"] is True
    v = derive([CREATE, n])
    assert v["incomplete"] is False and v["state"]["notes"] == [{"id": "pun:1", "text": "two trapped"}]


def test_permutations_and_duplicates_give_identical_view():
    m = mk("mum", 2, "SET", "severity", 5, supersedes=["mum:1"], hlc_=(2000, 0))
    p = mk("pun", 1, "SET", "severity", 4, supersedes=["mum:1"], hlc_=(2001, 0))
    n = mk("pun", 2, "NOTE", value={"text": "x"}, hlc_=(2002, 0))
    s = mk("mum", 3, "SET", "status", "assigned", supersedes=["mum:1"], hlc_=(2003, 0))
    base = [CREATE, m, p, n, s]
    want = canonical.dumps(derive(base))
    for perm in itertools.islice(itertools.permutations(base), 120):
        assert canonical.dumps(derive(list(perm))) == want
    rnd = random.Random(7)
    for _ in range(20):
        dup = base + rnd.choices(base, k=6)
        rnd.shuffle(dup)
        assert canonical.dumps(derive(dup)) == want


# ---- digests -------------------------------------------------------------
def test_digests_are_order_independent():
    pairs = [("mum:1", "a"), ("pun:1", "b"), ("mum:2", "c")]
    assert event_digest(pairs) == event_digest(reversed(pairs))
    v1 = {"R-1": derive([CREATE]), "R-2": derive([mk("mum", 9, "CREATE", value={"title": "b"})])}
    assert state_hash(v1) == state_hash(dict(reversed(list(v1.items()))))
