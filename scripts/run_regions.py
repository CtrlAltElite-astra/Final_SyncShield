"""Start all regions, one process each.   python scripts/run_regions.py [mum pun]

Ctrl+C stops them all. Data lives in data/<region>.db and survives restarts.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from run_one import PORTS, spawn  # noqa: E402

if __name__ == "__main__":
    regions = sys.argv[1:] or os.environ.get("REGIONS", "mum,pun").split(",")
    procs = {r: spawn(r, regions) for r in regions}
    print("Regions up: " + ", ".join(f"{r} http://127.0.0.1:{PORTS[r]}" for r in regions))
    print("Dashboard: cd dashboard && npm run dev   |   Ctrl+C to stop")
    try:
        while all(p.poll() is None for p in procs.values()):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for p in procs.values():
            if p.poll() is None:
                p.terminate()
