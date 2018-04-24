from morepath import redirect
from morepath.request import Response
from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.utils import add_cors_header
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_election_compound_summary


@ElectionDayApp.html(
    model=ElectionCompound,
    permission=Public
)
def view_election_compound(self, request):

    """" The main view. """

    return redirect(ElectionCompoundLayout(self, request).main_view)


@ElectionDayApp.json(
    model=ElectionCompound,
    name='json',
    permission=Public
)
def view_election_compound_json(self, request):
    """" The main view as JSON. """

    last_modified = self.last_modified

    @request.after
    def add_headers(response):
        add_cors_header(response)
        add_last_modified_header(response, last_modified)

    embed = {}
    media = {'charts': {}}
    layout = ElectionCompoundLayout(self, request)
    layout.last_modified = last_modified
    if layout.pdf_path:
        media['pdf'] = request.link(self, 'pdf')
    for tab in ('party-strengths', 'parties-panachage'):
        layout = ElectionCompoundLayout(self, request, tab=tab)
        layout.last_modified = last_modified
        if layout.visible:
            embed[tab] = request.link(self, '{}-chart'.format(tab))
        if layout.svg_path:
            media['charts'][tab] = request.link(self, '{}-svg'.format(tab))

    return {
        'completed': self.completed,
        'date': self.date.isoformat(),
        'last_modified': last_modified.isoformat(),
        'mandates': {
            'allocated': self.allocated_mandates or 0,
            'total': self.number_of_mandates or 0,
        },
        'progress': {
            'counted': self.progress[0] or 0,
            'total': self.progress[1] or 0
        },
        'elections': [
            request.link(election) for election in self.elections
        ],
        'elected_candidates': self.elected_candidates,
        'related_link': self.related_link,
        'title': self.title_translations,
        'type': 'election_compound',
        'url': request.link(self),
        'embed': embed,
        'media': media,
        'data': {
            'json': request.link(self, 'data-json'),
            'csv': request.link(self, 'data-csv'),
        }
    }


@ElectionDayApp.json(
    model=ElectionCompound,
    name='summary',
    permission=Public
)
def view_election_compound_summary(self, request):

    """ View the summary of the election compound as JSON. """

    @request.after
    def add_headers(response):
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)

    return get_election_compound_summary(self, request)


@ElectionDayApp.view(
    model=ElectionCompound,
    name='pdf',
    permission=Public
)
def view_election_compound_pdf(self, request):

    """ View the generated PDF. """

    layout = ElectionCompoundLayout(self, request)

    if not layout.pdf_path:
        return Response(status='503 Service Unavailable')

    content = None
    with request.app.filestorage.open(layout.pdf_path, 'rb') as f:
        content = f.read()

    return Response(
        content,
        content_type='application/pdf',
        content_disposition='inline; filename={}.pdf'.format(
            normalize_for_url(self.title)
        )
    )
