from datetime import timedelta

from ninja import Router, Schema
from ninja.errors import HttpError
from django.utils import timezone

from ddpui.models.admin.invitation import AdminInvitation
from ddpui.models.org import Org
from ddpui.models.role_based_access import Role
from ddpui.permissions.admin_permissions import require_platform_admin

invitations_router = Router()


class InvitationCreateSchema(Schema):
    email: str
    organization_id: int
    role_id: int
    expires_in_days: int = 7


@invitations_router.post("/invitations/")
@require_platform_admin
def send_invitation(request, payload: InvitationCreateSchema):
    org = Org.objects.filter(id=payload.organization_id).first()
    role = Role.objects.filter(id=payload.role_id).first()
    if not org or not role:
        raise HttpError(400, "Invalid organization or role")
    invitation = AdminInvitation.objects.create(
        email=payload.email.lower().strip(),
        organization=org,
        role=role,
        expires_at=timezone.now() + timedelta(days=payload.expires_in_days),
    )
    return {"id": invitation.id, "token": str(invitation.token), "status": invitation.status}


@invitations_router.get("/invitations/")
@require_platform_admin
def list_invitations(request, page: int = 1, page_size: int = 20, status: str = None):
    queryset = AdminInvitation.objects.select_related("organization", "role").order_by("-id")
    if status:
        queryset = queryset.filter(status=status)
    offset = max((page - 1) * page_size, 0)
    rows = queryset[offset : offset + page_size]
    return {
        "page": page,
        "page_size": page_size,
        "total_rows": queryset.count(),
        "rows": [
            {
                "id": invitation.id,
                "email": invitation.email,
                "organization_id": invitation.organization_id,
                "role_id": invitation.role_id,
                "token": str(invitation.token),
                "expires_at": invitation.expires_at,
                "status": invitation.status,
            }
            for invitation in rows
        ],
    }


@invitations_router.delete("/invitations/{id}/")
@require_platform_admin
def cancel_invitation(request, id: int):
    invitation = AdminInvitation.objects.filter(id=id).first()
    if not invitation:
        raise HttpError(404, "Invitation not found")
    invitation.status = AdminInvitation.STATUS_CANCELLED
    invitation.save(update_fields=["status", "updated_at"])
    return {"success": 1}


@invitations_router.post("/invitations/{id}/resend/")
@require_platform_admin
def resend_invitation(request, id: int):
    invitation = AdminInvitation.objects.filter(id=id).first()
    if not invitation:
        raise HttpError(404, "Invitation not found")
    invitation.expires_at = timezone.now() + timedelta(days=7)
    invitation.status = AdminInvitation.STATUS_PENDING
    invitation.save(update_fields=["expires_at", "status", "updated_at"])
    return {"success": 1, "token": str(invitation.token)}
