from onegov.core.security import Personal
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.layout import Layout
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Principal
from onegov.gazette.views import get_user


@GazetteApp.html(
    model=Principal,
    permission=Personal,
    name='dashboard',
    template='dashboard.pt',
)
def view_dashboard(self, request):
    layout = Layout(self, request)
    session = request.app.session()
    user = get_user(request)

    rejected = GazetteNoticeCollection(session, state='rejected').query()
    rejected = rejected.filter(GazetteNotice.user_id == user.id).all()
    if rejected:
        request.message(_("You have rejected messages."), 'warning')

    drafted = GazetteNoticeCollection(session, state='drafted').query()
    drafted = drafted.filter(GazetteNotice.user_id == user.id).all()

    submitted = GazetteNoticeCollection(session, state='submitted').query()
    submitted = submitted.filter(GazetteNotice.user_id == user.id).all()

    new_notice = request.link(
        GazetteNoticeCollection(session, state='drafted'),
        name='new-notice'
    )

    return {
        'layout': layout,
        'title': _("My Drafted and Submitted Official Notices"),
        'rejected': rejected,
        'drafted': drafted,
        'submitted': submitted,
        'new_notice': new_notice
    }
