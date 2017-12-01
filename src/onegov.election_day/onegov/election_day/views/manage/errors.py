from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ManageLayout
from onegov.election_day.models import Principal


@ElectionDayApp.manage_html(
    model=Principal,
    name='provoke_error',
    template='manage/provoke_error.pt'
)
def view_provoke_error(self, request):

    """ Provokes a JavaScript Error for testing.

    This view is not linked anywhere.

    """

    return {
        'layout': ManageLayout(self, request)
    }
