from typing import Optional

from ninja import Router, Schema
from ninja.errors import HttpError

from ddpui.models.org import Org
from ddpui.permissions.admin_permissions import require_platform_admin
from ddpui.services.admin.org_service import AdminOrgService

organizations_router = Router()


class OrgCreateSchema(Schema):
    name: str
    slug: str
    website: Optional[str] = None


class OrgUpdateSchema(Schema):
    name: Optional[str] = None
    website: Optional[str] = None


class BulkOrgActionSchema(Schema):
    org_ids: list[int]
    active: bool


@organizations_router.get("/organizations/")
@require_platform_admin
def list_orgs(request, page: int = 1, page_size: int = 20, search: str = None, status: str = None):
    queryset = AdminOrgService.list_orgs(search, status)
    offset = max((page - 1) * page_size, 0)
    rows = queryset[offset : offset + page_size]
    return {
        "page": page,
        "page_size": page_size,
        "total_rows": queryset.count(),
        "rows": [{"id": org.id, "name": org.name, "slug": org.slug, "website": org.website} for org in rows],
    }


@organizations_router.post("/organizations/")
@require_platform_admin
def create_org(request, payload: OrgCreateSchema):
    org = Org.objects.create(name=payload.name, slug=payload.slug, website=payload.website)
    return {"id": org.id, "name": org.name, "slug": org.slug, "website": org.website}


@organizations_router.get("/organizations/{id}/")
@require_platform_admin
def get_org(request, id: int):
    org = Org.objects.filter(id=id).first()
    if not org:
        raise HttpError(404, "Organization not found")
    return {"id": org.id, "name": org.name, "slug": org.slug, "website": org.website}


@organizations_router.patch("/organizations/{id}/")
@require_platform_admin
def update_org(request, id: int, payload: OrgUpdateSchema):
    org = Org.objects.filter(id=id).first()
    if not org:
        raise HttpError(404, "Organization not found")
    if payload.name is not None:
        org.name = payload.name
    if payload.website is not None:
        org.website = payload.website
    org.save()
    return {"id": org.id, "name": org.name, "slug": org.slug, "website": org.website}


@organizations_router.delete("/organizations/{id}/")
@require_platform_admin
def delete_org(request, id: int):
    org = Org.objects.filter(id=id).first()
    if not org:
        raise HttpError(404, "Organization not found")
    org.delete()
    return {"success": 1}


@organizations_router.post("/organizations/bulk/")
@require_platform_admin
def bulk_org_action(request, payload: BulkOrgActionSchema):
    # Org has no active flag yet, so return IDs for compatibility.
    found_ids = list(Org.objects.filter(id__in=payload.org_ids).values_list("id", flat=True))
    return {"success": 1, "org_ids": found_ids, "active": payload.active}
