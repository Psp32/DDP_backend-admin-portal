from django.db.models import Q

from ddpui.models.org import Org


class AdminOrgService:
    @staticmethod
    def list_orgs(search: str | None = None, status: str | None = None):
        queryset = Org.objects.all().order_by("-id")
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(slug__icontains=search))
        # Org does not have explicit status; keep compatibility with requested filter.
        if status == "inactive":
            queryset = queryset.none()
        return queryset
