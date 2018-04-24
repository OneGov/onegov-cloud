from datetime import date
from freezegun import freeze_time
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import ProporzElection
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.tests.common import DummyRequest
from unittest.mock import Mock


def test_election_compound_layout(session):
    date_ = date(2011, 1, 1)
    session.add(Election(title="m", domain='region', date=date_))
    session.add(ProporzElection(title="p", domain='region', date=date_))
    session.add(ElectionCompound(title="e", domain='canton', date=date_))
    session.flush()
    compound = session.query(ElectionCompound).one()

    layout = ElectionCompoundLayout(compound, DummyRequest())
    assert layout.all_tabs == (
        'districts',
        'candidates',
        'party-strengths',
        'parties-panachage',
        'data'
    )
    assert layout.title() == ''
    assert layout.title('undefined') == ''
    assert layout.title('districts') == '__districts'
    assert layout.title('candidates') == 'Elected candidates'
    assert layout.title('party-strengths') == 'Party strengths'
    assert layout.title('parties-panachage') == 'Panachage (parties)'
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

    with freeze_time("2014-01-01 12:00"):
        compound = ElectionCompound(
            title="ElectionCompound",
            domain='canton',
            date=date(2011, 1, 1),
        )
        session.add(compound)
        session.flush()
        ts = (
            '2ef359817c8f8a7354e201f891cd7c11a13f4e025aa25239c3ad0cabe58bc49b'
            '.1388577600'
        )

        request = DummyRequest()
        request.app.filestorage = Mock()

        layout = ElectionCompoundLayout(compound, request)
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert layout.svg_path == f'svg/election-{ts}.None.any.svg'
        assert layout.svg_link == 'ElectionCompound/None-svg'
        assert layout.svg_name == 'electioncompound.svg'

        layout = ElectionCompoundLayout(compound, request, 'party-strengths')
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert layout.svg_path == f'svg/election-{ts}.party-strengths.any.svg'
        assert layout.svg_link == 'ElectionCompound/party-strengths-svg'
        assert layout.svg_name == 'electioncompound-party-strengths.svg'

        layout = ElectionCompoundLayout(compound, request, 'parties-panachage')
        assert layout.pdf_path == f'pdf/election-{ts}.de.pdf'
        assert (
            layout.svg_path == f'svg/election-{ts}.parties-panachage.any.svg'
        )
        assert layout.svg_link == 'ElectionCompound/parties-panachage-svg'
        assert layout.svg_name == 'electioncompound-panachage-parties.svg'
