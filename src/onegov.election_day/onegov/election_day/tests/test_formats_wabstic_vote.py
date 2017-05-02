import tarfile

from datetime import date
from io import BytesIO
from onegov.ballot import Vote
from onegov.core.utils import module_path
from onegov.election_day.formats import import_vote_wabstic
from onegov.election_day.models import Principal
from pytest import mark


@mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/wabstic_vote.tar.gz'),
])
def test_import_wabstic_vote(session, tar_file):

    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()

    # The tar file contains vote results from the 12.02.2017:
    #   3 federal votes (canton SG)
    #   7 communal votes
    with tarfile.open(tar_file, 'r|gz') as f:
        sgstatic_gemeinden = f.extractfile(f.next()).read()
        sgstatic_geschaefte = f.extractfile(f.next()).read()
        sg_gemeinden = f.extractfile(f.next()).read()
        sg_geschaefte = f.extractfile(f.next()).read()

    assert sgstatic_gemeinden  # we don't need this file atm
    assert sgstatic_geschaefte  # we don't need this file atm

    # Test cantonal results
    principal = Principal('sg', '', '', canton='sg')
    for number, yeas, completed in (
        ('1', 70821, True),
        ('2', 84247, False),
        ('3', 57653, True)
    ):
        entities = principal.entities.get(vote.date.year, {})
        errors = import_vote_wabstic(
            vote, '1', number, entities,
            BytesIO(sg_geschaefte), 'text/plain',
            BytesIO(sg_gemeinden), 'text/plain'
        )
        assert not errors
        assert vote.completed == completed
        assert vote.ballots.one().results.count() == 78
        assert vote.yeas == yeas

    # Test communal results
    vote.domain = 'municipality'
    for district, number, entity_id, yeas in (
        ('3', '1', 3204, 1871),
        ('43', '1', 3292, 743),
        ('66', '1', 3352, 1167),
        # todo: are the data wrong??
        # ('68', '1', 3374, 189),
        # ('68', '1', 3374, 337),
        ('69', '1', 3375, 365),
        ('83', '1', 3402, 1596),
    ):
        principal = Principal(str(entity_id), '', '', municipality=entity_id)
        entities = principal.entities.get(vote.date.year, {})
        errors = import_vote_wabstic(
            vote, district, number, entities,
            BytesIO(sg_geschaefte), 'text/plain',
            BytesIO(sg_gemeinden), 'text/plain'
        )
        assert not errors
        assert vote.completed
        assert vote.ballots.one().results.one().yeas == yeas

    # Test communal results (missing)
    for district, number, entity_id, domain in (
        ('3', '1', 3204, 'federation'),  # domain missing
        ('300', '1', 3204, 'municipality'),  # district missing
        ('3', '5', 3204, 'municipality'),  # number missing
    ):
        vote.domain = domain
        principal = Principal(str(entity_id), '', '', municipality=entity_id)
        entities = principal.entities.get(vote.date.year, {})
        errors = import_vote_wabstic(
            vote, district, number, entities,
            BytesIO(sg_geschaefte), 'text/plain',
            BytesIO(sg_gemeinden), 'text/plain'
        )
        assert not errors
        assert not vote.completed
        assert not vote.ballots.one().results.one().counted
