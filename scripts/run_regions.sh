#!/usr/bin/env bash
# Starts mum :8001 and pun :8002 (data/mum.db, data/pun.db). Ctrl+C stops both.
cd "$(dirname "$0")/.." && exec python scripts/run_regions.py "$@"
