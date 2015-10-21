from onegov.core.security import Private
from onegov.town import TownApp
from onegov.town.models import PageMove


@TownApp.view(model=PageMove, permission=Private, request_method='PUT')
def move_page(self, request):
    request.assert_valid_csrf_token()
    self.execute()
