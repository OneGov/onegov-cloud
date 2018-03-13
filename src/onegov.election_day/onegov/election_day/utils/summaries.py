from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import Vote
from onegov.election_day.models import ArchivedResult


def get_election_summary(election, request, url=None):
    """ Returns some basic informations about the given election as a JSON
    seriazable dict. """

    last_modified = election.last_modified
    if last_modified:
        last_modified = last_modified.isoformat()

    return {
        'completed': election.completed,
        'date': election.date.isoformat(),
        'domain': election.domain,
        'elected': election.elected_candidates,
        'last_modified': last_modified,
        'progress': {
            'counted': election.progress[0] or 0,
            'total': election.progress[1] or 0
        },
        'title': election.title_translations,
        'type': 'election',
        'url': url or request.link(election),
    }


def get_election_compound_summary(election_compound, request, url=None):

    last_modified = election_compound.last_modified
    if last_modified:
        last_modified = last_modified.isoformat()

    return {
        'completed': election_compound.completed,
        'date': election_compound.date.isoformat(),
        'domain': election_compound.domain,
        'last_modified': last_modified,
        'progress': {
            'counted': election_compound.progress[0] or 0,
            'total': election_compound.progress[1] or 0
        },
        'title': election_compound.title_translations,
        'type': 'election_compound',
        'url': url or request.link(election_compound),
        'elections': [
            request.link(election) if isinstance(election, Election)
            else election
            for election in election_compound.elections
        ]
    }


def get_vote_summary(vote, request, url=None):
    """ Returns some basic informations about the given vote as a JSON
    seriazable dict. """

    try:
        divider = vote.ballots.count() or 1
    except AttributeError:
        divider = 1

    last_modified = vote.last_modified
    if last_modified:
        last_modified = last_modified.isoformat()

    counted = vote.progress[0] or 0
    nays_percentage = vote.nays_percentage if counted else None
    yeas_percentage = vote.yeas_percentage if counted else None
    summary = {
        'answer': vote.answer or None,
        'completed': vote.completed,
        'date': vote.date.isoformat(),
        'domain': vote.domain,
        'last_modified': last_modified,
        'nays_percentage': nays_percentage,
        'progress': {
            'counted': counted / divider,
            'total': (vote.progress[1] or 0) / divider
        },
        'title': vote.title_translations,
        'type': 'vote',
        'url': url or request.link(vote),
        'yeas_percentage': yeas_percentage,
    }
    if 'local' in (vote.meta or {}):
        summary['local'] = {
            'answer': vote.local_answer or "",
            'nays_percentage': vote.local_nays_percentage,
            'yeas_percentage': vote.local_yeas_percentage,
        }
    return summary


def get_summary(item, request):
    """ Returns some basic informations about the given election/vote as a JSON
    seriazable dict. """

    if isinstance(item, Election):
        return get_election_summary(item, request)

    if isinstance(item, ElectionCompound):
        return get_election_compound_summary(item, request)

    if isinstance(item, Vote):
        return get_vote_summary(item, request)

    if isinstance(item, ArchivedResult):
        if item.type == 'election':
            return get_election_summary(item, None, item.url)
        if item.type == 'election_compound':
            return get_election_compound_summary(item, None, item.url)
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
