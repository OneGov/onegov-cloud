from __future__ import annotations

from onegov.election_day.models import ArchivedResult
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import Vote


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.core.types import JSONObject_ro
    from onegov.election_day.models import ElectionCompoundPart
    from onegov.election_day.request import ElectionDayRequest
    from typing import TypeAlias

    ElectionCompoundOrPart: TypeAlias = ElectionCompound | ElectionCompoundPart


def get_election_summary(
    election: Election | ArchivedResult,
    request: ElectionDayRequest | None,
    url: str | None = None
) -> JSONObject_ro:
    """ Returns some basic informations about the given election as a JSON
    seriazable dict. """

    last_modified = election.last_modified

    return {
        'completed': election.completed,
        'date': election.date.isoformat(),
        'domain': election.domain,
        'elected': election.elected_candidates,
        'last_modified': last_modified.isoformat() if last_modified else None,
        'progress': {
            'counted': election.progress[0] or 0,
            'total': election.progress[1] or 0
        },
        'title': election.title_translations,
        'turnout': election.turnout,
        'type': 'election',
        'url': url or request.link(election),  # type:ignore[union-attr]
    }


def get_election_compound_summary(
    election_compound: ElectionCompoundOrPart | ArchivedResult,
    request: ElectionDayRequest | None,
    url: str | None = None,
    type_: str = 'election_compound'
) -> JSONObject_ro:

    last_modified = election_compound.last_modified

    return {
        'completed': election_compound.completed,
        'date': election_compound.date.isoformat(),
        'domain': election_compound.domain,
        'elected': election_compound.elected_candidates,
        'last_modified': last_modified.isoformat() if last_modified else None,
        'progress': {
            'counted': election_compound.progress[0] or 0,
            'total': election_compound.progress[1] or 0
        },
        'title': election_compound.title_translations,
        'type': type_,
        'url': url or request.link(election_compound),  # type:ignore
        'elections': [
            request.link(election)  # type:ignore[union-attr]
            if isinstance(election, Election)
            else election
            for election in election_compound.elections
        ]
    }


def get_vote_summary(
    vote: Vote | ArchivedResult,
    request: ElectionDayRequest | None,
    url: str | None = None
) -> JSONObject_ro:
    """ Returns some basic informations about the given vote as a JSON
    seriazable dict. """

    try:
        divider = len(vote.ballots) or 1  # type:ignore[union-attr]
    except AttributeError:
        divider = 1

    last_modified = vote.last_modified

    counted = vote.progress[0] or 0
    nays_percentage = vote.nays_percentage if counted else None
    yeas_percentage = vote.yeas_percentage if counted else None
    summary = {
        'answer': vote.answer or None,
        'completed': vote.completed,
        'date': vote.date.isoformat(),
        'domain': vote.domain,
        'last_modified': last_modified.isoformat() if last_modified else None,
        'nays_percentage': nays_percentage,
        'progress': {
            'counted': counted / divider,
            'total': (vote.progress[1] or 0) / divider
        },
        'title': vote.title_translations,
        'turnout': vote.turnout,
        'type': 'vote',
        'url': url or request.link(vote),  # type:ignore[union-attr]
        'yeas_percentage': yeas_percentage,
    }
    if 'local' in (vote.meta or {}):
        summary['local'] = {
            'answer': vote.local_answer or '',  # type:ignore
            'nays_percentage': vote.local_nays_percentage,  # type:ignore
            'yeas_percentage': vote.local_yeas_percentage,  # type:ignore
        }
    return summary


def get_summary(
    item: Election | ElectionCompound | Vote | ArchivedResult,
    request: ElectionDayRequest
) -> JSONObject_ro:
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
            return get_election_summary(
                item, None, item.adjusted_url(request)
            )
        if item.type == 'election_compound':
            return get_election_compound_summary(
                item, None, item.adjusted_url(request)
            )
        if item.type in ('vote', 'complex_vote'):
            return get_vote_summary(
                item, None, item.adjusted_url(request)
            )

    raise NotImplementedError(
        "get_summary can't handle type {}".format(type(item))
    )


def get_summaries(
    items: Iterable[Election | ElectionCompound | Vote | ArchivedResult],
    request: ElectionDayRequest
) -> list[JSONObject_ro]:
    """ Converts the given list of election/votes to a JSON seriazable
    list of summaries.

    """

    return [get_summary(item, request) for item in items]
