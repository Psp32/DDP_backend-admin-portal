# Dalgo Admin Portal — Backend Proposal (C4GT 2025)


## Overview

This proposal implements the foundational backend architecture for the Dalgo Admin Portal —
a centralized management interface for platform administrators to manage organizations,
users, roles, warehouse health, and platform observability.

The implementation is built entirely within the existing Django + Django Ninja architecture,
reusing existing models, auth patterns, and conventions without breaking any existing APIs.

---

## 1. Endpoints Implemented

### Organizations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/organizations/` | List orgs with pagination and search |
| POST | `/api/v1/admin/organizations/` | Create organization |
| GET | `/api/v1/admin/organizations/{id}/` | Get single organization |
| PATCH | `/api/v1/admin/organizations/{id}/` | Update organization |
| DELETE | `/api/v1/admin/organizations/{id}/` | Delete organization |
| POST | `/api/v1/admin/organizations/bulk/` | Bulk activate/deactivate |

### Roles
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/roles/` | List all roles |
| POST | `/api/v1/admin/roles/` | Create role |
| PATCH | `/api/v1/admin/roles/{id}/` | Update role |
| DELETE | `/api/v1/admin/roles/{id}/` | Delete role |

### Invitations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/admin/invitations/` | Send invitation |
| GET | `/api/v1/admin/invitations/` | List invitations |
| DELETE | `/api/v1/admin/invitations/{id}/` | Cancel invitation |
| POST | `/api/v1/admin/invitations/{id}/resend/` | Resend invitation |

### Monitoring & Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/warehouses/health/` | Warehouse health per org |
| GET | `/api/v1/admin/health/` | Full platform health summary |
| GET | `/api/v1/admin/audit-logs/` | Audit log listing with filters |

---

## 2. Architecture

### Folder Structure
```
ddpui/
├── api/
│   └── admin_portal/          # Admin-specific route handlers
│       ├── organizations.py
│       ├── roles.py
│       ├── invitations.py
│       ├── warehouses.py
│       └── health.py
├── models/
│   └── admin/                 # New models only, no existing model changes
│       ├── audit_log.py       # AuditLog
│       └── invitation.py      # AdminInvitation
├── services/
│   └── admin/                 # Business logic, decoupled from routes
│       ├── org_service.py
│       ├── warehouse_service.py
│       └── monitoring_service.py
├── permissions/
│   └── admin_permissions.py   # require_platform_admin, require_admin_role
├── middleware/
│   └── admin_audit_middleware.py  # Auto audit logging
└── migrations/
└── 0158_admin_portal_models.py
```

### Design Principles

- **Zero regression** — no existing models, APIs, or routes were modified
- **Reuse first** — `Org`, `OrgWarehouse`, `Role`, `RolePermission`, `UserAttributes` all reused as-is
- **Isolated modules** — all admin code lives in dedicated subpackages
- **Consistent conventions** — Django Ninja routers, `HttpError` semantics, PEP8/Black formatting throughout

---

## 3. Authentication & Authorization

### Authentication
All admin endpoints use the existing `CustomJwtAuthMiddleware` already mounted on the main
Ninja API. No new auth system was introduced.

### Platform Admin Guard
A `require_platform_admin` decorator checks `UserAttributes.is_platform_admin` on every
request to `/api/v1/admin/*`. Non-admin users receive a `403 Forbidden` response.

### Role-Level Guard
`require_admin_role([...])` provides finer-grained control for role-sensitive actions,
aligned with existing role slugs (`super-admin`, `account-manager`, etc.).

---

## 4. Audit Logging

### Approach — Automatic Middleware (not manual per-endpoint)

`AdminAuditLogMiddleware` intercepts all requests to `/api/v1/admin/*` and automatically
writes an `AuditLog` record after each response. Developers do not need to add logging calls
manually — every admin action is captured by default.

### What is captured
- Actor (user email)
- Action (HTTP method + endpoint path)
- Target type and target ID (parsed from URL)
- HTTP status code
- Source IP address
- Timestamp

---

## 5. Database Models & Migration

### New Models

**AuditLog**
```
actor (FK → User)
action (CharField)
target_type (CharField)
target_id (CharField)
metadata (JSONField)
ip_address (GenericIPAddressField)
timestamp (DateTimeField, indexed)
```

**AdminInvitation**
```
email (EmailField)
organization (FK → Org)
role (CharField)
token (UUIDField, unique)
expires_at (DateTimeField)
status (CharField: pending/accepted/expired/cancelled)
created_by (FK → User)
created_at (DateTimeField)
```

### Why AdminInvitation instead of reusing existing Invitation
The existing `Invitation` model serves the standard user onboarding flow with different
fields and status semantics. Rather than modifying a production model and risking
regressions, a dedicated `AdminInvitation` model was introduced for admin-scoped invitations.

### Migration
`0158_admin_portal_models.py` — creates both tables with appropriate indexes on
`AuditLog.timestamp` and `AuditLog.action` for efficient log querying.

---

## 6. Warehouse Health Checks

`AdminWarehouseService` checks warehouse connectivity by:
1. Building a warehouse client using the existing warehouse config
2. Executing a `SELECT 1` probe query
3. Measuring round-trip latency in milliseconds
4. Returning `healthy / degraded / unreachable` status

The `/api/v1/admin/health/` endpoint aggregates:
- Django DB connection status
- All warehouse connection statuses per org
- Overall API server status

---

## 7. Future Roadmap (Post-Selection)
```
Phase 2 — Core Management
- Superset instance management endpoints
- Warehouse credential rotation and key management
- Full invitation acceptance workflow with email sending

Phase 3 — Monitoring
- Real pipeline/job execution monitoring (Prefect integration)
- Pipeline failure rate analytics
- Emergency pipeline controls (pause/resume/cancel)
- Real-time metrics via WebSocket or polling

Phase 4 — Advanced
- Feature flag management API (scoped per org)
- A/B testing support infrastructure
- Advanced bulk operations
- Resource utilization metrics and alerting
```
---

## 8. Testing

Tests located at: `ddpui/tests/api_tests/test_admin_portal_api.py`

Coverage includes:
- Org CRUD (happy path, validation errors, auth failures)
- RBAC guard (admin access granted, non-admin blocked with 403)
- Audit log auto-capture via middleware
- Platform health endpoint response structure

**Note:** Full test suite requires `SECRET_KEY` and DB credentials set in environment.
Run with: `uv run pytest ddpui/tests/api_tests/test_admin_portal_api.py -v`
