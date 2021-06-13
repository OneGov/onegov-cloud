from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import Election
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.core.utils import groupbylist
from sqlalchemy import desc
from sqlalchemy.orm import object_session


def get_candidates_results(election, session):
    """ Returns the aggregated candidates results as list. """

    result = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.party,
        Candidate.votes.label('votes'),
        List.name,
        List.list_id
    )
    result = result.outerjoin(List)
    result = result.filter(Candidate.election_id == election.id)

    if election.completed:
        result = result.order_by(
            List.list_id,
            desc(Candidate.elected),
            desc(Candidate.votes),
            Candidate.family_name,
            Candidate.first_name
        )
    else:
        result = result.order_by(
            List.list_id,
            desc(Candidate.votes),
            Candidate.family_name,
            Candidate.first_name
        )

    return result


def get_candidates_data(election, limit=None, lists=None, elected=None):
    """" Get the candidates as JSON. Used to for the candidates bar chart.

    Allows to optionally
    - return only the first ``limit`` results.
    - return only results for candidates within the given list names (proporz)
      or party names (majorz).
    - return only elected candidates. If not specified, only elected candidates
      are returned for proporz elections, all for majorz elections.

    """

    session = object_session(election)

    list_names = {}
    colors = election.colors
    default_color = '#999' if election.colors else ''
    if election.type == 'proporz':
        list_names = dict(session.query(List.id, List.name).all())
        colors = {
            list_id: election.colors[name]
            for list_id, name in list_names.items()
            if name in election.colors
        }

    candidates = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.votes.label('votes'),
        Candidate.list_id,
        Candidate.party
    )
    candidates = candidates.filter(Candidate.election_id == election.id)

    if election.completed:
        candidates = candidates.order_by(
            desc(Candidate.elected),
            desc(Candidate.votes),
            Candidate.family_name,
            Candidate.first_name
        )
    else:
        candidates = candidates.order_by(
            desc(Candidate.votes),
            Candidate.family_name,
            Candidate.first_name
        )

    if lists:
        if election.type == 'majorz':
            candidates = candidates.filter(Candidate.party.in_(lists))
        else:
            list_ids = {
                id_ for id_, name in list_names.items() if name in lists
            }
            candidates = candidates.filter(Candidate.list_id.in_(list_ids))

    elected = election.type == 'proporz' if elected is None else elected
    if elected:
        candidates = candidates.filter(Candidate.elected == True)

    majority = 0
    if (
        election.type == 'majorz'
        and election.majority_type == 'absolute'
        and election.absolute_majority is not None
        and election.completed
    ):
        majority = election.absolute_majority

    if limit and limit > 0:
        candidates = candidates.limit(limit)

    return {
        'results': [
            {
                'text': '{} {}'.format(
                    candidate.family_name, candidate.first_name
                ),
                'value': candidate.votes,
                'class': (
                    'active' if candidate.elected and election.completed
                    else 'inactive'
                ),
                'color': (
                    colors.get(candidate.party)
                    or colors.get(candidate.list_id)
                    or default_color
                )
            } for candidate in candidates
        ],
        'majority': majority,
        'title': election.title
    }


def get_elected_candidates(election_compound, session):
    """ Returns the elected candidates of an election compound. """

    election_ids = [election.id for election in election_compound.elections]

    elected = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.party,
        List.name.label('list'),
        List.list_id,
        Election.id.label('election_id')
    )
    elected = elected.outerjoin(List, Candidate.list_id == List.id)
    elected = elected.outerjoin(Election)
    elected = elected.order_by(
        Election.shortcode,
        List.list_id,
        Candidate.family_name,
        Candidate.first_name
    )
    elected = elected.filter(Candidate.election_id.in_(election_ids))
    elected = elected.filter(Candidate.elected.is_(True))

    return elected


def get_candidates_results_by_entity(election):
    """ Returns the candidates results by entity. """

    session = object_session(election)

    candidates = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.votes.label('votes')
    )
    candidates = candidates.order_by(
        Candidate.family_name,
        Candidate.first_name
    )
    candidates = candidates.filter(Candidate.election_id == election.id)

    results = session.query(
        ElectionResult.name,
        Candidate.family_name,
        Candidate.first_name,
        CandidateResult.votes
    )
    results = results.outerjoin(Candidate, ElectionResult)
    results = results.filter(ElectionResult.election_id == election.id)
    results = results.filter(Candidate.election_id == election.id)
    results = results.order_by(
        ElectionResult.name,
        Candidate.family_name,
        Candidate.first_name
    )

    return candidates.all(), groupbylist(results, key=lambda x: x[0])
