from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.models import Archive


@ElectionDayApp.html(model=Archive, template='homepage.pt', permission=Public)
def view_archive(self, request):
    return {
        'layout': DefaultLayout(self, request),
        'date': self.date,
        'archive_items': self.by_date()
    }
