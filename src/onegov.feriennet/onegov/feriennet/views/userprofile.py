from onegov.core.security import Personal
from onegov.feriennet import FeriennetApp
from onegov.feriennet.forms import UserProfileForm
from onegov.org.models import Organisation
from onegov.org.views.userprofile import handle_user_profile


@FeriennetApp.form(
    model=Organisation, name='userprofile', template='userprofile.pt',
    permission=Personal, form=UserProfileForm)
def handle_custom_user_profile(self, request, form):
    return handle_user_profile(self, request, form)
