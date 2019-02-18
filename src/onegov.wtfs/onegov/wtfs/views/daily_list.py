from onegov.wtfs import WtfsApp
from onegov.wtfs.layouts import DailyListLayout
from onegov.wtfs.models import DailyList
from onegov.wtfs.security import ViewModel


@WtfsApp.html(
    model=DailyList,
    template='daily_list.pt',
    permission=ViewModel
)
def view_daily_list(self, request):
    """ View a single daily list. """
    layout = DailyListLayout(self, request)

    return {
        'layout': layout,
    }
