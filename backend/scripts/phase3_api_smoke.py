"""Quick Phase 3 API smoke checks (FE-07/FE-08 backend support)."""
import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"


def login(email: str, password: str) -> str:
    req = urllib.request.Request(
        BASE + "/auth/login",
        data=json.dumps({"identifier": email, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)["access_token"]


def api(token: str, path: str, method: str = "GET", body: dict | None = None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = raw
        return e.code, payload


def main() -> int:
    results: list[tuple[str, bool]] = []

    client_t = login("client@demo.com", "client123")
    st, clients = api(client_t, "/clients")
    results.append(("client_admin clients scoped to one", st == 200 and len(clients) == 1))

    st, sites = api(client_t, "/sites")
    site_id = sites[0]["id"]
    client_id = sites[0]["client_id"]
    st, wo = api(
        client_t,
        "/work-orders/request",
        "POST",
        {
            "title": "Smoke test request",
            "description": "Phase3 signoff",
            "urgency": "normal",
            "client_id": client_id,
            "site_id": site_id,
            "source": "request",
            "category": "general",
        },
    )
    results.append(("client_admin request WO", st == 200 and wo.get("status") == "requested"))
    wo_id = wo["id"]

    admin_t = login("admin@demo.com", "admin123")
    st, listed = api(admin_t, "/work-orders?status=requested")
    ids = [x["id"] for x in listed.get("data", [])]
    results.append(("admin lists requested WOs", st == 200 and wo_id in ids))

    st, approved = api(admin_t, f"/work-orders/{wo_id}/approve-request", "POST", {})
    results.append(("admin approve request", st == 200 and approved.get("status") == "created"))

    st, hist = api(admin_t, f"/work-orders/{wo_id}/history")
    results.append(
        (
            "approve recorded as status transition",
            st == 200
            and any(
                h.get("action") == "update"
                and h.get("before_json", {}).get("status") == "requested"
                and h.get("after_json", {}).get("status") == "created"
                for h in hist
            ),
        )
    )

    st, wo2 = api(
        client_t,
        "/work-orders/request",
        "POST",
        {
            "title": "Decline test",
            "description": "x",
            "urgency": "normal",
            "client_id": client_id,
            "site_id": site_id,
            "source": "request",
            "category": "general",
        },
    )
    wo2_id = wo2["id"]
    st, _ = api(admin_t, f"/work-orders/{wo2_id}/decline-request", "POST", {"reason": ""})
    results.append(("decline empty reason rejected", st == 422))

    st, declined = api(
        admin_t, f"/work-orders/{wo2_id}/decline-request", "POST", {"reason": "Not in scope"}
    )
    results.append(("decline with reason", st == 200 and declined.get("status") == "declined"))

    site_t = login("site@demo.com", "site123")
    st, sm_clients = api(site_t, "/clients")
    results.append(("site_manager clients scoped", st == 200 and len(sm_clients) == 1))

    passed = 0
    for name, ok in results:
        print(("PASS" if ok else "FAIL") + ": " + name)
        if ok:
            passed += 1
    print(f"TOTAL {passed}/{len(results)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
