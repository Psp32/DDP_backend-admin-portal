from ninja import Router

from ddpui.models.admin.audit_log import AuditLog
from ddpui.permissions.admin_permissions import require_platform_admin

audit_logs_router = Router()


@audit_logs_router.get("/audit-logs/")
@require_platform_admin
def list_audit_logs(
    request,
    page: int = 1,
    page_size: int = 20,
    actor_id: int = None,
    action: str = None,
    start_date: str = None,
    end_date: str = None,
):
    queryset = AuditLog.objects.select_related("actor").all().order_by("-timestamp")
    if actor_id:
        queryset = queryset.filter(actor_id=actor_id)
    if action:
        queryset = queryset.filter(action__icontains=action)
    if start_date:
        queryset = queryset.filter(timestamp__gte=start_date)
    if end_date:
        queryset = queryset.filter(timestamp__lte=end_date)

    offset = max((page - 1) * page_size, 0)
    rows = queryset[offset : offset + page_size]
    return {
        "page": page,
        "page_size": page_size,
        "total_rows": queryset.count(),
        "rows": [
            {
                "id": row.id,
                "actor_id": row.actor_id,
                "action": row.action,
                "target_type": row.target_type,
                "target_id": row.target_id,
                "metadata": row.metadata,
                "timestamp": row.timestamp,
                "ip_address": row.ip_address,
            }
            for row in rows
        ],
    }
