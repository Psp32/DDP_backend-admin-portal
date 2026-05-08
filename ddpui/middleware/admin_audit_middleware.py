from ddpui.models.admin.audit_log import AuditLog


class AdminAuditLogMiddleware:
    """Capture admin API calls into audit logs."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith("/api/v1/admin/"):
            actor = getattr(request, "user", None)
            action = f"{request.method} {request.path}"
            target_id = None
            target_type = None
            if getattr(request, "resolver_match", None):
                kwargs = request.resolver_match.kwargs or {}
                if "id" in kwargs:
                    target_id = str(kwargs["id"])
                elif "invitation_id" in kwargs:
                    target_id = str(kwargs["invitation_id"])
                target_type = request.path.strip("/").split("/")[-1]

            AuditLog.objects.create(
                actor=actor if actor and actor.is_authenticated else None,
                action=action,
                target_type=target_type,
                target_id=target_id,
                metadata={"status_code": response.status_code},
                ip_address=request.META.get("REMOTE_ADDR"),
            )

        return response
