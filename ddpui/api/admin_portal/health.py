from django.utils import timezone
from ninja import Router

from ddpui.permissions.admin_permissions import require_platform_admin
from ddpui.services.admin.monitoring_service import MonitoringService

health_router = Router()


@health_router.get("/health/")
@require_platform_admin
def admin_health(request):
    return {
        "api": "healthy",
        "database": MonitoringService.db_health(),
        "warehouses": MonitoringService.warehouse_health_rows(),
        "timestamp": timezone.now(),
    }
