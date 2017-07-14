from csv import writer
from morepath import redirect
from morepath.request import Response
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.forms import NoticeForm
from onegov.gazette.layout import Layout
from onegov.gazette.views import get_user_id


@GazetteApp.form(
    model=GazetteNoticeCollection,
    name='new-notice',
    template='form.pt',
    permission=Personal,
    form=NoticeForm
)
def create_notice(self, request, form):
    """ Create one or more new notices.

    We allow to create multiple notices with the same attributs for different.
    This view is mainly used by the editors.

    """
    layout = Layout(self, request)

    if form.submitted(request):
        notice = self.add(
            title=form.title.data,
            text=form.text.data,
            category=form.category.data,
            issues=form.issues.data,
            user_id=get_user_id(request)
        )
        return redirect(request.link(notice))

    if not form.errors and 'source' in request.params:
        try:
            form.apply_model(
                self.query().filter_by(id=request.params['source']).first()
            )
        except KeyError:
            pass

    return {
        'layout': layout,
        'form': form,
        'title': _("New Official Notice"),
        'button_text': _("Save"),
        'cancel': layout.dashboard_link
    }


@GazetteApp.html(
    model=GazetteNoticeCollection,
    template='notices.pt',
    permission=Private
)
def view_notices(self, request):
    """ View the list of notices.

    This view is only visible by a publisher. This (in the state 'published')
    is the view used by the publisher.

    """

    layout = Layout(self, request)

    title = {
        'submitted': _("Submitted Official Notices"),
        'published': _("Published Official Notices")
    }.get(self.state, _("Official Notices"))

    return {
        'layout': layout,
        'state': self.state,
        'notices': self.batch,
        'title': title
    }


@GazetteApp.html(
    model=GazetteNoticeCollection,
    template='statistics.pt',
    name='statistics',
    permission=Private
)
def view_notices_statistics(self, request):
    """ View the list of notices.

    This view is only visible by a publisher. This (in the state 'published')
    is the view used by the publisher.

    """

    layout = Layout(self, request)
    principal = request.app.principal

    return {
        'layout': layout,
        'collection': self,
        'title': _("Statistics"),
        'by_category': self.count_by_category(principal),
        'by_groups': self.count_by_group(),
    }


@GazetteApp.view(
    model=GazetteNoticeCollection,
    name='statistics-categories',
    permission=Private
)
def view_notices_statistics_categories(self, request):
    """ View the categories statistics data as CSV. """

    principal = request.app.principal

    response = Response()
    response.content_type = 'text/csv'
    response.content_disposition = 'inline; filename={}.csv'.format(
        request.translate(_("Categories")).lower()
    )
    csvwriter = writer(response)
    csvwriter.writerow([
        request.translate(_("Category")),
        request.translate(_("Title")),
        request.translate(_("Number of Notices"))
    ])
    csvwriter.writerows(self.count_by_category(principal))

    return response


@GazetteApp.view(
    model=GazetteNoticeCollection,
    name='statistics-groups',
    permission=Private
)
def view_notices_statistics_groups(self, request):
    """ View the groups statistics data as CSV. """

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
