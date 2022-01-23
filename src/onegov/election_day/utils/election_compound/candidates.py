from onegov.ballot import Candidate
from onegov.ballot import Election
from onegov.ballot import List


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
