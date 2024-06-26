from datetime import date
from onegov.election_day.collections import ListCollection
from onegov.election_day.models import List
from onegov.election_day.models import ProporzElection


def test_lists(session):
    election = ProporzElection(
        title="Election",
        domain='federation',
        date=date(2015, 6, 14)
    )
    election.lists.append(
        List(
            list_id='1',
            name='Liberal Party',
            number_of_mandates=0
        )
    )
    session.add(election)
    session.flush()

    collection = ListCollection(session)

    assert collection.query().count() == 1
    assert collection.by_id(election.lists[0].id) == \
        election.lists[0]
