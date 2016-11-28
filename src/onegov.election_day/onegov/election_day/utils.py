from onegov.ballot import Election, Vote
from onegov.election_day.models import ArchivedResult


def handle_headerless_params(request):
    if 'headerless' in request.params:
        request.browser_session['headerless'] = True
    if 'headerful' in request.params:
        if request.browser_session.has('headerless'):
            del request.browser_session['headerless']

    if request.browser_session.get('headerless'):
        request.include('frame_resizer')


def add_last_modified_header(response, last_modified):
    """ Adds the give date to the response as Last-Modified header. """

    if last_modified:
        response.headers.add(
            'Last-Modified',
            last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
        )


def get_election_summary(election, request, url=None):
    """ Returns some basic informations about the given election as a JSON
    seriazable dict. """

    last_modified = election.last_result_change
    if last_modified:
        last_modified = last_modified.isoformat()

    return {
        'date': election.date.isoformat(),
        'domain': election.domain,
        'last_modified': last_modified,
        'progress': {
            'counted': election.counted_entities or 0,
            'total': election.total_entities or 0
        },
        'title': election.title_translations,
        'type': 'election',
        'url': url or request.link(election),
    }


def get_vote_summary(vote, request, url=None):
    """ Returns some basic informations about the given vote as a JSON
    seriazable dict. """

    try:
        divider = vote.ballots.count() or 1
    except AttributeError:
        divider = 1

    last_modified = vote.last_result_change
    if last_modified:
        last_modified = last_modified.isoformat()

    return {
        'answer': vote.answer or "",
        'date': vote.date.isoformat(),
        'domain': vote.domain,
        'last_modified': last_modified,
        'nays_percentage': vote.nays_percentage,
        'progress': {
            'counted': (vote.progress[0] or 0) / divider,
            'total': (vote.progress[1] or 0) / divider
        },
        'title': vote.title_translations,
        'type': 'vote',
        'url': url or request.link(vote),
        'yeas_percentage': vote.yeas_percentage,
    }


def get_summary(item, request):
    """ Returns some basic informations about the given election/vote as a JSON
    seriazable dict. """
    if isinstance(item, Election):
        return get_election_summary(item, request)

    if isinstance(item, Vote):
        return get_vote_summary(item, request)

    if isinstance(item, ArchivedResult):
        if item.type == 'election':
            return get_election_summary(item, None, item.url)
        if item.type == 'vote':
            return get_vote_summary(item, None, item.url)

    raise NotImplementedError(
        "get_summary can't handle type {}".format(type(item))
    )


def get_summaries(items, request):
    """ Converts the given list of election/votes to a JSON seriazable
    list of summaries.

    """

    return [get_summary(item, request) for item in items]


def get_archive_links(archive, request):
    """ Returns a JSON seriazable dict of available archive links. """

    return {
        str(year): request.link(archive.for_date(year))
        for year in archive.get_years()
    }
