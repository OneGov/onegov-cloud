from morepath import redirect
from morepath.request import Response
from onegov.ballot import Vote
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.utils import add_cors_header
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_vote_summary


@ElectionDayApp.html(
    model=Vote,
    permission=Public
)
def view_vote(self, request):

    """" The main view. """

    return redirect(VoteLayout(self, request).main_view)


@ElectionDayApp.json(
    model=Vote,
    name='json',
    permission=Public
)
def view_vote_json(self, request):

    """" The main view as JSON. """

    last_modified = self.last_modified

    @request.after
    def add_headers(response):
        add_cors_header(response)
        add_last_modified_header(response, last_modified)

    embed = {}
    media = {}
    layout = VoteLayout(self, request)
    layout.last_modified = last_modified
    if layout.pdf_path:
        media['pdf'] = request.link(self, 'pdf')
    if layout.show_map:
        media['maps'] = {}
        for ballot in ('', 'proposal-', 'counter-proposal-', 'tie-breaker-'):
            for map in ('entities', 'districts'):
                tab = f'{ballot}{map}'
                layout = VoteLayout(self, request, tab)
                layout.last_modified = last_modified
                if layout.visible:
                    embed[tab] = request.link(layout.ballot, name=f'{map}-map')
                    if layout.svg_path:
                        media['maps'][tab] = layout.svg_link

    counted = self.progress[0]
    nays_percentage = self.nays_percentage if counted else None
    yeas_percentage = self.yeas_percentage if counted else None
    return {
        'completed': self.completed,
        'date': self.date.isoformat(),
        'domain': self.domain,
        'last_modified': last_modified.isoformat(),
        'progress': {
            'counted': counted,
            'total': self.progress[1]
        },
        'related_link': self.related_link,
        'title': self.title_translations,
        'type': 'election',
        'results': {
            'answer': self.answer,
            'nays_percentage': nays_percentage,
            'yeas_percentage': yeas_percentage,
        },
        'ballots': [
            {
                'type': ballot.type,
                'title': ballot.title_translations,
                'progress': {
                    'counted': ballot.progress[0],
                    'total': ballot.progress[1],
                },
                'results': {
                    'total': {
                        'accepted': ballot.accepted,
                        'yeas': ballot.yeas,
                        'nays': ballot.nays,
                        'empty': ballot.empty,
                        'invalid': ballot.invalid,
                        'yeas_percentage': ballot.yeas_percentage,
                        'nays_percentage': ballot.nays_percentage,
                        'eligible_voters': ballot.eligible_voters,
                        'cast_ballots': ballot.cast_ballots,
                        'turnout': ballot.turnout,
                        'counted': ballot.counted,
                    },
                    'entitites': [
                        {
                            'accepted': entity.accepted,
                            'yeas': entity.yeas,
                            'nays': entity.nays,
                            'empty': entity.empty,
                            'invalid': entity.invalid,
                            'yeas_percentage': entity.yeas_percentage,
                            'nays_percentage': entity.nays_percentage,
                            'eligible_voters': entity.eligible_voters,
                            'cast_ballots': entity.cast_ballots,
                            'turnout': entity.turnout,
                            'counted': entity.counted,
                            'name': (
                                entity.name if entity.entity_id else 'Expats'
                            ),
                            'district': (
                                entity.district if entity.entity_id else ''
                            ),
                            'id': entity.entity_id,
                        } for entity in ballot.results
                    ],
                },
            } for ballot in self.ballots
        ],
        'url': request.link(self),
        'embed': embed,
        'media': media,
        'data': {
            'json': request.link(self, 'data-json'),
            'csv': request.link(self, 'data-csv'),
        }
    }


@ElectionDayApp.json(
    model=Vote,
    name='summary',
    permission=Public
)
def view_vote_summary(self, request):

    """ View the summary of the vote as JSON. """

    @request.after
    def add_headers(response):
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)

    return get_vote_summary(self, request)


@ElectionDayApp.view(
    model=Vote,
    name='pdf',
    permission=Public
)
def view_vote_pdf(self, request):

    """ View the generated PDF. """

    layout = VoteLayout(self, request)

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
