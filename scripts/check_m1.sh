#!/usr/bin/env bash
# M1 / M1b evidence script (PDF 1 section 8). Start the regions first:
#   python scripts/run_regions.py        # in another terminal
# Needs curl and jq. Run on a fresh data/ for clean ids (rm -rf data).
set -u
K=(-H "X-API-Key: dev-officer" -H "Content-Type: application/json")
M=localhost:8001; P=localhost:8002
say() { printf '\n== %s\n' "$*"; }

say "M1: write on mum (expect 201 + event_id)"
RID=$(curl -s "${K[@]}" -X POST $M/v1/reports \
  -d '{"title":"Wall collapse, Kurla","category":"collapse","severity":3}' | tee /dev/stderr | jq -r .report.report_id)
sleep 3
say "report on pune (expect $RID)";  curl -s $P/v1/reports | jq '.[].report_id'
say "heads equal on both";           curl -s $M/v1/status | jq -c .heads; curl -s $P/v1/status | jq -c .heads
say "digest equal";                  curl -s $M/v1/status | jq -r .event_digest; curl -s $P/v1/status | jq -r .event_digest

say "M1b: cut both ways"
curl -s "${K[@]}" -X POST $M/admin/links/pun -d '{"mode":"down"}'
curl -s "${K[@]}" -X POST $P/admin/links/mum -d '{"mode":"down"}'
say "internal is 503 (expect 503 503)"
curl -s -o /dev/null -w '%{http_code} ' -H "X-Region: pun" -H "X-Peer-Token: change-me" $M/internal/v1/sync/summary
curl -s -o /dev/null -w '%{http_code}\n' -H "X-Region: mum" -H "X-Peer-Token: change-me" $P/internal/v1/sync/summary
say "both sides write the same field (expect 200 200)"
curl -s -o /dev/null -w '%{http_code} ' "${K[@]}" -X PATCH $M/v1/reports/$RID -d '{"field":"severity","value":5}'
curl -s -o /dev/null -w '%{http_code}\n' "${K[@]}" -X PATCH $P/v1/reports/$RID -d '{"field":"severity","value":4}'

say "heal both, wait 4 s"
curl -s "${K[@]}" -X POST $M/admin/links/pun -d '{"mode":"up"}' >/dev/null
curl -s "${K[@]}" -X POST $P/admin/links/mum -d '{"mode":"up"}' >/dev/null
sleep 4
say "conflicts on mum"; curl -s $M/v1/reports/$RID | jq -c '.conflicts'
say "conflicts on pun"; curl -s $P/v1/reports/$RID | jq -c '.conflicts'
say "state_hash equal"; curl -s $M/v1/status | jq -r .state_hash; curl -s $P/v1/status | jq -r .state_hash
