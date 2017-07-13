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
    name='archive',
    template='archive.pt',
)
def view_archive(self, request):
    layout = Layout(self, request)
    session = request.app.session()
    user = get_user(request)

    notices = GazetteNoticeCollection(session, state='published').query()
    notices = notices.filter(GazetteNotice.user_id == user.id).all()

    new_notice = request.link(
        GazetteNoticeCollection(session, state='drafted'),
        name='new-notice'
    )

    return {
        'layout': layout,
        'title': _("My Published Official Notices"),
        'notices': notices,
        'new_notice': new_notice
    }
