from datetime import timedelta
from morepath import redirect
from onegov.core.security import Personal
from onegov.core.security import Public
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.collections import IssueCollection
from onegov.gazette.layout import Layout
from onegov.gazette.models import Principal
from onegov.gazette.views import get_user_and_group
from sedate import utcnow


@GazetteApp.html(
    model=Principal,
    permission=Public
)
def view_principal(self, request):
    """ The homepage.

    Redirects to the default management views according to the logged in role.

    Shows the weekly PDFs if not logged-in.

    """

    layout = Layout(self, request)

    if request.is_private(self):
        return redirect(layout.manage_notices_link)

    if request.is_personal(self):
        return redirect(layout.dashboard_link)

    if not request.app.principal.frontend:
        return redirect(layout.login_link)

    return redirect(request.link(self, name='archive'))


@GazetteApp.html(
    model=Principal,
    permission=Public,
    name='archive',
    template='archive.pt',
)
def view_archive(self, request):
    """ The archive.

    Shows all the weekly PDFs by year.

    """
    layout = Layout(self, request)

    return {
        'layout': layout,
        'issues': IssueCollection(request.session).by_years(desc=True)
    }


@GazetteApp.html(
    model=Principal,
    permission=Personal,
    name='dashboard',
    template='dashboard.pt',
)
def view_dashboard(self, request):
    """ The dashboard view (for editors).

    Shows the drafted, submitted and rejected notices, shows warnings and
    allows to create a new notice.

    """
    layout = Layout(self, request)

    user_ids, group_ids = get_user_and_group(request)
    collection = GazetteNoticeCollection(
        request.session,
        user_ids=user_ids,
        group_ids=group_ids
    )

    # rejected
    rejected = collection.for_state('rejected').query().all()
    if rejected:
        request.message(_("You have rejected messages."), 'warning')

    # drafted
    drafted = collection.for_state('drafted').query().all()
    now = utcnow()
    limit = now + timedelta(days=2)
    past_issues_selected = False
    deadline_reached_soon = False
    for notice in drafted:
        for issue in notice.issue_objects:
            if issue.deadline < now:
                past_issues_selected = True
            elif issue.deadline < limit:
                deadline_reached_soon = True
    if past_issues_selected:
        request.message(
            _("You have drafted messages with past issues."),
            'warning'
        )
    if deadline_reached_soon:
        request.message(
            _("You have drafted messages with issues close to the deadline."),
            'warning'
        )

    # submitted
    submitted = collection.for_state('submitted').query().all()

    new_notice = request.link(
        collection.for_state('drafted'),
        name='new-notice'
    )

    return {
        'layout': layout,
        'title': _("Dashboard"),
        'rejected': rejected,
        'drafted': drafted,
        'submitted': submitted,
        'new_notice': new_notice,
        'current_issue': layout.current_issue
    }
