"""M1 / M1b evidence against REAL processes (owner: Simrit).

Starts mum+pun on spare ports with temp DBs, then walks PDF 1 section 8.
Run: pytest tests/integration -q
"""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]
PORTS = {"mum": 18001, "pun": 18002}
KEY = {"X-API-Key": "dev-officer"}
URL = {r: f"http://127.0.0.1:{p}" for r, p in PORTS.items()}


def start(region, tmp):
    env = dict(os.environ)
    other = "pun" if region == "mum" else "mum"
    env.update(REGION=region, PORT=str(PORTS[region]), DB_PATH=str(Path(tmp) / f"{region}.db"),
               PEERS=f"{other}={URL[other]}", PEER_TOKEN="t", SYNC_INTERVAL_MS="300",
               API_KEYS=f"dev-officer:officer-{region}-1:officer", PYTHONPATH=str(ROOT), ENV_FILE="none")
    return subprocess.Popen([sys.executable, "-m", "uvicorn", "region.main:app", "--host", "127.0.0.1",
                             "--port", str(PORTS[region]), "--workers", "1", "--log-level", "error"],
                            cwd=ROOT, env=env)


def wait_up(region, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if httpx.get(URL[region] + "/v1/health", timeout=0.5).status_code == 200:
                return
        except httpx.HTTPError:
            time.sleep(0.2)
    raise TimeoutError(region)


def until(fn, timeout=6.0):
    end = time.time() + timeout
    while time.time() < end:
        v = fn()
        if v:
            return v
        time.sleep(0.15)
    raise AssertionError("condition not reached in time")


def status(r):
    return httpx.get(URL[r] + "/v1/status", timeout=2).json()


def link(a, peer, mode):
    assert httpx.post(f"{URL[a]}/admin/links/{peer}", json={"mode": mode}, headers=KEY, timeout=2).status_code == 200


@pytest.fixture(scope="module")
def regions():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:  # Windows keeps -shm briefly
        procs = {r: start(r, tmp) for r in PORTS}
        try:
            for r in PORTS:
                wait_up(r)
            yield tmp, procs
        finally:
            for p in procs.values():
                p.kill()
                p.wait()


def test_m1_replication_restart_and_duplicates(regions):
    tmp, procs = regions
    r = httpx.post(URL["mum"] + "/v1/reports", headers=KEY, timeout=3,
                   json={"title": "Wall collapse, Kurla", "category": "collapse", "severity": 3})
    assert r.status_code == 201 and r.json()["event_id"] == "mum:1"
    assert r.json()["report"]["report_id"] == "R-mum-1"

    until(lambda: [x["report_id"] for x in httpx.get(URL["pun"] + "/v1/reports").json()] == ["R-mum-1"])
    until(lambda: status("mum")["heads"].get("mum") == status("pun")["heads"].get("mum") == 1)
    assert status("mum")["event_digest"] == status("pun")["event_digest"]
    assert status("mum")["state_hash"] == status("pun")["state_hash"]

    # restart proof: kill -9 pun, start again, data still there, no duplicates
    procs["pun"].kill()
    procs["pun"].wait()
    procs["pun"] = start("pun", tmp)
    wait_up("pun")
    assert len(httpx.get(URL["pun"] + "/v1/reports").json()) == 1
    time.sleep(1.0)
    assert status("pun")["event_count"] == 1


def test_sequential_patches_make_no_conflict(regions):
    for v in (4, 5):
        assert httpx.patch(URL["mum"] + "/v1/reports/R-mum-1", headers=KEY, timeout=3,
                           json={"field": "severity", "value": v}).status_code == 200
    rep = httpx.get(URL["mum"] + "/v1/reports/R-mum-1").json()
    assert rep["conflicts"] == [] and rep["state"]["severity"] == 5
    until(lambda: httpx.get(URL["pun"] + "/v1/reports/R-mum-1").json()["state"]["severity"] == 5)


def test_stale_expected_returns_409(regions):
    r = httpx.patch(URL["mum"] + "/v1/reports/R-mum-1", headers=KEY, timeout=3,
                    json={"field": "severity", "value": 2, "expected": ["mum:1"]})
    assert r.status_code == 409 and r.json()["live"]
    assert httpx.patch(URL["mum"] + "/v1/reports/R-nope-9", headers=KEY, timeout=3,
                       json={"field": "severity", "value": 2}).status_code == 404


def test_m1b_partition_both_write_heal_converge(regions):
    link("mum", "pun", "down")
    link("pun", "mum", "down")

    # /internal is blocked on both sides while down
    h = {"X-Region": "pun", "X-Peer-Token": "t"}
    assert httpx.get(URL["mum"] + "/internal/v1/sync/summary", headers=h).status_code == 503
    h = {"X-Region": "mum", "X-Peer-Token": "t"}
    assert httpx.get(URL["pun"] + "/internal/v1/sync/summary", headers=h).status_code == 503

    # both sides keep accepting writes
    assert httpx.patch(URL["mum"] + "/v1/reports/R-mum-1", headers=KEY, timeout=3,
                       json={"field": "status", "value": "assigned"}).status_code == 200
    assert httpx.patch(URL["pun"] + "/v1/reports/R-mum-1", headers=KEY, timeout=3,
                       json={"field": "status", "value": "closed"}).status_code == 200
    until(lambda: status("mum")["level"] == "ISOLATED" and status("pun")["level"] == "ISOLATED", 8)
    assert status("mum")["state_hash"] != status("pun")["state_hash"]  # nothing crossed

    link("mum", "pun", "up")
    link("pun", "mum", "up")
    until(lambda: status("mum")["event_digest"] == status("pun")["event_digest"], 8)
    a = httpx.get(URL["mum"] + "/v1/reports/R-mum-1").json()
    b = httpx.get(URL["pun"] + "/v1/reports/R-mum-1").json()
    assert a["conflicts"] == b["conflicts"] and len(a["conflicts"]) == 1
    assert a["state"] == b["state"]
    assert status("mum")["state_hash"] == status("pun")["state_hash"]
    until(lambda: status("mum")["level"] == "HEALTHY" and status("pun")["level"] == "HEALTHY", 8)
