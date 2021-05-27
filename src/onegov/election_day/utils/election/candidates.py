from onegov.ballot import Candidate
from onegov.ballot import Election
from onegov.ballot import List
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


def get_candidates_data(election, limit=None):
    """" Get the candidates as JSON. Used to for the candidates bar chart. """

    colors = election.colors
    default_color = '#999' if election.colors else ''

    session = object_session(election)

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

    majority = 0
    if (
        election.type == 'majorz'
        and election.majority_type == 'absolute'
        and election.absolute_majority is not None
        and election.completed
    ):
        majority = election.absolute_majority

    if election.type == 'proporz':
        candidates = candidates.filter(Candidate.elected == True)

        colors = {
            list_id: election.colors[name]
            for list_id, name in session.query(List.id, List.name)
            if name in election.colors
        }

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
