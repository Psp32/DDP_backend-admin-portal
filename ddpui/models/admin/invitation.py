import uuid

from django.db import models
from django.utils import timezone

from ddpui.models.org import Org
from ddpui.models.role_based_access import Role


class AdminInvitation(models.Model):
    """Invitation model for admin portal workflows."""

    STATUS_PENDING = "pending"
    STATUS_CANCELLED = "cancelled"
    STATUS_ACCEPTED = "accepted"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = (
        (STATUS_PENDING, STATUS_PENDING),
        (STATUS_CANCELLED, STATUS_CANCELLED),
        (STATUS_ACCEPTED, STATUS_ACCEPTED),
        (STATUS_EXPIRED, STATUS_EXPIRED),
    )

    email = models.CharField(max_length=254)
    organization = models.ForeignKey(Org, on_delete=models.CASCADE, related_name="admin_invitations")
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

