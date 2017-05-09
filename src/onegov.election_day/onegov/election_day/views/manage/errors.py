from onegov.core.security import Private
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import ManageLayout
from onegov.election_day.models import Principal


@ElectionDayApp.html(model=Principal, template='manage/provoke_error.pt',
                     permission=Private, name='provoke_error')
def view_provoke_error(self, request):

    return {
        'layout': ManageLayout(self, request)
    }
