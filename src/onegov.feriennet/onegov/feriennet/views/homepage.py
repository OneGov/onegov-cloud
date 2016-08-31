from onegov.core.security import Public
from onegov.feriennet import FeriennetApp
from onegov.org.layout import DefaultLayout
from onegov.org.models import Organisation
from onegov.user import Auth


@FeriennetApp.html(model=Organisation, template='homepage.pt',
                   permission=Public)
def view_feriennet(self, request):

    layout = DefaultLayout(self, request)

    return {
        'layout': layout,
        'title': self.name,
        'login_url': request.class_link(Auth, name='login'),
        'register_url': request.class_link(Auth, name='register')
    }
