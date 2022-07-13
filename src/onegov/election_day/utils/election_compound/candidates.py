from datetime import date
from onegov.ballot import Candidate
from onegov.ballot import Election
from onegov.ballot import List
from onegov.core.utils import groupbylist
from statistics import mean


def get_elected_candidates(election_compound, session):
    """ Returns the elected candidates of an election compound. """

    election_ids = [election.id for election in election_compound.elections]

    elected = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.party,
        Candidate.gender,
        Candidate.year_of_birth,
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


def get_candidate_statistics(elected_candidates):

    year = date.today().year

    def statistics(values):
        age = [value[1] for value in values]
        age = None if not age or None in age else mean([v - year for v in age])
        return {'count': len(values), 'age': age}

    values = [
        (candidate.gender or 'undetermined', candidate.year_of_birth)
        for candidate in elected_candidates
    ]

    result = {'total': statistics(values)}
    values = sorted(values, key=lambda x: x[0])
    values = dict(groupbylist(values, key=lambda x: x[0]))
    result.update({gender: statistics(values[gender]) for gender in values})

    return result
