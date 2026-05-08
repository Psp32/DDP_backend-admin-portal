from typing import Optional

from ninja import Router, Schema
from ninja.errors import HttpError

from ddpui.models.role_based_access import Role, Permission, RolePermission
from ddpui.permissions.admin_permissions import require_platform_admin, require_admin_role

roles_router = Router()


class RoleCreateSchema(Schema):
    name: str
    slug: str
    level: int = 1
    permission_slugs: list[str] = []


class RolePatchSchema(Schema):
    name: Optional[str] = None
    level: Optional[int] = None
    permission_slugs: Optional[list[str]] = None


@roles_router.get("/roles/")
@require_platform_admin
def list_roles(request):
    roles = Role.objects.all().order_by("-level")
    return [
        {
            "id": role.id,
            "uuid": str(role.uuid),
            "name": role.name,
            "slug": role.slug,
            "level": role.level,
            "permissions": list(
                RolePermission.objects.filter(role=role).values_list("permission__slug", flat=True)
            ),
        }
        for role in roles
    ]


@roles_router.post("/roles/")
@require_platform_admin
@require_admin_role(["super-admin", "account-manager"])
def create_role(request, payload: RoleCreateSchema):
    role = Role.objects.create(name=payload.name, slug=payload.slug, level=payload.level)
    if payload.permission_slugs:
        permissions = Permission.objects.filter(slug__in=payload.permission_slugs)
        RolePermission.objects.bulk_create(
            [RolePermission(role=role, permission=permission) for permission in permissions]
        )
    return {"id": role.id, "uuid": str(role.uuid), "name": role.name, "slug": role.slug}


@roles_router.patch("/roles/{id}/")
@require_platform_admin
@require_admin_role(["super-admin", "account-manager"])
def patch_role(request, id: int, payload: RolePatchSchema):
    role = Role.objects.filter(id=id).first()
    if not role:
        raise HttpError(404, "Role not found")

    if payload.name is not None:
        role.name = payload.name
    if payload.level is not None:
        role.level = payload.level
    role.save()

    if payload.permission_slugs is not None:
        RolePermission.objects.filter(role=role).delete()
        permissions = Permission.objects.filter(slug__in=payload.permission_slugs)
        RolePermission.objects.bulk_create(
            [RolePermission(role=role, permission=permission) for permission in permissions]
        )

    return {"success": 1}


@roles_router.delete("/roles/{id}/")
@require_platform_admin
@require_admin_role(["super-admin"])
def delete_role(request, id: int):
    role = Role.objects.filter(id=id).first()
    if not role:
        raise HttpError(404, "Role not found")
    role.delete()
    return {"success": 1}
