# Owners and change protocol

| lane | person | owns |
|---|---|---|
| A | Akshit | `contracts/`, `region/main.py`, `store.py`, `auth.py`, `migrations/`, `api/`, `trust/`, `requirements.txt`, `tests/api/` |
| B | Rahil | `region/engine/`, `tests/engine/`, `tests/fuzz/`, `docs/conflict-policy.md` |
| C | Miti | `dashboard/` (incl. `package.json`), `docs/` (except conflict-policy), `README.md` |
| D | Simrit | `region/sync/`, `region/config.py`, `.env.example`, `scripts/`, `tests/integration/` |

## Rules

- Branches `a/…`, `b/…`, `c/…`, `d/…`; pull `main` before each block; small PRs, one reviewer who explains it back.
- Need a change in someone else's file? Ask the owner in chat; the owner commits it.
- `contracts/*` and `migrations/*`: additive only (new optional fields), PR labelled `contract`, line in `contracts/CHANGELOG.md`.
- Any rule change in `engine/policy.py` bumps `POLICY_VERSION` and its unit test in the same PR.
- Commit under your own GitHub identity. No force-push. No code copied from reference repositories.
- One Uvicorn worker per region. A write never calls a peer.

## Where each lane starts (PDF 2, Phase 1)

- **A:** SET validation for all fields, roles, history endpoint, kill -9 test, partner adapter interface.
- **B:** `policy.py` v1 + `derive` v1, `priority.classify`, `CLOSE_VS_NEW_INFO`, `docs/conflict-policy.md`.
- **C:** report detail drawer, level banner, per-report badges, link matrix for 3 pairs.
- **D:** push fast path, gap-safe watermark tests, peer levels, scenario scripts, `mock_partner.py`.
