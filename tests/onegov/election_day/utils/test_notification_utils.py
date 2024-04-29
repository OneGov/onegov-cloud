from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import Vote
from onegov.election_day.utils import segment_models
from onegov.core.utils import groupbylist


def test_segment_models():
    assert segment_models([], [], []) == []

    elections = [
        Election(domain='federation'),
        Election(domain='canton'),
        Election(domain='district'),
        Election(domain='district'),
    ]
    compounds = [
        ElectionCompound(domain='canton')
    ]
    votes = [
        Vote(domain='canton'),
        Vote(domain='municipality', domain_segment='A'),
        Vote(domain='municipality', domain_segment='B'),
    ]
    groups = segment_models(elections, compounds, votes)
    assert len(groups) == 4
    groups = dict(groupbylist(groups, lambda x: (x.domain, x.domain_segment)))

    def compile(group):
        return str(
            group.filter.compile(compile_kwargs={"literal_binds": True})
        )

    group = groups[(None, None)][0]
    assert group.elections == elections
    assert group.election_compounds == compounds
    assert group.votes == votes
    assert compile(group) == 'subscribers.domain IS NULL'

    group = groups[('canton', None)][0]
    assert group.elections == elections
    assert group.election_compounds == compounds
    assert group.votes == votes[:1]
    assert compile(group) == "subscribers.domain != 'municipality'"

    group = groups[('municipality', 'A')][0]
    assert group.elections == []
    assert group.election_compounds == []
    assert group.votes == votes[1:2]
    assert compile(group) == (
        "subscribers.domain = 'municipality' "
        "AND subscribers.domain_segment = 'A'"
    )

    group = groups[('municipality', 'B')][0]
    assert group.elections == []
    assert group.election_compounds == []
    assert group.votes == votes[2:3]
    assert compile(group) == (
        "subscribers.domain = 'municipality' "
        "AND subscribers.domain_segment = 'B'"
    )
