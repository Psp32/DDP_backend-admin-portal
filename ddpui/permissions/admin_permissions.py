from functools import wraps

from ninja.errors import HttpError

from ddpui.models.org_user import UserAttributes


def require_platform_admin(api_endpoint):
    """Allow access only to platform admins."""

    @wraps(api_endpoint)
    def wrapper(*args, **kwargs):
        request = args[0]
        user = getattr(request, "user", None)
        if not user:
            raise HttpError(401, "Invalid or expired token")

        attributes = UserAttributes.objects.filter(user=user).first()
        if not attributes or not attributes.is_platform_admin:
            raise HttpError(403, "Platform admin access required")

        return api_endpoint(*args, **kwargs)

    return wrapper


def require_admin_role(allowed_roles: list[str]):
    """Guard endpoint by org role slug."""

    def decorator(api_endpoint):
        @wraps(api_endpoint)
        def wrapper(*args, **kwargs):
            request = args[0]
            orguser = getattr(request, "orguser", None)
            if not orguser or not orguser.new_role:
                raise HttpError(403, "Insufficient permissions")

            if orguser.new_role.slug not in allowed_roles:
                raise HttpError(403, "Insufficient permissions")

            return api_endpoint(*args, **kwargs)

        return wrapper

    return decorator
