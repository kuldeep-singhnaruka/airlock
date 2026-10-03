#!/usr/bin/env bash
set -euo pipefail

BASE="${API_BASE_URL:-http://127.0.0.1:8000}"
TOKEN="$(
  curl -sS -X POST "$BASE/v1/auth/token" \
    -H 'content-type: application/json' \
    -d '{"username":"demo","password":"demo-pass"}' \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
)"

echo "health:"
curl -sS "$BASE/health"
echo
echo "chat with tools:"
curl -sS -X POST "$BASE/v1/chat" \
  -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"How many tokens are in hello airlock?"}],"enable_tools":true}'
echo
echo "extract:"
curl -sS -X POST "$BASE/v1/extract" \
  -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"text":"Please fix the login bug today, this is urgent","schema_name":"task"}'
echo
echo "usage:"
curl -sS "$BASE/v1/usage" -H "authorization: Bearer $TOKEN"
echo
