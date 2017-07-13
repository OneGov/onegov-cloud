from morepath import redirect
from onegov.core.security import Public
from onegov.gazette import GazetteApp
from onegov.gazette.layout import Layout
from onegov.gazette.models import Principal


@GazetteApp.html(model=Principal, permission=Public)
def view_principal(self, request):
    layout = Layout(self, request)

    if request.is_secret(self):
        return redirect(layout.manage_users_link)

    if request.is_private(self):
        return redirect(layout.manage_notices_link)

    if request.is_personal(self):
        return redirect(layout.dashboard_link)

    return redirect(layout.login_link)
