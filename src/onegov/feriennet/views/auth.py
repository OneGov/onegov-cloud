from onegov.core.security import Public
from onegov.feriennet import FeriennetApp, _
from onegov.org.views.auth import handle_registration
from onegov.user import Auth
from onegov.user.forms import RegistrationForm


@FeriennetApp.form(
    model=Auth, name='register', template='form.pt',
    permission=Public, form=RegistrationForm
)
def custom_handle_registration(self, request, form):
    if request.app.org.meta.get('require_full_age_for_registration', False):
        form.callout = _(
            "The user account must be opened by a parent or guardian of "
            "full age."
        )
    return handle_registration(self, request, form)
