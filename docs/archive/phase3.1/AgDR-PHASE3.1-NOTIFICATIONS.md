# AgDR: Phase 3.1 Notifications

**Status:** Approved for Build  
**Author:** Hisham (Tech Lead)  
**Reviewer:** Tariq (Solution Architect)  
**Date:** 2026-06-06

## Context

Phase 3 MVP delivers WebSocket notifications in-memory on the frontend. Admins cannot action WO requests from the bell; unread counts vanish on refresh.

## Decision

1. **Persist notifications** in PostgreSQL (`notifications` table).
2. **WebSocket remains the real-time delivery channel**; on connect, client hydrates from REST.
3. **Deep-link contract** encoded in `payload_json.action`:

| type | action | Target route |
|------|--------|--------------|
| `work_order.requested` | `review_request` | `/work-orders?view=requests&review={woId}` |
| `work_order.status_changed` | `view_work_order` | `/work-orders/{woId}` or `?view=my_requests` |

## Data model

```sql
notifications (
  id UUID PK,
  tenant_id UUID FK,
  user_id UUID FK,
  type VARCHAR(64),
  title VARCHAR(512),
  payload_json JSONB,
  read_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ
)
```

Index: `(user_id, read_at, created_at DESC)`.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/notifications` | List last 50 for current user |
| PATCH | `/notifications/{id}/read` | Mark read |
| POST | `/notifications/read-all` | Mark all read |

## NFRs

- Unread count survives refresh
- p95 delivery < 2s on LAN demo
- Tenant isolation on all queries

## Out of scope (Phase 4)

- Push notifications (mobile)
- Email digest of unread notifications
- Dedicated notification preferences UI

## Alternatives considered

| Option | Rejected because |
|--------|------------------|
| Keep in-memory only | Fails refresh + audit requirements |
| Email-only | Too slow for request workflow |
