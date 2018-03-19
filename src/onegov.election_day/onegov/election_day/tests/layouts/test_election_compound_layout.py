from datetime import date
from onegov.ballot import Election
from onegov.ballot import ProporzElection
from onegov.ballot import ElectionCompound
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.tests import DummyRequest


def test_election_compound_layout(session):
    date_ = date(2011, 1, 1)
    session.add(Election(title="m", domain='region', date=date_))
    session.add(ProporzElection(title="p", domain='region', date=date_))
    session.add(ElectionCompound(title="e", domain='canton', date=date_))
    session.flush()
    compound = session.query(ElectionCompound).one()

    layout = ElectionCompoundLayout(compound, DummyRequest())
    assert layout.all_tabs == ('districts', 'candidates', 'parties', 'data')
    assert layout.title() == ''
    assert layout.title('undefined') == ''
    assert layout.title('districts') == '__districts'
    assert layout.title('candidates') == 'Elected candidates'
    assert layout.title('parties') == 'Parties'
    assert layout.title('data') == 'Downloads'
    assert layout.main_view == 'ElectionCompound/districts'
    assert list(layout.menu) == []
    assert layout.majorz is False
    assert layout.proporz is False

    compound.elections = ['m']
    layout = ElectionCompoundLayout(compound, DummyRequest())
    assert layout.majorz is True
    assert layout.proporz is False

    compound.elections = ['p']
    layout = ElectionCompoundLayout(compound, DummyRequest())
    assert layout.majorz is False
    assert layout.proporz is True
