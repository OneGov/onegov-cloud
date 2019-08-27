from datetime import date
from onegov.ballot import Candidate
from onegov.ballot import CandidateCollection
from onegov.ballot import Election


def test_candidates(session):
    election = Election(
        title="Election",
        domain='federation',
        date=date(2015, 6, 14)
    )
    election.candidates.append(
        Candidate(
            candidate_id='1',
            first_name='Hans',
            family_name='Müller',
            elected=False
        )
    )
    session.add(election)
    session.flush()

    collection = CandidateCollection(session)

    assert collection.query().count() == 1
    assert collection.by_id(election.candidates[0].id) == \
        election.candidates[0]
