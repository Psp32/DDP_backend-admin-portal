from django.db import connection

from ddpui.models.org import OrgWarehouse
from ddpui.services.admin.warehouse_service import AdminWarehouseService


class MonitoringService:
    @staticmethod
    def db_health():
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return "healthy"
        except Exception:
            return "unreachable"

    @staticmethod
    def warehouse_health_rows():
        rows = []
        for org_warehouse in OrgWarehouse.objects.select_related("org").all():
            health = AdminWarehouseService.check_health(org_warehouse)
            rows.append(
                {
                    "org": org_warehouse.org.slug or org_warehouse.org.name,
                    "status": health["status"],
                    "latency_ms": health["latency_ms"],
                }
            )
        return rows
