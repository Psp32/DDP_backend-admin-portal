from unittest.mock import Mock, patch

import pytest
from ninja.errors import HttpError

from django.contrib.auth.models import User

from ddpui.api.admin_portal.organizations import create_org, delete_org, list_orgs
from ddpui.api.admin_portal.roles import list_roles
from ddpui.api.admin_portal.health import list_audit_logs, admin_health
from ddpui.api.admin_portal.organizations import OrgCreateSchema
from ddpui.models.admin.audit_log import AuditLog
from ddpui.models.org import Org
from ddpui.models.org_user import OrgUser, UserAttributes
from ddpui.models.role_based_access import Role
from ddpui.tests.api_tests.test_user_org_api import seed_db

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_request():
    user = User.objects.create(username="platform-admin", email="platform-admin@example.com")
    role = Role.objects.filter(slug="super-admin").first()
    org = Org.objects.create(name="seed-org", slug="seed-org")
    orguser = OrgUser.objects.create(user=user, org=org, new_role=role)
    UserAttributes.objects.create(user=user, is_platform_admin=True)

    request = Mock()
    request.user = user
    request.orguser = orguser
    return request


@pytest.fixture
def viewer_request():
    user = User.objects.create(username="viewer", email="viewer@example.com")
    role = Role.objects.filter(slug="guest").first()
    org = Org.objects.create(name="viewer-org", slug="viewer-org")
    orguser = OrgUser.objects.create(user=user, org=org, new_role=role)
    UserAttributes.objects.create(user=user, is_platform_admin=False)

    request = Mock()
    request.user = user
    request.orguser = orguser
    return request


def test_org_crud_happy_path(seed_db, admin_request):
    payload = OrgCreateSchema(name="admin-new-org", slug="admin-new-org", website="https://example.org")
    created = create_org(admin_request, payload)
    assert created["name"] == payload.name

    listing = list_orgs(admin_request)
    assert listing["total_rows"] >= 1

    deleted = delete_org(admin_request, created["id"])
    assert deleted["success"] == 1


def test_org_create_auth_failure(seed_db, viewer_request):
    payload = OrgCreateSchema(name="forbidden-org", slug="forbidden-org", website=None)
    with pytest.raises(HttpError) as exc:
        create_org(viewer_request, payload)
    assert exc.value.status_code == 403


def test_rbac_guard_viewer_cannot_access_roles(seed_db, viewer_request):
    with pytest.raises(HttpError) as exc:
        list_roles(viewer_request)
    assert exc.value.status_code == 403


def test_audit_log_query(seed_db, admin_request):
    AuditLog.objects.create(actor=admin_request.user, action="GET /api/v1/admin/health/")
    response = list_audit_logs(admin_request)
    assert response["total_rows"] >= 1


def test_health_endpoint(seed_db, admin_request):
    with patch("ddpui.services.admin.monitoring_service.MonitoringService.db_health", return_value="healthy"):
        with patch(
            "ddpui.services.admin.monitoring_service.MonitoringService.warehouse_health_rows",
            return_value=[{"org": "seed-org", "status": "healthy", "latency_ms": 1}],
        ):
            response = admin_health(admin_request)
            assert response["api"] == "healthy"
            assert response["database"] == "healthy"
