from csv import writer
from morepath import redirect
from morepath.request import Response
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.forms import EmptyForm
from onegov.gazette.forms import NoticeForm
from onegov.gazette.layout import Layout
from onegov.gazette.views import get_user
from onegov.gazette.views import get_user_and_group


@GazetteApp.form(
    model=GazetteNoticeCollection,
    name='new-notice',
    template='form.pt',
    permission=Personal,
    form=NoticeForm
)
def create_notice(self, request, form):
    """ Create a new notice.

    If a valid UID of a notice is given (via 'source' query parameter), its
    values are pre-filled in the form.

    This view is mainly used by the editors.

    """
    self.on_request(request)

    layout = Layout(self, request)
    principal = request.app.principal

    if form.submitted(request):
        notice = self.add(
            title=form.title.data,
            text=form.text.data,
            organization_id=form.organization.data,
            category_id=form.category.data,
            user=get_user(request),
            issues=form.issues.data,
            principal=principal
        )
        return redirect(request.link(notice))

    if not form.errors and self.source:
        source = self.query().filter_by(id=self.source).first()
        if source:
            form.apply_model(source)

    return {
        'layout': layout,
        'form': form,
        'title': _("New Official Notice"),
        'button_text': _("Save"),
        'cancel': layout.dashboard_link,
        'current_issue': principal.current_issue
    }


@GazetteApp.html(
    model=GazetteNoticeCollection,
    template='notices.pt',
    permission=Personal
)
def view_notices(self, request):
    """ View the list of notices.

    This view is only visible by a publisher. This (in the state 'accepted')
    is the view used by the publisher.

    """
    self.on_request(request)

    layout = Layout(self, request)

    filters = (
        {
            'title': _(state),
            'link': request.link(self.for_state(state)),
            'class': 'active' if state == self.state else ''
        }
        for state in ('drafted', 'submitted', 'accepted', 'rejected')
    )

    orderings = {
        'title': {
            'title': _("Title"),
            'href': request.link(self.for_order('title')),
            'sort': self.direction if self.order == 'title' else '',
        },
        'organization': {
            'title': _("Organization"),
            'href': request.link(self.for_order('organization')),
            'sort': self.direction if self.order == 'organization' else '',
        },
        'category': {
            'title': _("Category"),
            'href': request.link(self.for_order('category')),
            'sort': self.direction if self.order == 'category' else '',
        },
        'first_issue': {
            'title': _("Issue(s)"),
            'href': request.link(self.for_order('first_issue')),
            'sort': self.direction if self.order == 'first_issue' else '',
        }
    }

    title = _("Official Notices")
    if not request.is_private(self):
        self.user_ids, self.group_ids = get_user_and_group(request)
        filters = None
        title = _("My Accepted Official Notices")

    return {
        'layout': layout,
        'notices': self.batch,
        'title': title,
        'filters': filters,
        'term': self.term,
        'from_date': self.from_date,
        'to_date': self.to_date,
        'orderings': orderings,
        'clear_term': request.link(self.for_term('')),
        'clear_dates': request.link(self.for_dates(None, None)),
        'new_notice': request.link(self, name='new-notice')
    }


@GazetteApp.html(
    model=GazetteNoticeCollection,
    template='statistics.pt',
    name='statistics',
    permission=Private
)
def view_notices_statistics(self, request):
    """ View the list of notices.

    This view is only visible by a publisher. This (in the state 'accepted')
    is the view used by the publisher.

    """
    self.on_request(request)

    layout = Layout(self, request)
    filters = (
        {
            'title': _(state),
            'link': request.link(self.for_state(state), name='statistics'),
            'class': 'active' if state == self.state else ''
        }
        for state in ('drafted', 'submitted', 'accepted', 'rejected')
    )

    return {
        'layout': layout,
        'filters': filters,
        'collection': self,
        'title': _("Statistics"),
        'from_date': self.from_date,
        'to_date': self.to_date,
        'by_organizations': self.count_by_organization(),
        'by_category': self.count_by_category(),
        'by_groups': self.count_by_group(),
        'clear': request.link(self.for_dates(None, None), name='statistics')
    }


@GazetteApp.view(
    model=GazetteNoticeCollection,
    name='statistics-organizations',
    permission=Private
)
def view_notices_statistics_organizations(self, request):
    """ View the organizations statistics data as CSV. """
    self.on_request(request)

    response = Response()
    response.content_type = 'text/csv'
    response.content_disposition = 'inline; filename={}.csv'.format(
        request.translate(_("Organizations")).lower()
    )
    csvwriter = writer(response)
    csvwriter.writerow([
        request.translate(_("Organization")),
        request.translate(_("Number of Notices"))
    ])
    csvwriter.writerows(self.count_by_organization())

    return response


@GazetteApp.view(
    model=GazetteNoticeCollection,
    name='statistics-categories',
    permission=Private
)
def view_notices_statistics_categories(self, request):
    """ View the categories statistics data as CSV. """
    self.on_request(request)

    response = Response()
    response.content_type = 'text/csv'
    response.content_disposition = 'inline; filename={}.csv'.format(
        request.translate(_("Categories")).lower()
    )
    csvwriter = writer(response)
    csvwriter.writerow([
        request.translate(_("Category")),
        request.translate(_("Number of Notices"))
    ])
    csvwriter.writerows(self.count_by_category())

    return response


@GazetteApp.view(
    model=GazetteNoticeCollection,
    name='statistics-groups',
    permission=Private
)
def view_notices_statistics_groups(self, request):
    """ View the groups statistics data as CSV. """
    self.on_request(request)

    response = Response()
    response.content_type = 'text/csv'
    response.content_disposition = 'inline; filename={}.csv'.format(
        request.translate(_("Groups")).lower()
    )
    csvwriter = writer(response)
    csvwriter.writerow([
        request.translate(_("Group")),
        request.translate(_("Number of Notices"))
    ])
    csvwriter.writerows(self.count_by_group())

    return response


@GazetteApp.form(
    model=GazetteNoticeCollection,
    name='update',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def view_notices_update(self, request, form):
    """ Updates all notices (of this state): Applies the categories, issues and
    organization from the meta informations. This view is not used normally
    and only intended when changing category names in the principal definition,
    for example.

    """
    self.on_request(request)

    layout = Layout(self, request)
    principal = request.app.principal

    if form.submitted(request):
        for notice in self.query():
            notice.apply_meta(principal)
        request.message(_("Notices updated."), "success")

        return redirect(layout.manage_notices_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("Update notices"),
        'button_text': _("Update"),
        'cancel': layout.manage_notices_link
    }
