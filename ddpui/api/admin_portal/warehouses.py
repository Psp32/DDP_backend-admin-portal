from ninja import Router

from ddpui.models.org import OrgWarehouse
from ddpui.permissions.admin_permissions import require_platform_admin
from ddpui.services.admin.warehouse_service import AdminWarehouseService

warehouses_router = Router()


@warehouses_router.get("/warehouses/health/")
@require_platform_admin
def warehouses_health(request):
    rows = []
    for org_warehouse in OrgWarehouse.objects.select_related("org").all():
        health = AdminWarehouseService.check_health(org_warehouse)
        rows.append(
            {
                "org": org_warehouse.org.slug or org_warehouse.org.name,
                "warehouse_type": org_warehouse.wtype,
                "status": health["status"],
                "latency_ms": health["latency_ms"],
            }
        )
    return {"warehouses": rows}
