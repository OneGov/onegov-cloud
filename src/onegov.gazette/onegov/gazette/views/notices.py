from morepath.request import Response
from onegov.core.security import Private
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.layout import Layout
from csv import writer


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
