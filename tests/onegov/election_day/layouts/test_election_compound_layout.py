from __future__ import annotations

from datetime import date
from freezegun import freeze_time
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionCompoundRelationship
from onegov.election_day.models import ElectionResult
from onegov.election_day.models import PartyPanachageResult
from onegov.election_day.models import PartyResult
from onegov.election_day.models import ProporzElection
from tests.onegov.election_day.common import DummyRequest
from unittest.mock import Mock


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_election_compound_layout_general(session: Session) -> None:
    date_ = date(2011, 1, 1)
    election = ProporzElection(title="election", domain='region', date=date_)
    session.add(election)
    session.add(ElectionCompound(title="e", domain='canton', date=date_))
    session.flush()
    compound = session.query(ElectionCompound).one()
    request: Any = DummyRequest()
    layout = ElectionCompoundLayout(compound, request)
    assert layout.all_tabs == (
        'seat-allocation',
        'list-groups',
        'superregions',
        'districts',
        'candidates',
        'party-strengths',
        'parties-panachage',
        'statistics',
        'data'
    )
    assert layout.title() == ''
    assert layout.title('undefined') == ''
    assert layout.title('seat-allocation') == 'Seat allocation'
    assert layout.title('list-groups') == 'List groups'
    assert layout.title('superregions') == '__superregions'
    assert layout.title('districts') == '__districts'
    assert layout.title('candidates') == 'Elected candidates'
    assert layout.title('party-strengths') == 'Party strengths'
    assert layout.title('parties-panachage') == 'Panachage'
    assert layout.title('data') == 'Downloads'
    assert layout.title('statistics') == 'Election statistics'
    assert layout.main_view == 'ElectionCompound/districts'
    assert layout.majorz is False
    assert layout.proporz is True
    assert layout.has_party_results is False
    assert layout.tab_visible('statistics') is False

    # test results
    compound.elections = [election]
    election.results.append(
        ElectionResult(
            name='1',
            entity_id=1,
            counted=True,
            eligible_voters=500,
        )
    )
    layout = ElectionCompoundLayout(compound, DummyRequest())  # type: ignore[arg-type]
    assert layout.has_results

    # test party results
    compound.party_results.append(
        PartyResult(
            year=2017,
            number_of_mandates=0,
            votes=10,
            total_votes=100,
            name_translations={'de_CH': 'A'},
            party_id='1'
        )
    )
    assert layout.has_party_results is True

    # test has_superregions
    layout = ElectionCompoundLayout(compound, request)
    assert layout.has_superregions is False

    request.app.principal.has_superregions = True
    layout = ElectionCompoundLayout(compound, request)
    assert layout.has_superregions is False

    compound.domain_elections = 'region'
    layout = ElectionCompoundLayout(compound, request)
    assert layout.has_superregions is True

    layout = ElectionCompoundLayout(compound, request)
    assert layout.main_view == 'ElectionCompound/superregions'

    compound.show_seat_allocation = True
    layout = ElectionCompoundLayout(compound, request)
    assert layout.main_view == 'ElectionCompound/seat-allocation'

    compound.show_seat_allocation = False
    compound.pukelsheim = True
    compound.show_list_groups = True
    layout = ElectionCompoundLayout(compound, request)
    assert layout.main_view == 'ElectionCompound/list-groups'

    # test file paths
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
        assert layout.pdf_path == f'pdf/elections-{ts}.de.pdf'
        assert layout.svg_path == f'svg/elections-{ts}.None.de.svg'
        assert layout.svg_link == 'ElectionCompound/None-svg'
        assert layout.svg_name == 'electioncompound.svg'

        layout = ElectionCompoundLayout(compound, request, 'seat-allocation')
        assert layout.pdf_path == f'pdf/elections-{ts}.de.pdf'
        assert layout.svg_path == f'svg/elections-{ts}.seat-allocation.de.svg'
        assert layout.svg_link == 'ElectionCompound/seat-allocation-svg'
        assert layout.svg_name == 'electioncompound-seat-allocation.svg'

        layout = ElectionCompoundLayout(compound, request, 'list-groups')
        assert layout.pdf_path == f'pdf/elections-{ts}.de.pdf'
        assert layout.svg_path == f'svg/elections-{ts}.list-groups.de.svg'
        assert layout.svg_link == 'ElectionCompound/list-groups-svg'
        assert layout.svg_name == 'electioncompound-list-groups.svg'

        layout = ElectionCompoundLayout(compound, request, 'party-strengths')
        assert layout.pdf_path == f'pdf/elections-{ts}.de.pdf'
        assert layout.svg_path == f'svg/elections-{ts}.party-strengths.de.svg'
        assert layout.svg_link == 'ElectionCompound/party-strengths-svg'
        assert layout.svg_name == 'electioncompound-party-strengths.svg'

        layout = ElectionCompoundLayout(compound, request, 'parties-panachage')
        assert layout.pdf_path == f'pdf/elections-{ts}.de.pdf'
        assert (
            layout.svg_path == f'svg/elections-{ts}.parties-panachage.de.svg'
        )
        assert layout.svg_link == 'ElectionCompound/parties-panachage-svg'
        assert layout.svg_name == 'electioncompound-panachage.svg'

    with freeze_time("2014-01-01 13:00"):
        second_compound = ElectionCompound(
            title='Second Compound',
            domain='federation',
            date=date(2011, 1, 1),
        )
        session.add(second_compound)
        session.flush()

        relationship = ElectionCompoundRelationship(
            source_id=compound.id,
            target_id=second_compound.id
        )
        session.add(relationship)
        session.flush()

        assert ElectionCompoundLayout(compound, request).related_compounds == [
            ('Second Compound', 'ElectionCompound/second-compound')
        ]
        assert ElectionCompoundLayout(
            second_compound, request
        ).related_compounds == []

    # test table links
    for tab, expected in (
        ('seat-allocation', 'ElectionCompound/seat-allocation-table'),
        ('list-groups', 'ElectionCompound/list-groups-table'),
        ('superregions', 'ElectionCompound/superregions-table'),
        ('districts', 'ElectionCompound/districts-table'),
        ('candidates', 'ElectionCompound/candidates-table'),
        ('party-strengths', 'ElectionCompound/party-strengths-table'),
        ('parties-panachage', None),
        ('statistics', 'ElectionCompound/statistics-table'),
        ('data', None)
    ):
        layout = ElectionCompoundLayout(compound, DummyRequest(), tab=tab)  # type: ignore[arg-type]
        assert not expected or f'{expected}?locale=de' == layout.table_link()


def test_election_compound_layout_menu(session: Session) -> None:
    election = ProporzElection(
        title="Election",
        domain='region',
        date=date(2011, 1, 1)
    )
    compound = ElectionCompound(
        title="Elections",
        domain='canton',
        date=date(2011, 1, 1)
    )
    session.add(election)
    session.add(compound)
    session.flush()
    compound.elections = [election]

    # No results yet
    request: Any = DummyRequest()
    assert ElectionCompoundLayout(compound, request).menu == []
    assert ElectionCompoundLayout(compound, request, 'data').menu == []

    # Results available
    election.results.append(
        ElectionResult(
            name='1',
            entity_id=1,
            counted=True,
            eligible_voters=500,
        )
    )
    assert ElectionCompoundLayout(compound, request).menu == [
        ('__districts', 'ElectionCompound/districts', False, []),
        ('Elected candidates', 'ElectionCompound/candidates', False, []),
        ('Election statistics', 'ElectionCompound/statistics', False, []),
        ('Downloads', 'ElectionCompound/data', False, [])
    ]
    assert ElectionCompoundLayout(compound, request, 'data').menu == [
        ('__districts', 'ElectionCompound/districts', False, []),
        ('Elected candidates', 'ElectionCompound/candidates', False, []),
        ('Election statistics', 'ElectionCompound/statistics', False, []),
        ('Downloads', 'ElectionCompound/data', True, [])
    ]

    # Party results available, but no views enabled
    compound.party_results.append(
        PartyResult(
            year=2017,
            number_of_mandates=0,
            votes=10,
            total_votes=100,
            name_translations={'de_CH': 'A'},
            party_id='1'
        )
    )
    compound.party_panachage_results.append(
        PartyPanachageResult(target='t', source='t ', votes=10)
    )
    assert ElectionCompoundLayout(compound, request).menu == [
        ('__districts', 'ElectionCompound/districts', False, []),
        ('Elected candidates', 'ElectionCompound/candidates', False, []),
        ('Election statistics', 'ElectionCompound/statistics', False, []),
        ('Downloads', 'ElectionCompound/data', False, [])
    ]

    # All views enabled
    request.app.principal.has_superregions = True
    compound.domain_elections = 'region'
    compound.pukelsheim = True
    compound.show_seat_allocation = True
    compound.show_list_groups = True
    compound.show_party_strengths = True
    compound.show_party_panachage = True
    assert ElectionCompoundLayout(compound, request).menu == [
        ('Seat allocation', 'ElectionCompound/seat-allocation', False, []),
        ('List groups', 'ElectionCompound/list-groups', False, []),
        ('__superregions', 'ElectionCompound/superregions', False, []),
        ('__regions', 'ElectionCompound/districts', False, []),
        ('Elected candidates', 'ElectionCompound/candidates', False, []),
        ('Party strengths', 'ElectionCompound/party-strengths', False, []),
        ('Panachage', 'ElectionCompound/parties-panachage', False, []),
        ('Election statistics', 'ElectionCompound/statistics', False, []),
        ('Downloads', 'ElectionCompound/data', False, [])
    ]

    # with horizontal_party_strengths
    compound.horizontal_party_strengths = True
    assert ElectionCompoundLayout(compound, request).menu == [
        ('Seat allocation', 'ElectionCompound/seat-allocation', False, []),
        ('Party strengths', 'ElectionCompound/party-strengths', False, []),
        ('List groups', 'ElectionCompound/list-groups', False, []),
        ('__superregions', 'ElectionCompound/superregions', False, []),
        ('__regions', 'ElectionCompound/districts', False, []),
        ('Elected candidates', 'ElectionCompound/candidates', False, []),
        ('Panachage', 'ElectionCompound/parties-panachage', False, []),
        ('Election statistics', 'ElectionCompound/statistics', False, []),
        ('Downloads', 'ElectionCompound/data', False, [])
    ]
