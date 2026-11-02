#!/usr/bin/env bash
# Smoke the always-on pilot: health → platform login → packages → provision company → company login.
#
# Usage:
#   BASE_URL=https://demo.orbittech.co ./deploy/pilot/smoke-pilot.sh
#   BASE_URL=http://127.0.0.1:8080 SUPER_EMAIL=super@demo.com SUPER_PASSWORD=super123 \
#     ./deploy/pilot/smoke-pilot.sh
#
# Exit 0 on success. Prints the provisioned company admin credentials.

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8080}"
BASE_URL="${BASE_URL%/}"
API="${BASE_URL}/api/v1"
SUPER_EMAIL="${SUPER_EMAIL:-super@demo.com}"
SUPER_PASSWORD="${SUPER_PASSWORD:-super123}"
SUFFIX="${RANDOM:-$RANDOM}"
COMPANY_NAME="${COMPANY_NAME:-Smoke Co ${SUFFIX}}"
ADMIN_EMAIL="${ADMIN_EMAIL:-smoke.admin.${SUFFIX}@example.com}"
ADMIN_NAME="${ADMIN_NAME:-Smoke Admin}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing dependency: $1" >&2; exit 1; }; }
need curl

# Prefer PYTHON, then repo venv, then python/python3 (skip Windows Store stubs).
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
_py_ok() { "$1" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >/dev/null 2>&1; }
PY=""
if [ -n "${PYTHON:-}" ] && _py_ok "$PYTHON"; then
  PY="$PYTHON"
elif [ -x "$ROOT/.venv/Scripts/python.exe" ] && _py_ok "$ROOT/.venv/Scripts/python.exe"; then
  PY="$ROOT/.venv/Scripts/python.exe"
elif [ -x "$ROOT/.venv/bin/python" ] && _py_ok "$ROOT/.venv/bin/python"; then
  PY="$ROOT/.venv/bin/python"
elif command -v python >/dev/null 2>&1 && _py_ok python; then
  PY=python
elif command -v python3 >/dev/null 2>&1 && _py_ok python3; then
  PY=python3
else
  echo "missing Python 3.9+ (set PYTHON= or create .venv)" >&2
  exit 1
fi

echo "==> Health ${API}/health"
curl -fsS --max-time 30 "${API}/health" | "$PY" -c 'import sys,json; d=json.load(sys.stdin); assert d.get("status")=="ok", d; print(d)'

echo "==> Login platform admin ${SUPER_EMAIL}"
LOGIN=$(curl -fsS --max-time 30 -X POST "${API}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"identifier\":\"${SUPER_EMAIL}\",\"password\":\"${SUPER_PASSWORD}\"}")
TOKEN=$(printf '%s' "$LOGIN" | "$PY" -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

echo "==> List active packages"
PKGS=$(curl -fsS --max-time 30 "${API}/platform/packages?active_only=true" -H "Authorization: Bearer ${TOKEN}")
PACKAGE_ID=$(printf '%s' "$PKGS" | "$PY" -c '
import sys, json
pkgs = json.load(sys.stdin)
assert pkgs, "no active packages — run pilot seed / platform bootstrap"
print(pkgs[0]["id"])
')
echo "    package_id=${PACKAGE_ID}"

echo "==> Provision maintenance company: ${COMPANY_NAME}"
PROV=$(curl -fsS --max-time 30 -X POST "${API}/platform/tenants" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"tenant_name\":\"${COMPANY_NAME}\",\"admin_email\":\"${ADMIN_EMAIL}\",\"admin_full_name\":\"${ADMIN_NAME}\",\"package_id\":\"${PACKAGE_ID}\"}")
ADMIN_PASSWORD=$(printf '%s' "$PROV" | "$PY" -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("tenant_id"), d
assert d.get("initial_password"), "expected auto-generated initial_password"
print("    tenant_id=", d["tenant_id"], file=sys.stderr)
print("    admin_user_id=", d["admin_user_id"], file=sys.stderr)
print("    initial_password=", d["initial_password"], file=sys.stderr)
print(d["initial_password"])
')

echo "==> Company admin login ${ADMIN_EMAIL}"
curl -fsS --max-time 30 -X POST "${API}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"identifier\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}" \
  | "$PY" -c 'import sys,json; d=json.load(sys.stdin); assert d.get("access_token"), d; print("    company login OK")'

echo "==> Smoke OK (${BASE_URL})"
