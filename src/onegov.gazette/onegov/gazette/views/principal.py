from datetime import datetime
from datetime import timedelta
from morepath import redirect
from onegov.core.security import Personal
from onegov.core.security import Public
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.layout import Layout
from onegov.gazette.models import Principal
from onegov.gazette.views import get_user_and_group


@GazetteApp.html(
    model=Principal,
    permission=Public
)
def view_principal(self, request):
    """ The homepage. Redirects to the default management views according to
    the logged in role.

    """

    layout = Layout(self, request)

    if request.is_secret(self):
        return redirect(layout.manage_users_link)

    if request.is_private(self):
        return redirect(layout.manage_notices_link)

    if request.is_personal(self):
        return redirect(layout.dashboard_link)

    return redirect(layout.login_link)


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
        request.app.session(),
        user_ids=user_ids,
        group_ids=group_ids
    )

    # rejected
    rejected = collection.for_state('rejected').query().all()
    if rejected:
        request.message(_("You have rejected messages."), 'warning')

    # drafted
    drafted = collection.for_state('drafted').query().all()
    now = datetime.now()
    limit = now + timedelta(days=2)
    for notice in drafted:
        past_issues_selected = False
        deadline_reached_soon = False
        for issue in notice.issues:
            deadline = self.issue(issue).deadline
            past_issues_selected = past_issues_selected or deadline < now
            deadline_reached_soon = deadline_reached_soon or deadline < limit
        if past_issues_selected:
            request.message(
                _(
                    (
                        "You have a drafted message with past issues: "
                        "<a href='${link}'>${title}</a>"
                    ),
                    mapping={
                        'link': request.link(notice),
                        'title': notice.title
                    }
                ),
                'info'
            )
        elif deadline_reached_soon:
            request.message(
                _(
                    (
                        "You have a drafted message with issues close to "
                        "the deadline: <a href='${link}'>${title}</a>"
                    ),
                    mapping={
                        'link': request.link(notice),
                        'title': notice.title
                    }
                ),
                'info'
            )

    # submitted
    submitted = collection.for_state('submitted').query().all()

    new_notice = request.link(
        collection.for_state('drafted'),
        name='new-notice'
    )

    return {
        'layout': layout,
        'title': _("My Drafted and Submitted Official Notices"),
        'rejected': rejected,
        'drafted': drafted,
        'submitted': submitted,
        'new_notice': new_notice,
        'current_issue': self.current_issue,
    }
