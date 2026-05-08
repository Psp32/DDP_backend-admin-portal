import time

from ddpui.models.org import OrgWarehouse
from ddpui.utils.secretsmanager import retrieve_warehouse_credentials
from ddpui.utils.warehouse.client.warehouse_factory import WarehouseFactory


class AdminWarehouseService:
    @staticmethod
    def check_health(org_warehouse: OrgWarehouse):
        started = time.perf_counter()
        try:
            credentials = retrieve_warehouse_credentials(org_warehouse)
            client = WarehouseFactory.connect(credentials, wtype=org_warehouse.wtype)
            client.run_query("SELECT 1")
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {"status": "healthy", "latency_ms": latency_ms}
        except Exception:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {"status": "unreachable", "latency_ms": latency_ms}
