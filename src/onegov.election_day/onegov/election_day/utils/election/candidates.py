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
        Candidate.votes,
        List.name,
        List.list_id
    )
    result = result.outerjoin(List)
    result = result.order_by(
        List.list_id,
        desc(Candidate.elected),
        desc(Candidate.votes),
        Candidate.family_name,
        Candidate.first_name
    )
    result = result.filter(Candidate.election_id == election.id)

    return result


def get_candidates_data(election, request):
    """" Get the candidates as JSON. Used to for the candidates bar chart. """

    session = object_session(election)

    candidates = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.votes
    )
    candidates = candidates.order_by(
        desc(Candidate.elected),
        desc(Candidate.votes),
        Candidate.family_name,
        Candidate.first_name
    )
    candidates = candidates.filter(Candidate.election_id == election.id)

    majority = 0
    if (
        election.type == 'majorz' and
        election.majority_type == 'absolute' and
        election.absolute_majority is not None
    ):
        majority = election.absolute_majority

    return {
        'results': [
            {
                'text': '{} {}'.format(candidate[0], candidate[1]),
                'value': candidate[3],
                'class': 'active' if candidate[2] else 'inactive'
            } for candidate in candidates.all()
            if (
                election.type == 'majorz' or
                election.type == 'proporz' and candidate[2]
            )
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
        List.name,
        List.list_id,
        Election.id
    )
    elected = elected.outerjoin(List)
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
