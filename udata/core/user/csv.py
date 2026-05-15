from udata.frontend import csv

from .models import User


@csv.adapter(User)
class UserCsvAdapter(csv.Adapter):
    fields = (
        "id",
        "slug",
        "first_name",
        "last_name",
        "email",
        "website",
        "about",
        "active",
        "roles",
        "created_at",
        "last_login_at",
        "current_login_at",
        "last_login_ip",
        "current_login_ip",
        "login_count",
        ("organizations", lambda u: ",".join(str(o.id) for o in u.organizations)),
        ("deleted", lambda u: u.deleted is not None),
    )

    def dynamic_fields(self):
        return csv.metric_fields(User) 