from __future__ import annotations

import pytest

from csv import DictReader
from datetime import date
from datetime import datetime
from decimal import Decimal
from freezegun import freeze_time
from io import BytesIO
from io import StringIO
from onegov.core.orm.abstract import MoveDirection
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.collections import TranslatablePageCollection
from onegov.swissvotes.models import SwissVote
from openpyxl import load_workbook
from pytz import utc
from tests.shared.utils import use_locale


from typing import Any, IO, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.swissvotes.models import SwissVoteFile
    from sqlalchemy.orm import Session
    from .conftest import TestApp


def test_pages(session: Session) -> None:
    pages = TranslatablePageCollection(session)

    # setdefault
    static = ['home', 'disclaimer', 'imprint', 'data-protection']
    for id in reversed(static):
        pages.setdefault(id)
    assert [page.id for page in pages.query()] == static

    # add
    about = pages.add(
        id='about',
        title_translations={'en': "About", 'de': "Über"},
        content_translations={'en': "Placeholder", 'de': "Platzhalter"}
    )
    assert about.id == 'about'
    assert about.title_translations == {'en': "About", 'de': "Über"}
    assert about.content_translations == {
        'en': "Placeholder", 'de': "Platzhalter"
    }
    assert [page.id for page in pages.query()] == static + ['about']

    contact = pages.add(
        id='contact',
        title_translations={'en': "Contact", 'de': "Kontakt"},
        content_translations={'en': "Placeholder", 'de': "Platzhalter"}
    )
    dataset = pages.add(
        id='dataset',
        title_translations={'en': "Dataset", 'de': "Datensatz"},
        content_translations={'en': "Placeholder", 'de': "Platzhalter"}
    )
    assert [page.id for page in pages.query()] == static + [
        'about', 'contact', 'dataset'
    ]

    # move
    pages.move(dataset, about, MoveDirection.above)
    pages.move(about, contact, MoveDirection.below)
    assert [page.id for page in pages.query()] == static + [
        'dataset', 'contact', 'about'
    ]


def test_votes(swissvotes_app: TestApp) -> None:
    votes = SwissVoteCollection(swissvotes_app)
    assert votes.last_modified is None

    with freeze_time(datetime(2019, 1, 1, 10, tzinfo=utc)):
        vote = votes.add(
            id=1,
            bfs_number=Decimal('100.1'),
            date=date(1990, 6, 2),
            title_de="Vote DE",
            title_fr="Vote FR",
            short_title_de="V D",
            short_title_fr="V F",
            short_title_en="V E",
            _legal_form=1
        )

    assert vote.id == 1
    assert vote.bfs_number == Decimal('100.1')
    assert vote.date == date(1990, 6, 2)
    assert vote.title_de == "Vote DE"
    assert vote.title_fr == "Vote FR"
    assert vote.short_title_de == "V D"
    assert vote.short_title_fr == "V F"
    assert vote.short_title_en == "V E"
    assert vote.legal_form == "Mandatory referendum"

    assert votes.last_modified == datetime(2019, 1, 1, 10, tzinfo=utc)
    assert votes.by_bfs_number('100.1') == vote
    assert votes.by_bfs_number(Decimal('100.1')) == vote


def test_votes_default(swissvotes_app: TestApp) -> None:
    votes = SwissVoteCollection(
        swissvotes_app,
        page=2,
        from_date=3,  # type: ignore[arg-type]
        to_date=4,  # type: ignore[arg-type]
        legal_form=5,  # type: ignore[arg-type]
        result=6,  # type: ignore[arg-type]
        policy_area=7,  # type: ignore[arg-type]
        term=8,  # type: ignore[arg-type]
        full_text=9,  # type: ignore[arg-type]
        position_federal_council=10,  # type: ignore[arg-type]
        position_national_council=11,  # type: ignore[arg-type]
        position_council_of_states=12,  # type: ignore[arg-type]
        sort_by=13,  # type: ignore[arg-type]
        sort_order=14  # type: ignore[arg-type]
    )
    assert votes.page == 2
    assert votes.from_date == 3
    assert votes.to_date == 4
    assert votes.legal_form == 5  # type: ignore[comparison-overlap]
    assert votes.result == 6  # type: ignore[comparison-overlap]
    assert votes.policy_area == 7  # type: ignore[comparison-overlap]
    assert votes.term == 8  # type: ignore[comparison-overlap]
    assert votes.full_text == 9
    assert votes.position_federal_council == 10  # type: ignore[comparison-overlap]
    assert votes.position_national_council == 11  # type: ignore[comparison-overlap]
    assert votes.position_council_of_states == 12  # type: ignore[comparison-overlap]
    assert votes.sort_by == 13  # type: ignore[comparison-overlap]
    assert votes.sort_order == 14  # type: ignore[comparison-overlap]

    votes = votes.default()
    assert votes.page == 0
    assert votes.from_date is None
    assert votes.to_date is None
    assert votes.legal_form is None
    assert votes.result is None
    assert votes.policy_area is None
    assert votes.term is None
    assert votes.full_text is None
    assert votes.position_federal_council is None
    assert votes.position_national_council is None
    assert votes.position_council_of_states is None
    assert votes.sort_by is None
    assert votes.sort_order is None


def test_votes_pagination(swissvotes_app: TestApp) -> None:
    votes = SwissVoteCollection(swissvotes_app)

    assert votes.pages_count == 0
    assert votes.batch == ()
    assert votes.page_index == 0
    assert votes.offset == 0
    assert votes.previous is None
    assert votes.next is None
    assert votes.page_by_index(0) == votes

    for id_ in range(26):
        votes.add(
            id=id_,
            bfs_number=Decimal(f'{id_}'),
            date=date(1990, 6, 2),
            title_de="Vote",
            title_fr="Vote",
            short_title_de="Vote",
            short_title_fr="Vote",
            short_title_en="Vote",
            _legal_form=1
        )

    votes = SwissVoteCollection(swissvotes_app)
    assert votes.query().count() == 26
    assert votes.subset_count == 26
    assert votes.pages_count == 2
    assert len(votes.batch) == 20
    assert votes.page_index == 0
    assert votes.offset == 0
    assert votes.previous is None
    assert votes.next == votes.page_by_index(1)
    assert votes.page_by_index(0) == votes

    assert votes.next.page_index == 1
    assert len(votes.next.batch) == 6
    assert votes.next.previous == votes


def test_votes_pagination_negative_page_index(swissvotes_app: TestApp) -> None:
    swissvotes = SwissVoteCollection(swissvotes_app, page=-9)
    assert swissvotes.page == 0
    assert swissvotes.page_index == 0
    assert swissvotes.page_by_index(-2).page == 0
    assert swissvotes.page_by_index(-3).page_index == 0

    with pytest.raises(AssertionError):
        SwissVoteCollection(swissvotes_app, page=None)  # type: ignore[arg-type]


def test_votes_term_filter(swissvotes_app: TestApp) -> None:
    assert SwissVoteCollection(swissvotes_app).term_filter == []
    assert SwissVoteCollection(swissvotes_app, term='').term_filter == []
    assert SwissVoteCollection(swissvotes_app, term='', full_text=True)\
        .term_filter == []

    def compiled(**kwargs: Any) -> list[str]:
        list_ = SwissVoteCollection(swissvotes_app, **kwargs).term_filter
        return [
            str(statement.compile(compile_kwargs={"literal_binds": True}))
            for statement in list_
        ]

    c_title_de = "to_tsvector('german', swissvotes.title_de)"
    c_title_fr = "to_tsvector('french', swissvotes.title_fr)"
    c_short_title_de = "to_tsvector('german', swissvotes.short_title_de)"
    c_short_title_fr = "to_tsvector('french', swissvotes.short_title_fr)"
    c_short_title_en = "to_tsvector('english', swissvotes.short_title_en)"
    c_keyword = "to_tsvector('german', swissvotes.keyword)"
    c_initiator_de = "to_tsvector('german', swissvotes.initiator_de)"
    c_initiator_fr = "to_tsvector('french', swissvotes.initiator_fr)"
    c_text_de = 'swissvotes."searchable_text_de_CH"'
    c_text_fr = 'swissvotes."searchable_text_fr_CH"'
    c_text_it = 'swissvotes."searchable_text_it_CH"'
    c_text_en = 'swissvotes."searchable_text_en_US"'

    assert compiled(term='987') == [
        'swissvotes.bfs_number = 987',
        "swissvotes.procedure_number = '987'",
        f"{c_title_de} @@ to_tsquery('german', '987')",
        f"{c_title_fr} @@ to_tsquery('french', '987')",
        f"{c_short_title_de} @@ to_tsquery('german', '987')",
        f"{c_short_title_fr} @@ to_tsquery('french', '987')",
        f"{c_short_title_en} @@ to_tsquery('english', '987')",
        f"{c_keyword} @@ to_tsquery('german', '987')",
    ]

    assert compiled(term='17.060') == [
        'swissvotes.bfs_number = 17.060',
        "swissvotes.procedure_number = '17.060'",
        f"{c_title_de} @@ to_tsquery('german', '17.060')",
        f"{c_title_fr} @@ to_tsquery('french', '17.060')",
        f"{c_short_title_de} @@ to_tsquery('german', '17.060')",
        f"{c_short_title_fr} @@ to_tsquery('french', '17.060')",
        f"{c_short_title_en} @@ to_tsquery('english', '17.060')",
        f"{c_keyword} @@ to_tsquery('german', '17.060')",
    ]

    assert compiled(term='17.12.2004') == [
        f"{c_title_de} @@ to_tsquery('german', '17.12.2004')",
        f"{c_title_fr} @@ to_tsquery('french', '17.12.2004')",
        f"{c_short_title_de} @@ to_tsquery('german', '17.12.2004')",
        f"{c_short_title_fr} @@ to_tsquery('french', '17.12.2004')",
        f"{c_short_title_en} @@ to_tsquery('english', '17.12.2004')",
        f"{c_keyword} @@ to_tsquery('german', '17.12.2004')",
    ]

    assert compiled(term='1893_002') == [
        "swissvotes.procedure_number = '1893_002'",
        f"{c_title_de} @@ to_tsquery('german', '1893002')",
        f"{c_title_fr} @@ to_tsquery('french', '1893002')",
        f"{c_short_title_de} @@ to_tsquery('german', '1893002')",
        f"{c_short_title_fr} @@ to_tsquery('french', '1893002')",
        f"{c_short_title_en} @@ to_tsquery('english', '1893002')",
        f"{c_keyword} @@ to_tsquery('german', '1893002')",
    ]

    assert compiled(term='abc') == [
        f"{c_title_de} @@ to_tsquery('german', 'abc')",
        f"{c_title_fr} @@ to_tsquery('french', 'abc')",
        f"{c_short_title_de} @@ to_tsquery('german', 'abc')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'abc')",
        f"{c_short_title_en} @@ to_tsquery('english', 'abc')",
        f"{c_keyword} @@ to_tsquery('german', 'abc')",
    ]
    assert compiled(term='abc', full_text=True) == [
        f"{c_title_de} @@ to_tsquery('german', 'abc')",
        f"{c_title_fr} @@ to_tsquery('french', 'abc')",
        f"{c_short_title_de} @@ to_tsquery('german', 'abc')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'abc')",
        f"{c_short_title_en} @@ to_tsquery('english', 'abc')",
        f"{c_keyword} @@ to_tsquery('german', 'abc')",
        f"{c_initiator_de} @@ to_tsquery('german', 'abc')",
        f"{c_initiator_fr} @@ to_tsquery('french', 'abc')",
        f"{c_text_de} @@ to_tsquery('german', 'abc')",
        f"{c_text_fr} @@ to_tsquery('french', 'abc')",
        f"{c_text_it} @@ to_tsquery('italian', 'abc')",
        f"{c_text_en} @@ to_tsquery('english', 'abc')",
    ]

    assert compiled(term='Müller') == [
        f"{c_title_de} @@ to_tsquery('german', 'Müller')",
        f"{c_title_fr} @@ to_tsquery('french', 'Müller')",
        f"{c_short_title_de} @@ to_tsquery('german', 'Müller')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'Müller')",
        f"{c_short_title_en} @@ to_tsquery('english', 'Müller')",
        f"{c_keyword} @@ to_tsquery('german', 'Müller')",
    ]

    assert compiled(term='20,20') == [
        f"{c_title_de} @@ to_tsquery('german', '20,20')",
        f"{c_title_fr} @@ to_tsquery('french', '20,20')",
        f"{c_short_title_de} @@ to_tsquery('german', '20,20')",
        f"{c_short_title_fr} @@ to_tsquery('french', '20,20')",
        f"{c_short_title_en} @@ to_tsquery('english', '20,20')",
        f"{c_keyword} @@ to_tsquery('german', '20,20')",
    ]

    assert compiled(term='Neu!') == [
        f"{c_title_de} @@ to_tsquery('german', 'Neu')",
        f"{c_title_fr} @@ to_tsquery('french', 'Neu')",
        f"{c_short_title_de} @@ to_tsquery('german', 'Neu')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'Neu')",
        f"{c_short_title_en} @@ to_tsquery('english', 'Neu')",
        f"{c_keyword} @@ to_tsquery('german', 'Neu')",
    ]

    assert compiled(term='H P Müller') == [
        f"{c_title_de} @@ to_tsquery('german', 'H <-> P <-> Müller')",
        f"{c_title_fr} @@ to_tsquery('french', 'H <-> P <-> Müller')",
        f"{c_short_title_de} @@ to_tsquery('german', 'H <-> P <-> Müller')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'H <-> P <-> Müller')",
        f"{c_short_title_en} @@ to_tsquery('english', 'H <-> P <-> Müller')",
        f"{c_keyword} @@ to_tsquery('german', 'H <-> P <-> Müller')",
    ]

    assert compiled(term='x AND y') == [
        f"{c_title_de} @@ to_tsquery('german', 'x <-> AND <-> y')",
        f"{c_title_fr} @@ to_tsquery('french', 'x <-> AND <-> y')",
        f"{c_short_title_de} @@ to_tsquery('german', 'x <-> AND <-> y')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'x <-> AND <-> y')",
        f"{c_short_title_en} @@ to_tsquery('english', 'x <-> AND <-> y')",
        f"{c_keyword} @@ to_tsquery('german', 'x <-> AND <-> y')",
    ]

    assert compiled(term='x | y') == [
        f"{c_title_de} @@ to_tsquery('german', 'x <-> y')",
        f"{c_title_fr} @@ to_tsquery('french', 'x <-> y')",
        f"{c_short_title_de} @@ to_tsquery('german', 'x <-> y')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'x <-> y')",
        f"{c_short_title_en} @@ to_tsquery('english', 'x <-> y')",
        f"{c_keyword} @@ to_tsquery('german', 'x <-> y')",
    ]

    assert compiled(term='y ! y') == [
        f"{c_title_de} @@ to_tsquery('german', 'y <-> y')",
        f"{c_title_fr} @@ to_tsquery('french', 'y <-> y')",
        f"{c_short_title_de} @@ to_tsquery('german', 'y <-> y')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'y <-> y')",
        f"{c_short_title_en} @@ to_tsquery('english', 'y <-> y')",
        f"{c_keyword} @@ to_tsquery('german', 'y <-> y')",
    ]


def test_votes_query(swissvotes_app: TestApp) -> None:
    votes = SwissVoteCollection(swissvotes_app)
    vote_1 = votes.add(
        id=1,
        bfs_number=Decimal('100'),
        date=date(1990, 6, 2),
        title_de="Abstimmung über diese Sache",
        title_fr="Vote sur cette question",
        short_title_de="diese Sache",
        short_title_fr="cette question",
        short_title_en="this thing",
        _legal_form=1,
        descriptor_1_level_1=Decimal('4'),
        descriptor_1_level_2=Decimal('4.2'),
        descriptor_1_level_3=Decimal('4.21'),
        descriptor_2_level_1=Decimal('10'),
        descriptor_2_level_2=Decimal('10.3'),
        descriptor_2_level_3=Decimal('10.35'),
        descriptor_3_level_1=Decimal('10'),
        descriptor_3_level_2=Decimal('10.3'),
        descriptor_3_level_3=Decimal('10.33'),
        _position_federal_council=3,
        _position_council_of_states=1,
        _position_national_council=2,
        _result=1,
    )
    votes.add(
        id=2,
        bfs_number=Decimal('200.1'),
        date=date(1990, 9, 2),
        title_de="Wir wollen diese Version die Sache",
        title_fr="Nous voulons cette version de la chose",
        short_title_de="diese Version",
        short_title_fr="cette version",
        short_title_en="that version",
        keyword="Variant A of X",
        initiator_de="Urheber",
        initiator_fr="Initiant",
        _legal_form=2,
        descriptor_1_level_1=Decimal('10'),
        descriptor_1_level_2=Decimal('10.3'),
        descriptor_1_level_3=Decimal('10.35'),
        descriptor_2_level_1=Decimal('1'),
        descriptor_2_level_2=Decimal('1.6'),
        descriptor_2_level_3=Decimal('1.62'),
        _position_federal_council=2,
        _position_council_of_states=2,
        _position_national_council=1,
        _result=1
    )
    votes.add(
        id=3,
        bfs_number=Decimal('200.2'),
        date=date(1990, 9, 2),
        title_de="Wir wollen nochmal etwas anderes",
        title_fr="Nous voulons encore une autre version de la chose",
        short_title_de="Nochmals etwas anderes",
        short_title_fr="encore une autre version",
        short_title_en="something else again",
        keyword="Variant B of X",
        _legal_form=2,
        descriptor_3_level_1=Decimal('8'),
        descriptor_3_level_2=Decimal('8.3'),
        _position_federal_council=1,
        _position_council_of_states=1,
        _position_national_council=1,
        _result=2
    )

    def count(**kwargs: Any) -> int:
        return SwissVoteCollection(swissvotes_app, **kwargs).query().count()

    assert count() == 3

    assert count(from_date=date(1900, 1, 1)) == 3
    assert count(from_date=date(1990, 6, 2)) == 3
    assert count(from_date=date(1990, 9, 2)) == 2
    assert count(from_date=date(1991, 3, 2)) == 0
    assert count(to_date=date(1900, 1, 1)) == 0
    assert count(to_date=date(1990, 6, 2)) == 1
    assert count(to_date=date(1990, 9, 2)) == 3
    assert count(to_date=date(1991, 3, 2)) == 3
    assert count(from_date=date(1990, 6, 2), to_date=date(1990, 6, 2)) == 1
    assert count(from_date=date(1990, 6, 2), to_date=date(1990, 9, 2)) == 3
    assert count(from_date=date(1990, 9, 2), to_date=date(1990, 6, 2)) == 0

    assert count(legal_form=[]) == 3
    assert count(legal_form=[1]) == 1
    assert count(legal_form=[2]) == 2
    assert count(legal_form=[1, 2]) == 3
    assert count(legal_form=[3]) == 0

    assert count(result=[]) == 3
    assert count(result=[1]) == 2
    assert count(result=[2]) == 1
    assert count(result=[1, 2]) == 3
    assert count(result=[3]) == 0

    assert count(position_federal_council=[]) == 3
    assert count(position_federal_council=[1]) == 1
    assert count(position_federal_council=[2]) == 1
    assert count(position_federal_council=[1, 2]) == 2
    assert count(position_federal_council=[3]) == 1

    assert count(position_council_of_states=[]) == 3
    assert count(position_council_of_states=[1]) == 2
    assert count(position_council_of_states=[2]) == 1
    assert count(position_council_of_states=[1, 2]) == 3
    assert count(position_council_of_states=[3]) == 0

    assert count(position_national_council=[]) == 3
    assert count(position_national_council=[1]) == 2
    assert count(position_national_council=[2]) == 1
    assert count(position_national_council=[1, 2]) == 3
    assert count(position_national_council=[3]) == 0

    assert count(policy_area=['1']) == 1
    assert count(policy_area=['4']) == 1
    assert count(policy_area=['8']) == 1
    assert count(policy_area=['10']) == 2
    assert count(policy_area=['1', '4']) == 2
    assert count(policy_area=['8', '10']) == 3
    assert count(policy_area=['1', '8', '10']) == 3
    assert count(policy_area=['1', '4', '8', '10']) == 3
    assert count(policy_area=['4.42']) == 1
    assert count(policy_area=['4.42.421']) == 1
    assert count(policy_area=['4.42.421', '10']) == 1
    assert count(policy_area=['4.42.421', '10.103']) == 1
    assert count(policy_area=['4.42.421', '10.103.1033']) == 1
    assert count(policy_area=['4.42.421', '10.103.1035']) == 2

    assert count(term='Abstimmung') == 1
    assert count(term='cette question') == 1
    assert count(term='version') == 2
    assert count(term='encore') == 1
    assert count(term='thing') == 1
    assert count(term='something') == 1
    assert count(term='riant') == 0
    assert count(term='A of X') == 1
    assert count(term='urheber') == 0
    assert count(term='Urheber', full_text=True) == 1
    assert count(term='Initiant', full_text=True) == 1

    # test tie-breaker
    vote_1._legal_form = 5
    vote_1._position_federal_council = 8
    vote_1._position_council_of_states = 8
    vote_1._position_national_council = 8
    assert count(legal_form=[5], position_federal_council=[2]) == 1
    assert count(legal_form=[5], position_federal_council=[8]) == 1
    assert count(legal_form=[5], position_federal_council=[1]) == 0
    assert count(legal_form=[5], position_federal_council=[9]) == 0
    assert count(legal_form=[5], position_council_of_states=[2]) == 1
    assert count(legal_form=[5], position_council_of_states=[8]) == 1
    assert count(legal_form=[5], position_council_of_states=[1]) == 0
    assert count(legal_form=[5], position_council_of_states=[9]) == 0
    assert count(legal_form=[5], position_national_council=[2]) == 1
    assert count(legal_form=[5], position_national_council=[8]) == 1
    assert count(legal_form=[5], position_national_council=[1]) == 0
    assert count(legal_form=[5], position_national_council=[9]) == 0

    vote_1._position_federal_council = 9
    vote_1._position_council_of_states = 9
    vote_1._position_national_council = 9
    assert count(legal_form=[5], position_federal_council=[2]) == 0
    assert count(legal_form=[5], position_federal_council=[8]) == 0
    assert count(legal_form=[5], position_federal_council=[1]) == 1
    assert count(legal_form=[5], position_federal_council=[9]) == 1
    assert count(legal_form=[5], position_council_of_states=[2]) == 0
    assert count(legal_form=[5], position_council_of_states=[8]) == 0
    assert count(legal_form=[5], position_council_of_states=[1]) == 1
    assert count(legal_form=[5], position_council_of_states=[9]) == 1
    assert count(legal_form=[5], position_national_council=[2]) == 0
    assert count(legal_form=[5], position_national_council=[8]) == 0
    assert count(legal_form=[5], position_national_council=[1]) == 1
    assert count(legal_form=[5], position_national_council=[9]) == 1


def test_votes_query_attachments(
    swissvotes_app: TestApp,
    postgres_version: str,
    attachments: dict[str, SwissVoteFile],
    campaign_material: dict[str, SwissVoteFile]
) -> None:
    votes = SwissVoteCollection(swissvotes_app)
    votes.add(
        id=1,
        bfs_number=Decimal('100'),
        date=date(1990, 6, 2),
        title_de="Vote on that one thing",
        title_fr="Vote on that one thing",
        short_title_de="Vote on that one thing",
        short_title_fr="Vote on that one thing",
        short_title_en="Vote on that one thing",
        _legal_form=1,
    )
    votes.add(
        id=2,
        bfs_number=Decimal('200.1'),
        date=date(1990, 9, 2),
        title_de="We want this version the thing",
        title_fr="We want this version the thing",
        short_title_de="We want this version the thing",
        short_title_fr="We want this version the thing",
        short_title_en="We want this version the thing",
        _legal_form=2,
    )
    vote = votes.add(
        id=3,
        bfs_number=Decimal('200.2'),
        date=date(1990, 9, 2),
        title_de="We want that version of the thing",
        title_fr="We want that version of the thing",
        short_title_de="We want that version of the thing",
        short_title_fr="We want that version of the thing",
        short_title_en="We want that version of the thing",
        _legal_form=2,
    )
    for name, attachment in attachments.items():
        setattr(vote, name, attachment)
    vote.campaign_material_metadata = {
        'campaign_material_other-essay': {'language': ['de']},
        'campaign_material_other-leaflet': {'language': ['it']},
    }
    vote.files.append(campaign_material['campaign_material_other-essay.pdf'])
    vote.files.append(campaign_material['campaign_material_other-leaflet.pdf'])
    votes.session.flush()

    def count(**kwargs: Any) -> int:
        return SwissVoteCollection(swissvotes_app, **kwargs).query().count()

    assert count() == 3

    assert count(term='Abstimmungstext') == 0
    assert count(term='Abstimmungstext', full_text=True) == 1
    assert count(term='Abst*', full_text=True) == 1
    assert count(term='conseil', full_text=True) == 1
    assert count(term='Parlamentdebatte', full_text=True) == 1
    assert count(term='Réalisation', full_text=True) == 1
    assert count(term='booklet', full_text=True) == 0
    assert count(term='Abhandlung', full_text=True) == 1
    assert count(term='Volantino', full_text=True) == 1
    assert count(term='volantinare', full_text=True) == 1
    assert count(term='Volantini', full_text=True) == 1


def test_votes_order(swissvotes_app: TestApp) -> None:
    votes = SwissVoteCollection(swissvotes_app)

    for index, title in enumerate(('Firsţ', 'Śecond', 'Thirḓ'), start=1):
        votes.add(
            id=index,
            bfs_number=Decimal(str(index)),
            date=date(1990, 6, index),
            title_de=title,
            title_fr=''.join(reversed(title)),
            short_title_de=title,
            short_title_fr=''.join(reversed(title)),
            short_title_en=''.join(reversed(title)),
            _legal_form=index,
            _result=index,
            result_people_yeas_p=index / 10,
            result_turnout=index / 10
        )

    assert votes.sort_order_by_key('date') == 'descending'
    assert votes.sort_order_by_key('legal_form') == 'unsorted'
    assert votes.sort_order_by_key('result') == 'unsorted'
    assert votes.sort_order_by_key('result_people_yeas_p') == 'unsorted'
    assert votes.sort_order_by_key('result_turnout') == 'unsorted'
    assert votes.sort_order_by_key('title') == 'unsorted'
    assert votes.sort_order_by_key('invalid') == 'unsorted'

    votes = SwissVoteCollection(swissvotes_app, sort_by='', sort_order='')
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'

    votes = SwissVoteCollection(swissvotes_app, sort_by='xx', sort_order='yy')
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'

    votes = SwissVoteCollection(swissvotes_app, sort_by='date',
                                sort_order='yy')
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'

    votes = SwissVoteCollection(swissvotes_app, sort_by='xx',
                                sort_order='ascending')
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'

    votes = SwissVoteCollection(swissvotes_app, sort_by='result',
                                sort_order='yy')
    assert votes.current_sort_by == 'result'
    assert votes.current_sort_order == 'ascending'

    votes = SwissVoteCollection(swissvotes_app)
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'
    assert 'date' in str(votes.order_by)
    assert 'DESC' in str(votes.order_by)
    assert [vote.id for vote in votes.query()] == [3, 2, 1]

    votes = votes.by_order('date')
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'ascending'
    assert 'date' in str(votes.order_by)
    assert [vote.id for vote in votes.query()] == [1, 2, 3]

    votes = votes.by_order('legal_form')
    assert votes.current_sort_by == 'legal_form'
    assert votes.current_sort_order == 'ascending'
    assert 'legal_form' in str(votes.order_by)
    assert [vote.id for vote in votes.query()] == [1, 2, 3]

    votes = votes.by_order('legal_form')
    assert votes.current_sort_by == 'legal_form'
    assert votes.current_sort_order == 'descending'
    assert 'legal_form' in str(votes.order_by)
    assert 'DESC' in str(votes.order_by)
    assert [vote.id for vote in votes.query()] == [3, 2, 1]

    votes = votes.by_order('result')
    assert votes.current_sort_by == 'result'
    assert votes.current_sort_order == 'ascending'
    assert 'result' in str(votes.order_by)
    assert [vote.id for vote in votes.query()] == [1, 2, 3]

    votes = votes.by_order('result')
    assert votes.current_sort_by == 'result'
    assert votes.current_sort_order == 'descending'
    assert 'result' in str(votes.order_by)
    assert 'DESC' in str(votes.order_by)
    assert [vote.id for vote in votes.query()] == [3, 2, 1]

    votes = votes.by_order('result_people_yeas_p')
    assert votes.current_sort_by == 'result_people_yeas_p'
    assert votes.current_sort_order == 'ascending'
    assert 'result_people_yeas_p' in str(votes.order_by)
    assert [vote.id for vote in votes.query()] == [1, 2, 3]

    votes = votes.by_order('result_people_yeas_p')
    assert votes.current_sort_by == 'result_people_yeas_p'
    assert votes.current_sort_order == 'descending'
    assert 'result_people_yeas_p' in str(votes.order_by)
    assert 'DESC' in str(votes.order_by)
    assert [vote.id for vote in votes.query()] == [3, 2, 1]

    votes = votes.by_order('result_turnout')
    assert votes.current_sort_by == 'result_turnout'
    assert votes.current_sort_order == 'ascending'
    assert 'result_turnout' in str(votes.order_by)
    assert [vote.id for vote in votes.query()] == [1, 2, 3]

    votes = votes.by_order('result_turnout')
    assert votes.current_sort_by == 'result_turnout'
    assert votes.current_sort_order == 'descending'
    assert 'result_turnout' in str(votes.order_by)
    assert 'DESC' in str(votes.order_by)
    assert [vote.id for vote in votes.query()] == [3, 2, 1]

    votes = votes.by_order('title')
    assert votes.current_sort_by == 'title'
    assert votes.current_sort_order == 'ascending'
    assert 'title' in str(votes.order_by)
    assert [vote.id for vote in votes.query()] == [1, 2, 3]

    votes = votes.by_order('title')
    assert votes.current_sort_by == 'title'
    assert votes.current_sort_order == 'descending'
    assert 'title' in str(votes.order_by)
    assert 'DESC' in str(votes.order_by)
    assert [vote.id for vote in votes.query()] == [3, 2, 1]

    with use_locale(votes.app, 'fr_CH'):
        assert [vote.id for vote in votes.query()] == [1, 3, 2]

    votes = votes.by_order(None)
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'

    votes = votes.by_order('')
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'

    votes = votes.by_order('xxx')
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'


def test_votes_available_descriptors(swissvotes_app: TestApp) -> None:
    votes = SwissVoteCollection(swissvotes_app)
    assert votes.available_descriptors == [set(), set(), set()]

    votes.add(
        id=1,
        bfs_number=Decimal('1'),
        date=date(1990, 6, 2),
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        short_title_en="Vote",
        _legal_form=1,
        descriptor_1_level_1=Decimal('4'),
        descriptor_1_level_2=Decimal('4.2'),
        descriptor_1_level_3=Decimal('4.21'),
        descriptor_2_level_1=Decimal('10'),
        descriptor_2_level_2=Decimal('10.3'),
        descriptor_2_level_3=Decimal('10.35'),
        descriptor_3_level_1=Decimal('10'),
        descriptor_3_level_2=Decimal('10.3'),
        descriptor_3_level_3=Decimal('10.33'),
    )
    votes.add(
        id=2,
        bfs_number=Decimal('2'),
        date=date(1990, 6, 2),
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        short_title_en="Vote",
        _legal_form=1,
        descriptor_1_level_1=Decimal('10'),
        descriptor_1_level_2=Decimal('10.3'),
        descriptor_1_level_3=Decimal('10.35'),
        descriptor_2_level_1=Decimal('1'),
        descriptor_2_level_2=Decimal('1.6'),
        descriptor_2_level_3=Decimal('1.62'),
    )
    votes.add(
        id=3,
        bfs_number=Decimal('3'),
        date=date(1990, 6, 2),
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        short_title_en="Vote",
        _legal_form=1,
        descriptor_3_level_1=Decimal('8'),
        descriptor_3_level_2=Decimal('8.3'),
    )

    assert SwissVoteCollection(swissvotes_app).available_descriptors == [
        {Decimal('1.00'), Decimal('4.00'), Decimal('8.00'), Decimal('10.00')},
        {Decimal('1.60'), Decimal('4.20'), Decimal('8.30'), Decimal('10.30')},
        {Decimal('1.62'), Decimal('4.21'), Decimal('10.33'), Decimal('10.35')}
    ]


def test_votes_update(swissvotes_app: TestApp) -> None:
    votes = SwissVoteCollection(swissvotes_app)

    added, updated = votes.update([
        SwissVote(
            bfs_number=Decimal('1'),
            date=date(1990, 6, 1),
            title_de="First",
            title_fr="First",
            short_title_de="First",
            short_title_fr="First",
            short_title_en="First",
            _legal_form=1,
        ),
        SwissVote(
            bfs_number=Decimal('2'),
            date=date(1990, 6, 1),
            title_de="Second",
            title_fr="Second",
            short_title_de="Second",
            short_title_fr="Second",
            short_title_en="Second",
            _legal_form=1,
        )
    ])
    assert added == 2
    assert updated == 0
    assert votes.query().count() == 2

    added, updated = votes.update([
        SwissVote(
            bfs_number=Decimal('1'),
            date=date(1990, 6, 1),
            title_de="First",
            title_fr="First",
            short_title_de="First",
            short_title_fr="First",
            short_title_en="First",
            _legal_form=1,
        )
    ])
    assert added == 0
    assert updated == 0

    added, updated = votes.update([
        SwissVote(
            bfs_number=Decimal('1'),
            date=date(1990, 6, 1),
            title_de="First vote",
            title_fr="First vote",
            short_title_de="First vote",
            short_title_fr="First vote",
            short_title_en="First vote",
            _legal_form=1,
        )
    ])
    assert added == 0
    assert updated == 1
    assert votes.by_bfs_number(Decimal('1')).title == 'First vote'  # type: ignore[union-attr]


def test_votes_update_metadata(swissvotes_app: TestApp) -> None:
    votes = SwissVoteCollection(swissvotes_app)
    vote_1 = votes.add(
        bfs_number=Decimal('1'),
        date=date(1990, 6, 1),
        title_de="First",
        title_fr="First",
        short_title_de="First",
        short_title_fr="First",
        short_title_en="First",
        _legal_form=1,
    )
    vote_2 = votes.add(
        bfs_number=Decimal('2'),
        date=date(1990, 6, 1),
        title_de="Second",
        title_fr="Second",
        short_title_de="Second",
        short_title_fr="Second",
        short_title_en="Second",
        _legal_form=1,
    )

    added, updated = votes.update_metadata({
        Decimal('1'): {
            'essay.pdf': {'a': 10, 'b': 11},
            'leafet.pdf': {'a': 20, 'c': 21},
        },
        Decimal('3'): {
            'article.pdf': {'a': 30, 'b': 31},
        },
    })
    assert added == 2
    assert updated == 0

    added, updated = votes.update_metadata({
        Decimal('1'): {
            'essay.pdf': {'a': 10, 'b': 12},
            'letter.pdf': {'a': 40},
        },
        Decimal('2'): {
            'legal.pdf': {'a': 40},
        },
        Decimal('3'): {
            'article.pdf': {'a': 30, 'b': 31},
        },
    })
    assert added == 2
    assert updated == 1

    assert vote_1.campaign_material_metadata == {
        'essay.pdf': {'a': 10, 'b': 12},
        'leafet.pdf': {'a': 20, 'c': 21},
        'letter.pdf': {'a': 40}
    }
    assert vote_2.campaign_material_metadata == {
        'legal.pdf': {'a': 40}
    }


def test_votes_export(swissvotes_app: TestApp) -> None:
    votes = SwissVoteCollection(swissvotes_app)
    vote = votes.add(
        bfs_number=Decimal('100.1'),
        date=date(1990, 6, 2),
        title_de="Vote DE",
        title_fr="Vote FR",
        short_title_de="V D",
        short_title_fr="V F",
        short_title_en="V E",
        keyword="Keyword",
        _legal_form=1,
        _parliamentary_initiated=1,
        initiator_de="Initiator D",
        initiator_fr="Initiator F",
        anneepolitique="anneepolitique",
        descriptor_1_level_1=Decimal('4'),
        descriptor_1_level_2=Decimal('4.2'),
        descriptor_1_level_3=Decimal('4.21'),
        descriptor_2_level_1=Decimal('10'),
        descriptor_2_level_2=Decimal('10.3'),
        descriptor_2_level_3=Decimal('10.35'),
        descriptor_3_level_1=Decimal('10'),
        descriptor_3_level_2=Decimal('10.3'),
        descriptor_3_level_3=Decimal('10.33'),
        _result=1,
        result_turnout=Decimal('20.01'),
        _result_people_accepted=1,
        result_people_yeas_p=Decimal('40.01'),
        _result_cantons_accepted=1,
        result_cantons_yeas=Decimal('1.5'),
        result_cantons_nays=Decimal('24.5'),
        brief_description_title='Kurzbeschreibung'
    )
    vote._result_ag_accepted = 0
    vote._result_ai_accepted = 0
    vote._result_ar_accepted = 0
    vote._result_be_accepted = 0
    vote._result_bl_accepted = 0
    vote._result_bs_accepted = 0
    vote._result_fr_accepted = 0
    vote._result_ge_accepted = 0
    vote._result_gl_accepted = 0
    vote._result_gr_accepted = 0
    vote._result_ju_accepted = 0
    vote._result_lu_accepted = 0
    vote._result_ne_accepted = 0
    vote._result_nw_accepted = 0
    vote._result_ow_accepted = 0
    vote._result_sg_accepted = 0
    vote._result_sh_accepted = 0
    vote._result_so_accepted = 0
    vote._result_sz_accepted = 0
    vote._result_tg_accepted = 0
    vote._result_ti_accepted = 0
    vote._result_ur_accepted = 0
    vote._result_vd_accepted = 0
    vote._result_vs_accepted = 0
    vote._result_zg_accepted = 0
    vote._result_zh_accepted = 0
    vote.procedure_number = '24.557'
    vote._position_federal_council = 1
    vote._position_parliament = 1
    vote._position_national_council = 1
    vote.position_national_council_yeas = 10
    vote.position_national_council_nays = 20
    vote._position_council_of_states = 1
    vote.position_council_of_states_yeas = 30
    vote.position_council_of_states_nays = 40
    vote.duration_federal_assembly = 30
    vote.duration_initative_collection = 32
    vote.duration_referendum_collection = 35
    vote.signatures_valid = 40
    vote.recommendations = {
        'fdp': 1,
        'cvp': 1,
        'sps': 1,
        'svp': 1,
        'lps': 2,
        'ldu': 2,
        'evp': 2,
        'csp': 3,
        'pda': 3,
        'poch': 3,
        'gps': 4,
        'sd': 4,
        'rep': 4,
        'edu': 5,
        'fps': 5,
        'lega': 5,
        'kvp': 66,
        'glp': 66,
        'bdp': None,
        'mcg': 9999,
        'mitte': 9999,
        'sav': 1,
        'eco': 2,
        'sgv': 3,
        'sbv-usp': 3,
        'sgb': 3,
        'travs': 3,
        'vsa': 9999,
        'vpod': 9999,
        'ssv': 9999,
        'gem': 9999,
        'kdk': 9999,
        'vdk': 9999,
        'endk': 9999,
        'fdk': 9999,
        'edk': 9999,
        'gdk': 9999,
        'ldk': 9999,
        'sodk': 9999,
        'kkjpd': 9999,
        'bpuk': 9999,
        'sbk': 9999,
        'acs': 9999,
        'tcs': 9999,
        'vcs': 9999,
        'voev': 9999,
    }
    vote.recommendations_other_yes_de = "Pro Velo D"
    vote.recommendations_other_yes_fr = "Pro Velo F"
    vote.recommendations_other_no_de = "Biosuisse D"
    vote.recommendations_other_no_fr = "Biosuisse F"
    vote.recommendations_other_free_de = "Pro Natura D, Greenpeace D"
    vote.recommendations_other_free_fr = "Pro Natura F, Greenpeace F"
    vote.recommendations_other_counter_proposal_de = "Pro Juventute D"
    vote.recommendations_other_counter_proposal_fr = "Pro Juventute F"
    vote.recommendations_other_popular_initiative_de = "Pro Senectute D"
    vote.recommendations_other_popular_initiative_fr = "Pro Senectute F"
    vote.recommendations_divergent = {
        'bdp_ag': 1,
        'bdp_ai': 1,
        'bdp_ar': 1,
        'bdp_be': 1,
        'bdp_bl': 1,
        'bdp_bs': 1,
        'bdp_fr': 1,
        'bdp_ge': 1,
        'bdp_gl': 1,
        'bdp_gr': 1,
        'bdp_ju': 1,
        'bdp_lu': 1,
        'bdp_ne': 1,
        'bdp_nw': 1,
        'bdp_ow': 1,
        'bdp_sg': 1,
        'bdp_sh': 1,
        'bdp_so': 1,
        'bdp_sz': 1,
        'bdp_tg': 1,
        'bdp_ti': 1,
        'bdp_ur': 1,
        'bdp_vd': 1,
        'bdp_vs': 1,
        'bdp_vsr': 1,
        'bdp_vso': 1,
        'bdp_zg': 1,
        'bdp_zh': 1,
        'jbdp_ch': 1,
        'csp_fr': 1,
        'csp_gr': 1,
        'csp_ju': 1,
        'csp_lu': 1,
        'csp_ow': 1,
        'csp_sg': 1,
        'csp_vs': 1,
        'csp_vsr': 1,
        'csp_vso': 1,
        'csp_zh': 1,
        'cvp-fr_ch': 1,
        'cvp_ag': 1,
        'cvp_ai': 1,
        'cvp_ar': 1,
        'cvp_be': 1,
        'cvp_bl': 1,
        'cvp_bs': 1,
        'cvp_fr': 1,
        'cvp_ge': 1,
        'cvp_gl': 1,
        'cvp_gr': 1,
        'cvp_ju': 1,
        'cvp_lu': 1,
        'cvp_ne': 1,
        'cvp_nw': 1,
        'cvp_ow': 1,
        'cvp_sg': 1,
        'cvp_sh': 1,
        'cvp_so': 1,
        'cvp_sz': 1,
        'cvp_tg': 1,
        'cvp_ti': 1,
        'cvp_ur': 1,
        'cvp_vd': 1,
        'cvp_vs': 1,
        'cvp_vsr': 1,
        'cvp_vso': 1,
        'cvp_zg': 1,
        'cvp_zh': 1,
        'jcvp_ch': 1,
        'jcvp_ag': 1,
        'jcvp_be': 1,
        'jcvp_gr': 1,
        'jcvp_lu': 1,
        'jcvp_so': 1,
        'jcvp_zh': 1,
        'edu_ag': 1,
        'edu_ai': 1,
        'edu_ar': 1,
        'edu_be': 1,
        'edu_bl': 1,
        'edu_bs': 1,
        'edu_fr': 1,
        'edu_ge': 1,
        'edu_gl': 1,
        'edu_gr': 1,
        'edu_ju': 1,
        'edu_lu': 1,
        'edu_ne': 1,
        'edu_nw': 1,
        'edu_ow': 1,
        'edu_sg': 1,
        'edu_sh': 1,
        'edu_so': 1,
        'edu_sz': 1,
        'edu_tg': 1,
        'edu_ti': 1,
        'edu_ur': 1,
        'edu_vd': 1,
        'edu_vs': 1,
        'edu_vsr': 1,
        'edu_vso': 1,
        'edu_zg': 1,
        'edu_zh': 1,
        'evp_ag': 1,
        'evp_ai': 1,
        'evp_ar': 1,
        'evp_be': 1,
        'evp_bl': 1,
        'evp_bs': 1,
        'evp_fr': 1,
        'evp_ge': 1,
        'evp_gl': 1,
        'evp_gr': 1,
        'evp_ju': 1,
        'evp_lu': 1,
        'evp_ne': 1,
        'evp_nw': 1,
        'evp_ow': 1,
        'evp_sg': 1,
        'evp_sh': 1,
        'evp_so': 1,
        'evp_sz': 1,
        'evp_tg': 1,
        'evp_ti': 1,
        'evp_ur': 1,
        'evp_vd': 1,
        'evp_vs': 1,
        'evp_zg': 1,
        'evp_zh': 1,
        'jevp_ch': 1,
        'fdp-fr_ch': 1,
        'fdp_ag': 1,
        'fdp_ai': 1,
        'fdp_ar': 1,
        'fdp_be': 1,
        'fdp_bl': 1,
        'fdp_bs': 1,
        'fdp_fr': 1,
        'fdp_ge': 1,
        'fdp_gl': 1,
        'fdp_gr': 1,
        'fdp_ju': 1,
        'fdp_lu': 1,
        'fdp_ne': 1,
        'fdp_nw': 1,
        'fdp_ow': 1,
        'fdp_sg': 1,
        'fdp_sh': 1,
        'fdp_so': 1,
        'fdp_sz': 1,
        'fdp_tg': 1,
        'fdp_ti': 1,
        'fdp_ur': 1,
        'fdp_vd': 1,
        'fdp_vs': 1,
        'fdp_vsr': 1,
        'fdp_vso': 1,
        'fdp_zg': 1,
        'fdp_zh': 1,
        'jfdp_ch': 1,
        'jfdp_ag': 1,
        'jfdp_bl': 1,
        'jfdp_fr': 1,
        'jfdp_gr': 1,
        'jfdp_ju': 1,
        'jfdp_lu': 1,
        'jfdp_sh': 1,
        'jfdp_ti': 1,
        'jfdp_vd': 1,
        'jfdp_zh': 1,
        'fps_ag': 1,
        'fps_ai': 1,
        'fps_be': 1,
        'fps_bl': 1,
        'fps_bs': 1,
        'fps_sg': 1,
        'fps_sh': 1,
        'fps_so': 1,
        'fps_tg': 1,
        'fps_zh': 1,
        'glp_ag': 1,
        'glp_ai': 1,
        'glp_ar': 1,
        'glp_be': 1,
        'glp_bl': 1,
        'glp_bs': 1,
        'glp_fr': 1,
        'glp_ge': 1,
        'glp_gl': 1,
        'glp_gr': 1,
        'glp_ju': 1,
        'glp_lu': 1,
        'glp_ne': 1,
        'glp_nw': 1,
        'glp_ow': 1,
        'glp_sg': 1,
        'glp_sh': 1,
        'glp_so': 1,
        'glp_sz': 1,
        'glp_tg': 1,
        'glp_ti': 1,
        'glp_ur': 1,
        'glp_vd': 1,
        'glp_vs': 1,
        'glp_vsr': 1,
        'glp_vso': 1,
        'glp_zg': 1,
        'glp_zh': 1,
        'jglp_ch': 1,
        'gps_ag': 66,
        'gps_ai': 66,
        'gps_ar': 66,
        'gps_be': 66,
        'gps_bl': 66,
        'gps_bs': 66,
        'gps_fr': 66,
        'gps_ge': 66,
        'gps_gl': 66,
        'gps_gr': 66,
        'gps_ju': 66,
        'gps_lu': 66,
        'gps_ne': 66,
        'gps_nw': 66,
        'gps_ow': 66,
        'gps_sg': 66,
        'gps_sh': 66,
        'gps_so': 66,
        'gps_sz': 66,
        'gps_tg': 66,
        'gps_ti': 66,
        'gps_ur': 66,
        'gps_vd': 66,
        'gps_vs': 66,
        'gps_vsr': 66,
        'gps_vso': 66,
        'gps_zg': 66,
        'gps_zh': 66,
        'jgps_ch': 66,
        'kvp_sg': 1,
        'lps_be': 1,
        'lps_bl': 1,
        'lps_bs': 1,
        'lps_fr': 1,
        'lps_ge': 1,
        'lps_ju': 1,
        'lps_ne': 1,
        'lps_sg': 1,
        'lps_ti': 1,
        'lps_vd': 1,
        'lps_vs': 1,
        'lps_zh': 1,
        'jlps_ch': 1,
        'jlps_so': 1,
        'jlps_ti': 1,
        'ldu_ag': 1,
        'ldu_ar': 1,
        'ldu_be': 1,
        'ldu_bl': 1,
        'ldu_bs': 1,
        'ldu_gr': 1,
        'ldu_lu': 1,
        'ldu_ne': 1,
        'ldu_sg': 1,
        'ldu_sh': 1,
        'ldu_so': 1,
        'ldu_tg': 1,
        'ldu_vd': 1,
        'ldu_zg': 1,
        'ldu_zh': 1,
        'jldu_ch': 1,
        'poch_so': 2,
        'poch_zh': 2,
        'pda_be': 1,
        'pda_bl': 1,
        'pda_bs': 1,
        'pda_ge': 1,
        'pda_ju': 1,
        'pda_ne': 1,
        'pda_sg': 1,
        'pda_ti': 1,
        'pda_vd': 1,
        'pda_zh': 1,
        'jpda_ch': 1,
        'rep_ag': 1,
        'rep_ge': 1,
        'rep_ne': 1,
        'rep_tg': 1,
        'rep_vd': 1,
        'rep_zh': 1,
        'sd_ag': 1,
        'sd_be': 1,
        'sd_bl': 1,
        'sd_bs': 1,
        'sd_fr': 1,
        'sd_ge': 1,
        'sd_gr': 1,
        'sd_lu': 1,
        'sd_ne': 1,
        'sd_sg': 1,
        'sd_so': 1,
        'sd_tg': 1,
        'sd_ti': 1,
        'sd_vd': 1,
        'sd_zh': 1,
        'jsd_ch': 1,
        'sps_ag': 1,
        'sps_ai': 1,
        'sps_ar': 1,
        'sps_be': 1,
        'sps_bl': 1,
        'sps_bs': 1,
        'sps_fr': 1,
        'sps_ge': 1,
        'sps_gl': 1,
        'sps_gr': 1,
        'sps_ju': 1,
        'sps_lu': 1,
        'sps_ne': 1,
        'sps_nw': 1,
        'sps_ow': 1,
        'sps_sg': 1,
        'sps_sh': 1,
        'sps_so': 1,
        'sps_sz': 1,
        'sps_tg': 1,
        'sps_ti': 1,
        'sps_ur': 1,
        'sps_vd': 1,
        'sps_vs': 1,
        'sps_vsr': 1,
        'sps_vso': 1,
        'sps_zg': 1,
        'sps_zh': 1,
        'juso_ch': 1,
        'juso_be': 1,
        'juso_ge': 1,
        'juso_ju': 1,
        'juso_ti': 1,
        'juso_vs': 1,
        'juso_zh': 1,
        'svp_ag': 3,
        'svp_ai': 3,
        'svp_ar': 3,
        'svp_be': 3,
        'svp_bl': 3,
        'svp_bs': 3,
        'svp_fr': 3,
        'svp_ge': 3,
        'svp_gl': 3,
        'svp_gr': 3,
        'svp_ju': 3,
        'svp_lu': 3,
        'svp_ne': 3,
        'svp_nw': 3,
        'svp_ow': 3,
        'svp_sg': 3,
        'svp_sh': 3,
        'svp_so': 3,
        'svp_sz': 3,
        'svp_tg': 3,
        'svp_ti': 3,
        'svp_ur': 3,
        'svp_vd': 3,
        'svp_vs': 3,
        'svp_vsr': 3,
        'svp_vso': 3,
        'svp_zg': 3,
        'svp_zh': 3,
        'jsvp_ch': 3,
        'jsvp_ag': 3,
        'jsvp_be': 3,
        'jsvp_ge': 3,
        'jsvp_sh': 3,
        'jsvp_ur': 3,
        'jsvp_zh': 3,
        'sgb_ag': 1,
        'sgb_ju': 1,
        'sgb_vs': 1,
        'sgv_ag': 1,
        'sgv_bs': 1,
        'sgv_sh': 1,
        'vpod_ge': 1,
        'vpod_vd': 1,
        'mitte-fr_ch': 2,
        'mitte_ag': 2,
        'mitte_ai': 2,
        'mitte_ar': 2,
        'mitte_be': 2,
        'mitte_bl': 2,
        'mitte_bs': 2,
        'mitte_fr': 2,
        'mitte_ge': 2,
        'mitte_gl': 2,
        'mitte_gr': 2,
        'mitte_ju': 2,
        'mitte_lu': 2,
        'mitte_ne': 2,
        'mitte_nw': 2,
        'mitte_ow': 2,
        'mitte_sg': 2,
        'mitte_sh': 2,
        'mitte_so': 2,
        'mitte_sz': 2,
        'mitte_tg': 2,
        'mitte_ti': 2,
        'mitte_ur': 2,
        'mitte_vd': 2,
        'mitte_vs': 2,
        'mitte_vsr': 2,
        'mitte_vso': 2,
        'mitte_zg': 2,
        'mitte_zh': 2,
        'jmitte_ch': 2,
        'jmitte_ag': 2,
        'jmitte_ai': 2,
        'jmitte_ar': 2,
        'jmitte_be': 2,
        'jmitte_bl': 2,
        'jmitte_bs': 2,
        'jmitte_fr': 2,
        'jmitte_ge': 2,
        'jmitte_gl': 2,
        'jmitte_gr': 2,
        'jmitte_ju': 2,
        'jmitte_lu': 2,
        'jmitte_ne': 2,
        'jmitte_nw': 2,
        'jmitte_ow': 2,
        'jmitte_sg': 2,
        'jmitte_sh': 2,
        'jmitte_so': 2,
        'jmitte_sz': 2,
        'jmitte_tg': 2,
        'jmitte_ti': 2,
        'jmitte_ur': 2,
        'jmitte_vd': 2,
        'jmitte_vs': 2,
        'jmitte_vsr': 2,
        'jmitte_vso': 2,
        'jmitte_zg': 2,
        'jmitte_zh': 2,
    }
    vote.national_council_election_year = 1990
    vote.national_council_share_fdp = Decimal('01.10')
    vote.national_council_share_cvp = Decimal('02.10')
    vote.national_council_share_sps = Decimal('03.10')
    vote.national_council_share_svp = Decimal('04.10')
    vote.national_council_share_lps = Decimal('05.10')
    vote.national_council_share_ldu = Decimal('06.10')
    vote.national_council_share_evp = Decimal('07.10')
    vote.national_council_share_csp = Decimal('08.10')
    vote.national_council_share_pda = Decimal('09.10')
    vote.national_council_share_poch = Decimal('10.10')
    vote.national_council_share_gps = Decimal('11.10')
    vote.national_council_share_sd = Decimal('12.10')
    vote.national_council_share_rep = Decimal('13.10')
    vote.national_council_share_edu = Decimal('14.10')
    vote.national_council_share_fps = Decimal('15.10')
    vote.national_council_share_lega = Decimal('16.10')
    vote.national_council_share_kvp = Decimal('17.10')
    vote.national_council_share_glp = Decimal('18.10')
    vote.national_council_share_bdp = Decimal('19.10')
    vote.national_council_share_mcg = Decimal('20.20')
    vote.national_council_share_mitte = Decimal('20.10')
    vote.national_council_share_ubrige = Decimal('21.20')
    vote.national_council_share_yeas = Decimal('22.20')
    vote.national_council_share_nays = Decimal('23.20')
    vote.national_council_share_neutral = Decimal('24.20')
    vote.national_council_share_none = Decimal('25.20')
    vote.national_council_share_empty = Decimal('26.20')
    vote.national_council_share_free_vote = Decimal('27.20')
    vote.national_council_share_unknown = Decimal('28.20')
    vote.bfs_map_de = 'map de'
    vote.bfs_map_fr = 'map fr'
    vote.bfs_map_en = 'map en'
    vote.bfs_dashboard_de = "https://dashboard.de"
    vote.bfs_dashboard_fr = "https://dashboard.fr"
    vote.bfs_dashboard_en = "https://dashboard.en"
    vote.link_curia_vista_de = 'https://curia.vista/de'
    vote.link_curia_vista_fr = 'https://curia.vista/fr'
    vote.link_easyvote_de = 'https://easy.vote/de'
    vote.link_easyvote_fr = 'https://easy.vote/fr'
    vote.link_bk_results_de = 'https://bk.results/de'
    vote.link_bk_results_fr = 'https://bk.results/fr'
    vote.link_bk_chrono_de = 'https://bk.chrono/de'
    vote.link_bk_chrono_fr = 'https://bk.chrono/fr'
    vote.link_federal_council_de = 'https://federal.council/de'
    vote.link_federal_council_fr = 'https://federal.council/fr'
    vote.link_federal_council_en = 'https://federal.council/en'
    vote.link_federal_departement_de = 'https://federal.departement/de'
    vote.link_federal_departement_fr = 'https://federal.departement/fr'
    vote.link_federal_departement_en = 'https://federal.departement/en'
    vote.link_federal_office_de = 'https://federal.office/de'
    vote.link_federal_office_fr = 'https://federal.office/fr'
    vote.link_federal_office_en = 'https://federal.office/en'
    vote.link_campaign_yes_1_de = 'https://yes1.de'
    vote.link_campaign_yes_2_de = 'https://yes2.de'
    vote.link_campaign_yes_3_de = 'https://yes3.de'
    vote.link_campaign_no_1_de = 'https://no1.de'
    vote.link_campaign_no_2_de = 'https://no2.de'
    vote.link_campaign_no_3_de = 'https://no3.de'
    vote.link_campaign_yes_1_fr = 'https://yes1.fr'
    vote.link_campaign_yes_2_fr = 'https://yes2.fr'
    vote.link_campaign_yes_3_fr = 'https://yes3.fr'
    vote.link_campaign_no_1_fr = 'https://no1.fr'
    vote.link_campaign_no_2_fr = 'https://no2.fr'
    vote.link_campaign_no_3_fr = 'https://no3.fr'
    vote.posters_mfg_yea = (
        'https://museum.ch/objects/1 '
        'https://museum.ch/objects/2'
    )
    vote.posters_mfg_nay = (
        'https://museum.ch/objects/3 '
        'https://museum.ch/objects/4'
    )
    vote.posters_bs_yea = (
        'https://plakatsammlungbasel.ch/objects/1 '
        'https://plakatsammlungbasel.ch/objects/2'
    )
    vote.posters_bs_nay = (
        'https://plakatsammlungbasel.ch/objects/3 '
        'https://plakatsammlungbasel.ch/objects/4'
    )
    vote.posters_sa_yea = (
        'https://sozialarchiv.ch/objects/1 '
        'https://sozialarchiv.ch/objects/2'
    )
    vote.posters_sa_nay = (
        'https://sozialarchiv.ch/objects/3 '
        'https://sozialarchiv.ch/objects/4'
    )
    vote.link_post_vote_poll_de = 'https://post.vote.poll/de'
    vote.link_post_vote_poll_fr = 'https://post.vote.poll/fr'
    vote.link_post_vote_poll_en = 'https://post.vote.poll/en'
    vote.media_ads_total = 1001
    vote.media_ads_yea_p = Decimal('10.06')
    vote.media_coverage_articles_total = 1007
    vote.media_coverage_tonality_total = Decimal('10.10')
    vote.campaign_finances_yea_total = 10000
    vote.campaign_finances_nay_total = 20000
    vote.campaign_finances_yea_donors_de = 'Donor 1 D, Donor 2 D'
    vote.campaign_finances_yea_donors_fr = 'Donor 1 F, Donor 2 F'
    vote.campaign_finances_nay_donors_de = 'Donor D'
    vote.campaign_finances_nay_donors_fr = 'Donor F'
    vote.campaign_finances_link_de = 'https://finances.de'
    vote.campaign_finances_link_fr = 'https://finances.fr'

    votes.session.flush()
    votes.session.expire_all()

    file: IO[Any] = StringIO()
    votes.export_csv(file)
    file.seek(0)
    rows = list(DictReader(file))
    assert len(rows) == 1
    csv = dict(rows[0])
    expected: dict[str, Any] = {
        'anr': '100,1',
        'datum': '02.06.1990',
        'titel_off_d': 'Vote DE',
        'titel_off_f': 'Vote FR',
        'titel_kurz_d': 'V D',
        'titel_kurz_f': 'V F',
        'titel_kurz_e': 'V E',
        'kurzbetitel': 'Kurzbeschreibung',
        'stichwort': 'Keyword',
        'rechtsform': '1',
        'pa-iv': '1',
        'd1e1': '4',
        'd1e2': '4,2',
        'd1e3': '4,21',
        'd2e1': '10',
        'd2e2': '10,3',
        'd2e3': '10,35',
        'd3e1': '10',
        'd3e2': '10,3',
        'd3e3': '10,33',
        'volk': '1',
        'stand': '1',
        'annahme': '1',
        'bet': '20,01',
        'volkja-proz': '40,01',
        'kt-ja': '1,5',
        'kt-nein': '24,5',
        'ag-annahme': '0',
        'ai-annahme': '0',
        'ar-annahme': '0',
        'be-annahme': '0',
        'bkchrono-de': 'https://bk.chrono/de',
        'bkchrono-fr': 'https://bk.chrono/fr',
        'bkresults-de': 'https://bk.results/de',
        'bkresults-fr': 'https://bk.results/fr',
        'bl-annahme': '0',
        'bs-annahme': '0',
        'curiavista-de': 'https://curia.vista/de',
        'curiavista-fr': 'https://curia.vista/fr',
        'easyvideo_de': 'https://easy.vote/de',
        'easyvideo_fr': 'https://easy.vote/fr',
        'info_br-de': 'https://federal.council/de',
        'info_br-fr': 'https://federal.council/fr',
        'info_br-en': 'https://federal.council/en',
        'info_dep-de': 'https://federal.departement/de',
        'info_dep-fr': 'https://federal.departement/fr',
        'info_dep-en': 'https://federal.departement/en',
        'info_amt-de': 'https://federal.office/de',
        'info_amt-fr': 'https://federal.office/fr',
        'info_amt-en': 'https://federal.office/en',
        'fr-annahme': '0',
        'ge-annahme': '0',
        'gl-annahme': '0',
        'gr-annahme': '0',
        'ju-annahme': '0',
        'lu-annahme': '0',
        'ne-annahme': '0',
        'nw-annahme': '0',
        'ow-annahme': '0',
        'sg-annahme': '0',
        'sh-annahme': '0',
        'so-annahme': '0',
        'sz-annahme': '0',
        'tg-annahme': '0',
        'ti-annahme': '0',
        'ur-annahme': '0',
        'vd-annahme': '0',
        'vs-annahme': '0',
        'zg-annahme': '0',
        'zh-annahme': '0',
        'gesch_nr': '24.557',
        'br-pos': '1',
        'bv-pos': '1',
        'nr-pos': '1',
        'nrja': '10',
        'nrnein': '20',
        'sr-pos': '1',
        'srja': '30',
        'srnein': '40',
        'dauer_bv': '30',
        'i-dauer_samm': '32',
        'fr-dauer_samm': '35',
        'unter_g': '40',
        'p-fdp': '1',
        'p-cvp': '1',
        'p-sps': '1',
        'p-svp': '1',
        'p-lps': '2',
        'p-ldu': '2',
        'p-evp': '2',
        'p-ucsp': '3',
        'p-pda': '3',
        'p-poch': '3',
        'p-gps': '4',
        'p-sd': '4',
        'p-rep': '4',
        'p-edu': '5',
        'p-fps': '5',
        'p-lega': '5',
        'p-kvp': '66',
        'p-glp': '66',
        'p-bdp': '.',
        'p-mcg': '9999',
        'p-mitte': '9999',
        'p-sav': '1',
        'p-eco': '2',
        'p-sgv': '3',
        'p-sbv': '3',
        'p-sgb': '3',
        'p-travs': '3',
        'p-vsa': '9999',
        'p-vpod': '9999',
        'p-ssv': '9999',
        'p-gem': '9999',
        'p-kdk': '9999',
        'p-vdk': '9999',
        'p-endk': '9999',
        'p-fdk': '9999',
        'p-edk': '9999',
        'p-gdk': '9999',
        'p-ldk': '9999',
        'p-sodk': '9999',
        'p-kkjpd': '9999',
        'p-bpuk': '9999',
        'p-sbk': '9999',
        'p-acs': '9999',
        'p-tcs': '9999',
        'p-vcs': '9999',
        'p-voev': '9999',
        'p-others_yes': 'Pro Velo D',
        'p-others_yes-fr': 'Pro Velo F',
        'p-others_no': 'Biosuisse D',
        'p-others_no-fr': 'Biosuisse F',
        'p-others_free': 'Pro Natura D, Greenpeace D',
        'p-others_free-fr': 'Pro Natura F, Greenpeace F',
        'p-others_counterp': 'Pro Juventute D',
        'p-others_counterp-fr': 'Pro Juventute F',
        'p-others_init': 'Pro Senectute D',
        'p-others_init-fr': 'Pro Senectute F',
        'pdev-bdp_AG': '1',
        'pdev-bdp_AI': '1',
        'pdev-bdp_AR': '1',
        'pdev-bdp_BE': '1',
        'pdev-bdp_BL': '1',
        'pdev-bdp_BS': '1',
        'pdev-bdp_FR': '1',
        'pdev-bdp_GE': '1',
        'pdev-bdp_GL': '1',
        'pdev-bdp_GR': '1',
        'pdev-bdp_JU': '1',
        'pdev-bdp_LU': '1',
        'pdev-bdp_NE': '1',
        'pdev-bdp_NW': '1',
        'pdev-bdp_OW': '1',
        'pdev-bdp_SG': '1',
        'pdev-bdp_SH': '1',
        'pdev-bdp_SO': '1',
        'pdev-bdp_SZ': '1',
        'pdev-bdp_TG': '1',
        'pdev-bdp_TI': '1',
        'pdev-bdp_UR': '1',
        'pdev-bdp_VD': '1',
        'pdev-bdp_VS': '1',
        'pdev-bdp_VSr': '1',
        'pdev-bdp_VSo': '1',
        'pdev-bdp_ZG': '1',
        'pdev-bdp_ZH': '1',
        'pdev-jbdp_CH': '1',
        'pdev-csp_FR': '1',
        'pdev-csp_GR': '1',
        'pdev-csp_JU': '1',
        'pdev-csp_LU': '1',
        'pdev-csp_OW': '1',
        'pdev-csp_SG': '1',
        'pdev-csp_VS': '1',
        'pdev-csp_VSr': '1',
        'pdev-csp_VSo': '1',
        'pdev-csp_ZH': '1',
        'pdev-cvp_frauen': '1',
        'pdev-cvp_AG': '1',
        'pdev-cvp_AI': '1',
        'pdev-cvp_AR': '1',
        'pdev-cvp_BE': '1',
        'pdev-cvp_BL': '1',
        'pdev-cvp_BS': '1',
        'pdev-cvp_FR': '1',
        'pdev-cvp_GE': '1',
        'pdev-cvp_GL': '1',
        'pdev-cvp_GR': '1',
        'pdev-cvp_JU': '1',
        'pdev-cvp_LU': '1',
        'pdev-cvp_NE': '1',
        'pdev-cvp_NW': '1',
        'pdev-cvp_OW': '1',
        'pdev-cvp_SG': '1',
        'pdev-cvp_SH': '1',
        'pdev-cvp_SO': '1',
        'pdev-cvp_SZ': '1',
        'pdev-cvp_TG': '1',
        'pdev-cvp_TI': '1',
        'pdev-cvp_UR': '1',
        'pdev-cvp_VD': '1',
        'pdev-cvp_VS': '1',
        'pdev-cvp_VSr': '1',
        'pdev-cvp_VSo': '1',
        'pdev-cvp_ZG': '1',
        'pdev-cvp_ZH': '1',
        'pdev-jcvp_CH': '1',
        'pdev-jcvp_AG': '1',
        'pdev-jcvp_BE': '1',
        'pdev-jcvp_GR': '1',
        'pdev-jcvp_LU': '1',
        'pdev-jcvp_SO': '1',
        'pdev-jcvp_ZH': '1',
        'pdev-edu_AG': '1',
        'pdev-edu_AI': '1',
        'pdev-edu_AR': '1',
        'pdev-edu_BE': '1',
        'pdev-edu_BL': '1',
        'pdev-edu_BS': '1',
        'pdev-edu_FR': '1',
        'pdev-edu_GE': '1',
        'pdev-edu_GL': '1',
        'pdev-edu_GR': '1',
        'pdev-edu_JU': '1',
        'pdev-edu_LU': '1',
        'pdev-edu_NE': '1',
        'pdev-edu_NW': '1',
        'pdev-edu_OW': '1',
        'pdev-edu_SG': '1',
        'pdev-edu_SH': '1',
        'pdev-edu_SO': '1',
        'pdev-edu_SZ': '1',
        'pdev-edu_TG': '1',
        'pdev-edu_TI': '1',
        'pdev-edu_UR': '1',
        'pdev-edu_VD': '1',
        'pdev-edu_VS': '1',
        'pdev-edu_VSr': '1',
        'pdev-edu_VSo': '1',
        'pdev-edu_ZG': '1',
        'pdev-edu_ZH': '1',
        'pdev-evp_AG': '1',
        'pdev-evp_AI': '1',
        'pdev-evp_AR': '1',
        'pdev-evp_BE': '1',
        'pdev-evp_BL': '1',
        'pdev-evp_BS': '1',
        'pdev-evp_FR': '1',
        'pdev-evp_GE': '1',
        'pdev-evp_GL': '1',
        'pdev-evp_GR': '1',
        'pdev-evp_JU': '1',
        'pdev-evp_LU': '1',
        'pdev-evp_NE': '1',
        'pdev-evp_NW': '1',
        'pdev-evp_OW': '1',
        'pdev-evp_SG': '1',
        'pdev-evp_SH': '1',
        'pdev-evp_SO': '1',
        'pdev-evp_SZ': '1',
        'pdev-evp_TG': '1',
        'pdev-evp_TI': '1',
        'pdev-evp_UR': '1',
        'pdev-evp_VD': '1',
        'pdev-evp_VS': '1',
        'pdev-evp_ZG': '1',
        'pdev-evp_ZH': '1',
        'pdev-jevp_CH': '1',
        'pdev-fdp_Frauen': '1',
        'pdev-fdp_AG': '1',
        'pdev-fdp_AI': '1',
        'pdev-fdp_AR': '1',
        'pdev-fdp_BE': '1',
        'pdev-fdp_BL': '1',
        'pdev-fdp_BS': '1',
        'pdev-fdp_FR': '1',
        'pdev-fdp_GE': '1',
        'pdev-fdp_GL': '1',
        'pdev-fdp_GR': '1',
        'pdev-fdp_JU': '1',
        'pdev-fdp_LU': '1',
        'pdev-fdp_NE': '1',
        'pdev-fdp_NW': '1',
        'pdev-fdp_OW': '1',
        'pdev-fdp_SG': '1',
        'pdev-fdp_SH': '1',
        'pdev-fdp_SO': '1',
        'pdev-fdp_SZ': '1',
        'pdev-fdp_TG': '1',
        'pdev-fdp_TI': '1',
        'pdev-fdp_UR': '1',
        'pdev-fdp_VD': '1',
        'pdev-fdp_VS': '1',
        'pdev-fdp_VSr': '1',
        'pdev-fdp_Vso': '1',
        'pdev-fdp_ZG': '1',
        'pdev-fdp_ZH': '1',
        'pdev-jfdp_CH': '1',
        'pdev-jfdp_AG': '1',
        'pdev-jfdp_BL': '1',
        'pdev-jfdp_FR': '1',
        'pdev-jfdp_GR': '1',
        'pdev-jfdp_JU': '1',
        'pdev-jfdp_LU': '1',
        'pdev-jfdp_SH': '1',
        'pdev-jfdp_TI': '1',
        'pdev-jfdp_VD': '1',
        'pdev-jfdp_ZH': '1',
        'pdev-fps_AG': '1',
        'pdev-fps_AI': '1',
        'pdev-fps_BE': '1',
        'pdev-fps_BL': '1',
        'pdev-fps_BS': '1',
        'pdev-fps_SG': '1',
        'pdev-fps_SH': '1',
        'pdev-fps_SO': '1',
        'pdev-fps_TG': '1',
        'pdev-fps_ZH': '1',
        'pdev-glp_AG': '1',
        'pdev-glp_AI': '1',
        'pdev-glp_AR': '1',
        'pdev-glp_BE': '1',
        'pdev-glp_BL': '1',
        'pdev-glp_BS': '1',
        'pdev-glp_FR': '1',
        'pdev-glp_GE': '1',
        'pdev-glp_GL': '1',
        'pdev-glp_GR': '1',
        'pdev-glp_JU': '1',
        'pdev-glp_LU': '1',
        'pdev-glp_NE': '1',
        'pdev-glp_NW': '1',
        'pdev-glp_OW': '1',
        'pdev-glp_SG': '1',
        'pdev-glp_SH': '1',
        'pdev-glp_SO': '1',
        'pdev-glp_SZ': '1',
        'pdev-glp_TG': '1',
        'pdev-glp_TI': '1',
        'pdev-glp_UR': '1',
        'pdev-glp_VD': '1',
        'pdev-glp_VS': '1',
        'pdev-glp_VSr': '1',
        'pdev-glp_VSo': '1',
        'pdev-glp_ZG': '1',
        'pdev-glp_ZH': '1',
        'pdev-jglp_CH': '1',
        'pdev-gps_AG': '66',
        'pdev-gps_AI': '66',
        'pdev-gps_AR': '66',
        'pdev-gps_BE': '66',
        'pdev-gps_BL': '66',
        'pdev-gps_BS': '66',
        'pdev-gps_FR': '66',
        'pdev-gps_GE': '66',
        'pdev-gps_GL': '66',
        'pdev-gps_GR': '66',
        'pdev-gps_JU': '66',
        'pdev-gps_LU': '66',
        'pdev-gps_NE': '66',
        'pdev-gps_NW': '66',
        'pdev-gps_OW': '66',
        'pdev-gps_SG': '66',
        'pdev-gps_SH': '66',
        'pdev-gps_SO': '66',
        'pdev-gps_SZ': '66',
        'pdev-gps_TG': '66',
        'pdev-gps_TI': '66',
        'pdev-gps_UR': '66',
        'pdev-gps_VD': '66',
        'pdev-gps_VS': '66',
        'pdev-gps_VSr': '66',
        'pdev-gps_VSo': '66',
        'pdev-gps_ZG': '66',
        'pdev-gps_ZH': '66',
        'pdev-jgps_CH': '66',
        'pdev-kvp_SG': '1',
        'pdev-lps_BE': '1',
        'pdev-lps_BL': '1',
        'pdev-lps_BS': '1',
        'pdev-lps_FR': '1',
        'pdev-lps_GE': '1',
        'pdev-lps_JU': '1',
        'pdev-lps_NE': '1',
        'pdev-lps_SG': '1',
        'pdev-lps_TI': '1',
        'pdev-lps_VD': '1',
        'pdev-lps_VS': '1',
        'pdev-lps_ZH': '1',
        'pdev-jlps_CH': '1',
        'pdev-jlps_SO': '1',
        'pdev-jlps_TI': '1',
        'pdev-ldu_AG': '1',
        'pdev-ldu_AR': '1',
        'pdev-ldu_BE': '1',
        'pdev-ldu_BL': '1',
        'pdev-ldu_BS': '1',
        'pdev-ldu_GR': '1',
        'pdev-ldu_LU': '1',
        'pdev-ldu_NE': '1',
        'pdev-ldu_SG': '1',
        'pdev-ldu_SH': '1',
        'pdev-ldu_SO': '1',
        'pdev-ldu_TG': '1',
        'pdev-ldu_VD': '1',
        'pdev-ldu_ZG': '1',
        'pdev-ldu_ZH': '1',
        'pdev-jldu_CH': '1',
        'pdev-poch_SO': '2',
        'pdev-poch_ZH': '2',
        'pdev-pda_BE': '1',
        'pdev-pda_BL': '1',
        'pdev-pda_BS': '1',
        'pdev-pda_GE': '1',
        'pdev-pda_JU': '1',
        'pdev-pda_NE': '1',
        'pdev-pda_SG': '1',
        'pdev-pda_TI': '1',
        'pdev-pda_VD': '1',
        'pdev-pda_ZH': '1',
        'pdev-jpda_CH': '1',
        'pdev-rep_AG': '1',
        'pdev-rep_GE': '1',
        'pdev-rep_NE': '1',
        'pdev-rep_TG': '1',
        'pdev-rep_VD': '1',
        'pdev-rep_ZH': '1',
        'pdev-sd_AG': '1',
        'pdev-sd_BE': '1',
        'pdev-sd_BL': '1',
        'pdev-sd_BS': '1',
        'pdev-sd_FR': '1',
        'pdev-sd_GE': '1',
        'pdev-sd_GR': '1',
        'pdev-sd_LU': '1',
        'pdev-sd_NE': '1',
        'pdev-sd_SG': '1',
        'pdev-sd_SO': '1',
        'pdev-sd_TG': '1',
        'pdev-sd_TI': '1',
        'pdev-sd_VD': '1',
        'pdev-sd_ZH': '1',
        'pdev-jsd_CH': '1',
        'pdev-sps_AG': '1',
        'pdev-sps_AI': '1',
        'pdev-sps_AR': '1',
        'pdev-sps_BE': '1',
        'pdev-sps_BL': '1',
        'pdev-sps_BS': '1',
        'pdev-sps_FR': '1',
        'pdev-sps_GE': '1',
        'pdev-sps_GL': '1',
        'pdev-sps_GR': '1',
        'pdev-sps_JU': '1',
        'pdev-sps_LU': '1',
        'pdev-sps_NE': '1',
        'pdev-sps_NW': '1',
        'pdev-sps_OW': '1',
        'pdev-sps_SG': '1',
        'pdev-sps_SH': '1',
        'pdev-sps_SO': '1',
        'pdev-sps_SZ': '1',
        'pdev-sps_TG': '1',
        'pdev-sps_TI': '1',
        'pdev-sps_UR': '1',
        'pdev-sps_VD': '1',
        'pdev-sps_VS': '1',
        'pdev-sps_VSr': '1',
        'pdev-sps_VSo': '1',
        'pdev-sps_ZG': '1',
        'pdev-sps_ZH': '1',
        'pdev-juso_CH': '1',
        'pdev-juso_BE': '1',
        'pdev-juso_GE': '1',
        'pdev-juso_JU': '1',
        'pdev-juso_TI': '1',
        'pdev-juso_VS': '1',
        'pdev-juso_ZH': '1',
        'pdev-svp_AG': '3',
        'pdev-svp_AI': '3',
        'pdev-svp_AR': '3',
        'pdev-svp_BE': '3',
        'pdev-svp_BL': '3',
        'pdev-svp_BS': '3',
        'pdev-svp_FR': '3',
        'pdev-svp_GE': '3',
        'pdev-svp_GL': '3',
        'pdev-svp_GR': '3',
        'pdev-svp_JU': '3',
        'pdev-svp_LU': '3',
        'pdev-svp_NE': '3',
        'pdev-svp_NW': '3',
        'pdev-svp_OW': '3',
        'pdev-svp_SG': '3',
        'pdev-svp_SH': '3',
        'pdev-svp_SO': '3',
        'pdev-svp_SZ': '3',
        'pdev-svp_TG': '3',
        'pdev-svp_TI': '3',
        'pdev-svp_UR': '3',
        'pdev-svp_VD': '3',
        'pdev-svp_VS': '3',
        'pdev-svp_VSr': '3',
        'pdev-svp_VSo': '3',
        'pdev-svp_ZG': '3',
        'pdev-svp_ZH': '3',
        'pdev-jsvp_CH': '3',
        'pdev-jsvp_AG': '3',
        'pdev-jsvp_BE': '3',
        'pdev-jsvp_GE': '3',
        'pdev-jsvp_SH': '3',
        'pdev-jsvp_UR': '3',
        'pdev-jsvp_ZH': '3',
        'pdev-sgb_AG': '1',
        'pdev-sgb_JU': '1',
        'pdev-sgb_VS': '1',
        'pdev-sgv_AG': '1',
        'pdev-sgv_BS': '1',
        'pdev-sgv_SH': '1',
        'pdev-vpod_GE': '1',
        'pdev-vpod_VD': '1',
        'pdev-mitte_frauen': '2',
        'pdev-mitte_AG': '2',
        'pdev-mitte_AI': '2',
        'pdev-mitte_AR': '2',
        'pdev-mitte_BE': '2',
        'pdev-mitte_BL': '2',
        'pdev-mitte_BS': '2',
        'pdev-mitte_FR': '2',
        'pdev-mitte_GE': '2',
        'pdev-mitte_GL': '2',
        'pdev-mitte_GR': '2',
        'pdev-mitte_JU': '2',
        'pdev-mitte_LU': '2',
        'pdev-mitte_NE': '2',
        'pdev-mitte_NW': '2',
        'pdev-mitte_OW': '2',
        'pdev-mitte_SG': '2',
        'pdev-mitte_SH': '2',
        'pdev-mitte_SO': '2',
        'pdev-mitte_SZ': '2',
        'pdev-mitte_TG': '2',
        'pdev-mitte_TI': '2',
        'pdev-mitte_UR': '2',
        'pdev-mitte_VD': '2',
        'pdev-mitte_VS': '2',
        'pdev-mitte_VSr': '2',
        'pdev-mitte_VSo': '2',
        'pdev-mitte_ZG': '2',
        'pdev-mitte_ZH': '2',
        'pdev-jmitte_CH': '2',
        'pdev-jmitte_AG': '2',
        'pdev-jmitte_AI': '2',
        'pdev-jmitte_AR': '2',
        'pdev-jmitte_BE': '2',
        'pdev-jmitte_BL': '2',
        'pdev-jmitte_BS': '2',
        'pdev-jmitte_FR': '2',
        'pdev-jmitte_GE': '2',
        'pdev-jmitte_GL': '2',
        'pdev-jmitte_GR': '2',
        'pdev-jmitte_JU': '2',
        'pdev-jmitte_LU': '2',
        'pdev-jmitte_NE': '2',
        'pdev-jmitte_NW': '2',
        'pdev-jmitte_OW': '2',
        'pdev-jmitte_SG': '2',
        'pdev-jmitte_SH': '2',
        'pdev-jmitte_SO': '2',
        'pdev-jmitte_SZ': '2',
        'pdev-jmitte_TG': '2',
        'pdev-jmitte_TI': '2',
        'pdev-jmitte_UR': '2',
        'pdev-jmitte_VD': '2',
        'pdev-jmitte_VS': '2',
        'pdev-jmitte_VSr': '2',
        'pdev-jmitte_VSo': '2',
        'pdev-jmitte_ZG': '2',
        'pdev-jmitte_ZH': '2',
        'nr-wahl': '1990',
        'w-fdp': '1,1',
        'w-cvp': '2,1',
        'w-sp': '3,1',
        'w-svp': '4,1',
        'w-lps': '5,1',
        'w-ldu': '6,1',
        'w-evp': '7,1',
        'w-csp': '8,1',
        'w-pda': '9,1',
        'w-poch': '10,1',
        'w-gps': '11,1',
        'w-sd': '12,1',
        'w-rep': '13,1',
        'w-edu': '14,1',
        'w-fps': '15,1',
        'w-lega': '16,1',
        'w-kvp': '17,1',
        'w-glp': '18,1',
        'w-bdp': '19,1',
        'w-mcg': '20,2',
        'w-mitte': '20,1',
        'w-ubrige': '21,2',
        'ja-lager': '22,2',
        'nein-lager': '23,2',
        'keinepar-summe': '25,2',
        'leer-summe': '26,2',
        'freigabe-summe': '27,2',
        'neutral-summe': '24,2',
        'unbekannt-summe': '28,2',
        'urheber': 'Initiator D',
        'urheber-fr': 'Initiator F',
        'anneepolitique': 'anneepolitique',
        'bfsmap-de': 'map de',
        'bfsmap-fr': 'map fr',
        'bfsmap-en': 'map en',
        'bfsdash-de': 'https://dashboard.de',
        'bfsdash-fr': 'https://dashboard.fr',
        'bfsdash-en': 'https://dashboard.en',
        'poster_ja_mfg': (
            'https://museum.ch/objects/1 '
            'https://museum.ch/objects/2'
        ),
        'poster_nein_mfg': (
            'https://museum.ch/objects/3 '
            'https://museum.ch/objects/4'
        ),
        'poster_ja_bs': (
            'https://plakatsammlungbasel.ch/objects/1 '
            'https://plakatsammlungbasel.ch/objects/2'
        ),
        'poster_nein_bs': (
            'https://plakatsammlungbasel.ch/objects/3 '
            'https://plakatsammlungbasel.ch/objects/4'
        ),
        'poster_ja_sa': (
            'https://sozialarchiv.ch/objects/1 '
            'https://sozialarchiv.ch/objects/2'
        ),
        'poster_nein_sa': (
            'https://sozialarchiv.ch/objects/3 '
            'https://sozialarchiv.ch/objects/4'
        ),
        'nach_cockpit_d': 'https://post.vote.poll/de',
        'nach_cockpit_f': 'https://post.vote.poll/fr',
        'nach_cockpit_e': 'https://post.vote.poll/en',
        'inserate-total': '1001',
        'inserate-jaanteil': '10,06',
        'mediares-tot': '1007',
        'mediaton-tot': '10,1',
        'web-yes-1-de': 'https://yes1.de',
        'web-yes-2-de': 'https://yes2.de',
        'web-yes-3-de': 'https://yes3.de',
        'web-no-1-de': 'https://no1.de',
        'web-no-2-de': 'https://no2.de',
        'web-no-3-de': 'https://no3.de',
        'web-yes-1-fr': 'https://yes1.fr',
        'web-yes-2-fr': 'https://yes2.fr',
        'web-yes-3-fr': 'https://yes3.fr',
        'web-no-1-fr': 'https://no1.fr',
        'web-no-2-fr': 'https://no2.fr',
        'web-no-3-fr': 'https://no3.fr',
        'finanz-ja-tot': '10000',
        'finanz-nein-tot': '20000',
        'finanz-ja-gr-de': 'Donor 1 D, Donor 2 D',
        'finanz-ja-gr-fr': 'Donor 1 F, Donor 2 F',
        'finanz-nein-gr-de': 'Donor D',
        'finanz-nein-gr-fr': 'Donor F',
        'finanz-link-de': 'https://finances.de',
        'finanz-link-fr': 'https://finances.fr',
    }
    assert csv == expected

    file = BytesIO()
    votes.export_xlsx(file)
    file.seek(0)
    workbook = load_workbook(file)
    sheet = workbook['DATA']
    xlsx = dict(
        zip(
            [cell.value for cell in tuple(sheet.rows)[0]],
            [cell.value for cell in tuple(sheet.rows)[1]]
        )
    )
    expected = {
        'anr': 100.1,
        'datum': datetime(1990, 6, 2),
        'titel_off_d': 'Vote DE',
        'titel_off_f': 'Vote FR',
        'titel_kurz_d': 'V D',
        'titel_kurz_f': 'V F',
        'titel_kurz_e': 'V E',
        'kurzbetitel': 'Kurzbeschreibung',
        'stichwort': 'Keyword',
        'rechtsform': 1.0,
        'pa-iv': 1.0,
        'd1e1': 4.0,
        'd1e2': 4.2,
        'd1e3': 4.21,
        'd2e1': 10.0,
        'd2e2': 10.3,
        'd2e3': 10.35,
        'd3e1': 10.0,
        'd3e2': 10.3,
        'd3e3': 10.33,
        'volk': 1.0,
        'stand': 1.0,
        'annahme': 1.0,
        'bet': 20.01,
        'volkja-proz': 40.01,
        'kt-ja': 1.5,
        'kt-nein': 24.5,
        'ag-annahme': 0.0,
        'ai-annahme': 0.0,
        'ar-annahme': 0.0,
        'be-annahme': 0.0,
        'bkchrono-de': 'https://bk.chrono/de',
        'bkchrono-fr': 'https://bk.chrono/fr',
        'bkresults-de': 'https://bk.results/de',
        'bkresults-fr': 'https://bk.results/fr',
        'bl-annahme': 0.0,
        'bs-annahme': 0.0,
        'curiavista-de': 'https://curia.vista/de',
        'curiavista-fr': 'https://curia.vista/fr',
        'easyvideo_de': 'https://easy.vote/de',
        'easyvideo_fr': 'https://easy.vote/fr',
        'info_br-de': 'https://federal.council/de',
        'info_br-fr': 'https://federal.council/fr',
        'info_br-en': 'https://federal.council/en',
        'info_dep-de': 'https://federal.departement/de',
        'info_dep-fr': 'https://federal.departement/fr',
        'info_dep-en': 'https://federal.departement/en',
        'info_amt-de': 'https://federal.office/de',
        'info_amt-fr': 'https://federal.office/fr',
        'info_amt-en': 'https://federal.office/en',
        'fr-annahme': 0.0,
        'ge-annahme': 0.0,
        'gl-annahme': 0.0,
        'gr-annahme': 0.0,
        'ju-annahme': 0.0,
        'lu-annahme': 0.0,
        'ne-annahme': 0.0,
        'nw-annahme': 0.0,
        'ow-annahme': 0.0,
        'sg-annahme': 0.0,
        'sh-annahme': 0.0,
        'so-annahme': 0.0,
        'sz-annahme': 0.0,
        'tg-annahme': 0.0,
        'ti-annahme': 0.0,
        'ur-annahme': 0.0,
        'vd-annahme': 0.0,
        'vs-annahme': 0.0,
        'zg-annahme': 0.0,
        'zh-annahme': 0.0,
        'gesch_nr': '24.557',
        'br-pos': 1.0,
        'bv-pos': 1.0,
        'nr-pos': 1.0,
        'nrja': 10.0,
        'nrnein': 20.0,
        'sr-pos': 1.0,
        'srja': 30.0,
        'srnein': 40.0,
        'dauer_bv': 30.0,
        'i-dauer_samm': 32.0,
        'fr-dauer_samm': 35.0,
        'unter_g': 40.0,
        'p-fdp': 1.0,
        'p-cvp': 1.0,
        'p-sps': 1.0,
        'p-svp': 1.0,
        'p-lps': 2.0,
        'p-ldu': 2.0,
        'p-evp': 2.0,
        'p-ucsp': 3.0,
        'p-pda': 3.0,
        'p-poch': 3.0,
        'p-gps': 4.0,
        'p-sd': 4.0,
        'p-rep': 4.0,
        'p-edu': 5.0,
        'p-fps': 5.0,
        'p-lega': 5.0,
        'p-kvp': 66.0,
        'p-glp': 66.0,
        'p-bdp': None,
        'p-mcg': 9999.0,
        'p-mitte': 9999.0,
        'p-sav': 1.0,
        'p-eco': 2.0,
        'p-sgv': 3.0,
        'p-sbv': 3.0,
        'p-sgb': 3.0,
        'p-travs': 3.0,
        'p-vsa': 9999.0,
        'p-vpod': 9999.0,
        'p-ssv': 9999.0,
        'p-gem': 9999.0,
        'p-kdk': 9999.0,
        'p-vdk': 9999.0,
        'p-endk': 9999.0,
        'p-fdk': 9999.0,
        'p-edk': 9999.0,
        'p-gdk': 9999.0,
        'p-ldk': 9999.0,
        'p-sodk': 9999.0,
        'p-kkjpd': 9999.0,
        'p-bpuk': 9999.0,
        'p-sbk': 9999.0,
        'p-acs': 9999.0,
        'p-tcs': 9999.0,
        'p-vcs': 9999.0,
        'p-voev': 9999.0,
        'p-others_yes': 'Pro Velo D',
        'p-others_yes-fr': 'Pro Velo F',
        'p-others_no': 'Biosuisse D',
        'p-others_no-fr': 'Biosuisse F',
        'p-others_free': 'Pro Natura D, Greenpeace D',
        'p-others_free-fr': 'Pro Natura F, Greenpeace F',
        'p-others_counterp': 'Pro Juventute D',
        'p-others_counterp-fr': 'Pro Juventute F',
        'p-others_init': 'Pro Senectute D',
        'p-others_init-fr': 'Pro Senectute F',
        'pdev-bdp_AG': 1.0,
        'pdev-bdp_AI': 1.0,
        'pdev-bdp_AR': 1.0,
        'pdev-bdp_BE': 1.0,
        'pdev-bdp_BL': 1.0,
        'pdev-bdp_BS': 1.0,
        'pdev-bdp_FR': 1.0,
        'pdev-bdp_GE': 1.0,
        'pdev-bdp_GL': 1.0,
        'pdev-bdp_GR': 1.0,
        'pdev-bdp_JU': 1.0,
        'pdev-bdp_LU': 1.0,
        'pdev-bdp_NE': 1.0,
        'pdev-bdp_NW': 1.0,
        'pdev-bdp_OW': 1.0,
        'pdev-bdp_SG': 1.0,
        'pdev-bdp_SH': 1.0,
        'pdev-bdp_SO': 1.0,
        'pdev-bdp_SZ': 1.0,
        'pdev-bdp_TG': 1.0,
        'pdev-bdp_TI': 1.0,
        'pdev-bdp_UR': 1.0,
        'pdev-bdp_VD': 1.0,
        'pdev-bdp_VS': 1.0,
        'pdev-bdp_VSr': 1.0,
        'pdev-bdp_VSo': 1.0,
        'pdev-bdp_ZG': 1.0,
        'pdev-bdp_ZH': 1.0,
        'pdev-jbdp_CH': 1.0,
        'pdev-csp_FR': 1.0,
        'pdev-csp_GR': 1.0,
        'pdev-csp_JU': 1.0,
        'pdev-csp_LU': 1.0,
        'pdev-csp_OW': 1.0,
        'pdev-csp_SG': 1.0,
        'pdev-csp_VS': 1.0,
        'pdev-csp_VSr': 1.0,
        'pdev-csp_VSo': 1.0,
        'pdev-csp_ZH': 1.0,
        'pdev-cvp_frauen': 1.0,
        'pdev-cvp_AG': 1.0,
        'pdev-cvp_AI': 1.0,
        'pdev-cvp_AR': 1.0,
        'pdev-cvp_BE': 1.0,
        'pdev-cvp_BL': 1.0,
        'pdev-cvp_BS': 1.0,
        'pdev-cvp_FR': 1.0,
        'pdev-cvp_GE': 1.0,
        'pdev-cvp_GL': 1.0,
        'pdev-cvp_GR': 1.0,
        'pdev-cvp_JU': 1.0,
        'pdev-cvp_LU': 1.0,
        'pdev-cvp_NE': 1.0,
        'pdev-cvp_NW': 1.0,
        'pdev-cvp_OW': 1.0,
        'pdev-cvp_SG': 1.0,
        'pdev-cvp_SH': 1.0,
        'pdev-cvp_SO': 1.0,
        'pdev-cvp_SZ': 1.0,
        'pdev-cvp_TG': 1.0,
        'pdev-cvp_TI': 1.0,
        'pdev-cvp_UR': 1.0,
        'pdev-cvp_VD': 1.0,
        'pdev-cvp_VS': 1.0,
        'pdev-cvp_VSr': 1.0,
        'pdev-cvp_VSo': 1.0,
        'pdev-cvp_ZG': 1.0,
        'pdev-cvp_ZH': 1.0,
        'pdev-jcvp_CH': 1.0,
        'pdev-jcvp_AG': 1.0,
        'pdev-jcvp_BE': 1.0,
        'pdev-jcvp_GR': 1.0,
        'pdev-jcvp_LU': 1.0,
        'pdev-jcvp_SO': 1.0,
        'pdev-jcvp_ZH': 1.0,
        'pdev-edu_AG': 1.0,
        'pdev-edu_AI': 1.0,
        'pdev-edu_AR': 1.0,
        'pdev-edu_BE': 1.0,
        'pdev-edu_BL': 1.0,
        'pdev-edu_BS': 1.0,
        'pdev-edu_FR': 1.0,
        'pdev-edu_GE': 1.0,
        'pdev-edu_GL': 1.0,
        'pdev-edu_GR': 1.0,
        'pdev-edu_JU': 1.0,
        'pdev-edu_LU': 1.0,
        'pdev-edu_NE': 1.0,
        'pdev-edu_NW': 1.0,
        'pdev-edu_OW': 1.0,
        'pdev-edu_SG': 1.0,
        'pdev-edu_SH': 1.0,
        'pdev-edu_SO': 1.0,
        'pdev-edu_SZ': 1.0,
        'pdev-edu_TG': 1.0,
        'pdev-edu_TI': 1.0,
        'pdev-edu_UR': 1.0,
        'pdev-edu_VD': 1.0,
        'pdev-edu_VS': 1.0,
        'pdev-edu_VSr': 1.0,
        'pdev-edu_VSo': 1.0,
        'pdev-edu_ZG': 1.0,
        'pdev-edu_ZH': 1.0,
        'pdev-evp_AG': 1.0,
        'pdev-evp_AI': 1.0,
        'pdev-evp_AR': 1.0,
        'pdev-evp_BE': 1.0,
        'pdev-evp_BL': 1.0,
        'pdev-evp_BS': 1.0,
        'pdev-evp_FR': 1.0,
        'pdev-evp_GE': 1.0,
        'pdev-evp_GL': 1.0,
        'pdev-evp_GR': 1.0,
        'pdev-evp_JU': 1.0,
        'pdev-evp_LU': 1.0,
        'pdev-evp_NE': 1.0,
        'pdev-evp_NW': 1.0,
        'pdev-evp_OW': 1.0,
        'pdev-evp_SG': 1.0,
        'pdev-evp_SH': 1.0,
        'pdev-evp_SO': 1.0,
        'pdev-evp_SZ': 1.0,
        'pdev-evp_TG': 1.0,
        'pdev-evp_TI': 1.0,
        'pdev-evp_UR': 1.0,
        'pdev-evp_VD': 1.0,
        'pdev-evp_VS': 1.0,
        'pdev-evp_ZG': 1.0,
        'pdev-evp_ZH': 1.0,
        'pdev-jevp_CH': 1.0,
        'pdev-fdp_Frauen': 1.0,
        'pdev-fdp_AG': 1.0,
        'pdev-fdp_AI': 1.0,
        'pdev-fdp_AR': 1.0,
        'pdev-fdp_BE': 1.0,
        'pdev-fdp_BL': 1.0,
        'pdev-fdp_BS': 1.0,
        'pdev-fdp_FR': 1.0,
        'pdev-fdp_GE': 1.0,
        'pdev-fdp_GL': 1.0,
        'pdev-fdp_GR': 1.0,
        'pdev-fdp_JU': 1.0,
        'pdev-fdp_LU': 1.0,
        'pdev-fdp_NE': 1.0,
        'pdev-fdp_NW': 1.0,
        'pdev-fdp_OW': 1.0,
        'pdev-fdp_SG': 1.0,
        'pdev-fdp_SH': 1.0,
        'pdev-fdp_SO': 1.0,
        'pdev-fdp_SZ': 1.0,
        'pdev-fdp_TG': 1.0,
        'pdev-fdp_TI': 1.0,
        'pdev-fdp_UR': 1.0,
        'pdev-fdp_VD': 1.0,
        'pdev-fdp_VS': 1.0,
        'pdev-fdp_VSr': 1.0,
        'pdev-fdp_Vso': 1.0,
        'pdev-fdp_ZG': 1.0,
        'pdev-fdp_ZH': 1.0,
        'pdev-jfdp_CH': 1.0,
        'pdev-jfdp_AG': 1.0,
        'pdev-jfdp_BL': 1.0,
        'pdev-jfdp_FR': 1.0,
        'pdev-jfdp_GR': 1.0,
        'pdev-jfdp_JU': 1.0,
        'pdev-jfdp_LU': 1.0,
        'pdev-jfdp_SH': 1.0,
        'pdev-jfdp_TI': 1.0,
        'pdev-jfdp_VD': 1.0,
        'pdev-jfdp_ZH': 1.0,
        'pdev-fps_AG': 1.0,
        'pdev-fps_AI': 1.0,
        'pdev-fps_BE': 1.0,
        'pdev-fps_BL': 1.0,
        'pdev-fps_BS': 1.0,
        'pdev-fps_SG': 1.0,
        'pdev-fps_SH': 1.0,
        'pdev-fps_SO': 1.0,
        'pdev-fps_TG': 1.0,
        'pdev-fps_ZH': 1.0,
        'pdev-glp_AG': 1.0,
        'pdev-glp_AI': 1.0,
        'pdev-glp_AR': 1.0,
        'pdev-glp_BE': 1.0,
        'pdev-glp_BL': 1.0,
        'pdev-glp_BS': 1.0,
        'pdev-glp_FR': 1.0,
        'pdev-glp_GE': 1.0,
        'pdev-glp_GL': 1.0,
        'pdev-glp_GR': 1.0,
        'pdev-glp_JU': 1.0,
        'pdev-glp_LU': 1.0,
        'pdev-glp_NE': 1.0,
        'pdev-glp_NW': 1.0,
        'pdev-glp_OW': 1.0,
        'pdev-glp_SG': 1.0,
        'pdev-glp_SH': 1.0,
        'pdev-glp_SO': 1.0,
        'pdev-glp_SZ': 1.0,
        'pdev-glp_TG': 1.0,
        'pdev-glp_TI': 1.0,
        'pdev-glp_UR': 1.0,
        'pdev-glp_VD': 1.0,
        'pdev-glp_VS': 1.0,
        'pdev-glp_VSr': 1.0,
        'pdev-glp_VSo': 1.0,
        'pdev-glp_ZG': 1.0,
        'pdev-glp_ZH': 1.0,
        'pdev-jglp_CH': 1.0,
        'pdev-gps_AG': 66.0,
        'pdev-gps_AI': 66.0,
        'pdev-gps_AR': 66.0,
        'pdev-gps_BE': 66.0,
        'pdev-gps_BL': 66.0,
        'pdev-gps_BS': 66.0,
        'pdev-gps_FR': 66.0,
        'pdev-gps_GE': 66.0,
        'pdev-gps_GL': 66.0,
        'pdev-gps_GR': 66.0,
        'pdev-gps_JU': 66.0,
        'pdev-gps_LU': 66.0,
        'pdev-gps_NE': 66.0,
        'pdev-gps_NW': 66.0,
        'pdev-gps_OW': 66.0,
        'pdev-gps_SG': 66.0,
        'pdev-gps_SH': 66.0,
        'pdev-gps_SO': 66.0,
        'pdev-gps_SZ': 66.0,
        'pdev-gps_TG': 66.0,
        'pdev-gps_TI': 66.0,
        'pdev-gps_UR': 66.0,
        'pdev-gps_VD': 66.0,
        'pdev-gps_VS': 66.0,
        'pdev-gps_VSr': 66.0,
        'pdev-gps_VSo': 66.0,
        'pdev-gps_ZG': 66.0,
        'pdev-gps_ZH': 66.0,
        'pdev-jgps_CH': 66.0,
        'pdev-kvp_SG': 1.0,
        'pdev-lps_BE': 1.0,
        'pdev-lps_BL': 1.0,
        'pdev-lps_BS': 1.0,
        'pdev-lps_FR': 1.0,
        'pdev-lps_GE': 1.0,
        'pdev-lps_JU': 1.0,
        'pdev-lps_NE': 1.0,
        'pdev-lps_SG': 1.0,
        'pdev-lps_TI': 1.0,
        'pdev-lps_VD': 1.0,
        'pdev-lps_VS': 1.0,
        'pdev-lps_ZH': 1.0,
        'pdev-jlps_CH': 1.0,
        'pdev-jlps_SO': 1.0,
        'pdev-jlps_TI': 1.0,
        'pdev-ldu_AG': 1.0,
        'pdev-ldu_AR': 1.0,
        'pdev-ldu_BE': 1.0,
        'pdev-ldu_BL': 1.0,
        'pdev-ldu_BS': 1.0,
        'pdev-ldu_GR': 1.0,
        'pdev-ldu_LU': 1.0,
        'pdev-ldu_NE': 1.0,
        'pdev-ldu_SG': 1.0,
        'pdev-ldu_SH': 1.0,
        'pdev-ldu_SO': 1.0,
        'pdev-ldu_TG': 1.0,
        'pdev-ldu_VD': 1.0,
        'pdev-ldu_ZG': 1.0,
        'pdev-ldu_ZH': 1.0,
        'pdev-jldu_CH': 1.0,
        'pdev-poch_SO': 2.0,
        'pdev-poch_ZH': 2.0,
        'pdev-pda_BE': 1.0,
        'pdev-pda_BL': 1.0,
        'pdev-pda_BS': 1.0,
        'pdev-pda_GE': 1.0,
        'pdev-pda_JU': 1.0,
        'pdev-pda_NE': 1.0,
        'pdev-pda_SG': 1.0,
        'pdev-pda_TI': 1.0,
        'pdev-pda_VD': 1.0,
        'pdev-pda_ZH': 1.0,
        'pdev-jpda_CH': 1.0,
        'pdev-rep_AG': 1.0,
        'pdev-rep_GE': 1.0,
        'pdev-rep_NE': 1.0,
        'pdev-rep_TG': 1.0,
        'pdev-rep_VD': 1.0,
        'pdev-rep_ZH': 1.0,
        'pdev-sd_AG': 1.0,
        'pdev-sd_BE': 1.0,
        'pdev-sd_BL': 1.0,
        'pdev-sd_BS': 1.0,
        'pdev-sd_FR': 1.0,
        'pdev-sd_GE': 1.0,
        'pdev-sd_GR': 1.0,
        'pdev-sd_LU': 1.0,
        'pdev-sd_NE': 1.0,
        'pdev-sd_SG': 1.0,
        'pdev-sd_SO': 1.0,
        'pdev-sd_TG': 1.0,
        'pdev-sd_TI': 1.0,
        'pdev-sd_VD': 1.0,
        'pdev-sd_ZH': 1.0,
        'pdev-jsd_CH': 1.0,
        'pdev-sps_AG': 1.0,
        'pdev-sps_AI': 1.0,
        'pdev-sps_AR': 1.0,
        'pdev-sps_BE': 1.0,
        'pdev-sps_BL': 1.0,
        'pdev-sps_BS': 1.0,
        'pdev-sps_FR': 1.0,
        'pdev-sps_GE': 1.0,
        'pdev-sps_GL': 1.0,
        'pdev-sps_GR': 1.0,
        'pdev-sps_JU': 1.0,
        'pdev-sps_LU': 1.0,
        'pdev-sps_NE': 1.0,
        'pdev-sps_NW': 1.0,
        'pdev-sps_OW': 1.0,
        'pdev-sps_SG': 1.0,
        'pdev-sps_SH': 1.0,
        'pdev-sps_SO': 1.0,
        'pdev-sps_SZ': 1.0,
        'pdev-sps_TG': 1.0,
        'pdev-sps_TI': 1.0,
        'pdev-sps_UR': 1.0,
        'pdev-sps_VD': 1.0,
        'pdev-sps_VS': 1.0,
        'pdev-sps_VSr': 1.0,
        'pdev-sps_VSo': 1.0,
        'pdev-sps_ZG': 1.0,
        'pdev-sps_ZH': 1.0,
        'pdev-juso_CH': 1.0,
        'pdev-juso_BE': 1.0,
        'pdev-juso_GE': 1.0,
        'pdev-juso_JU': 1.0,
        'pdev-juso_TI': 1.0,
        'pdev-juso_VS': 1.0,
        'pdev-juso_ZH': 1.0,
        'pdev-svp_AG': 3.0,
        'pdev-svp_AI': 3.0,
        'pdev-svp_AR': 3.0,
        'pdev-svp_BE': 3.0,
        'pdev-svp_BL': 3.0,
        'pdev-svp_BS': 3.0,
        'pdev-svp_FR': 3.0,
        'pdev-svp_GE': 3.0,
        'pdev-svp_GL': 3.0,
        'pdev-svp_GR': 3.0,
        'pdev-svp_JU': 3.0,
        'pdev-svp_LU': 3.0,
        'pdev-svp_NE': 3.0,
        'pdev-svp_NW': 3.0,
        'pdev-svp_OW': 3.0,
        'pdev-svp_SG': 3.0,
        'pdev-svp_SH': 3.0,
        'pdev-svp_SO': 3.0,
        'pdev-svp_SZ': 3.0,
        'pdev-svp_TG': 3.0,
        'pdev-svp_TI': 3.0,
        'pdev-svp_UR': 3.0,
        'pdev-svp_VD': 3.0,
        'pdev-svp_VS': 3.0,
        'pdev-svp_VSr': 3.0,
        'pdev-svp_VSo': 3.0,
        'pdev-svp_ZG': 3.0,
        'pdev-svp_ZH': 3.0,
        'pdev-jsvp_CH': 3.0,
        'pdev-jsvp_AG': 3.0,
        'pdev-jsvp_BE': 3.0,
        'pdev-jsvp_GE': 3.0,
        'pdev-jsvp_SH': 3.0,
        'pdev-jsvp_UR': 3.0,
        'pdev-jsvp_ZH': 3.0,
        'pdev-sgb_AG': 1.0,
        'pdev-sgb_JU': 1.0,
        'pdev-sgb_VS': 1.0,
        'pdev-sgv_AG': 1.0,
        'pdev-sgv_BS': 1.0,
        'pdev-sgv_SH': 1.0,
        'pdev-vpod_GE': 1.0,
        'pdev-vpod_VD': 1.0,
        'pdev-mitte_frauen': 2.0,
        'pdev-mitte_AG': 2.0,
        'pdev-mitte_AI': 2.0,
        'pdev-mitte_AR': 2.0,
        'pdev-mitte_BE': 2.0,
        'pdev-mitte_BL': 2.0,
        'pdev-mitte_BS': 2.0,
        'pdev-mitte_FR': 2.0,
        'pdev-mitte_GE': 2.0,
        'pdev-mitte_GL': 2.0,
        'pdev-mitte_GR': 2.0,
        'pdev-mitte_JU': 2.0,
        'pdev-mitte_LU': 2.0,
        'pdev-mitte_NE': 2.0,
        'pdev-mitte_NW': 2.0,
        'pdev-mitte_OW': 2.0,
        'pdev-mitte_SG': 2.0,
        'pdev-mitte_SH': 2.0,
        'pdev-mitte_SO': 2.0,
        'pdev-mitte_SZ': 2.0,
        'pdev-mitte_TG': 2.0,
        'pdev-mitte_TI': 2.0,
        'pdev-mitte_UR': 2.0,
        'pdev-mitte_VD': 2.0,
        'pdev-mitte_VS': 2.0,
        'pdev-mitte_VSr': 2.0,
        'pdev-mitte_VSo': 2.0,
        'pdev-mitte_ZG': 2.0,
        'pdev-mitte_ZH': 2.0,
        'pdev-jmitte_CH': 2.0,
        'pdev-jmitte_AG': 2.0,
        'pdev-jmitte_AI': 2.0,
        'pdev-jmitte_AR': 2.0,
        'pdev-jmitte_BE': 2.0,
        'pdev-jmitte_BL': 2.0,
        'pdev-jmitte_BS': 2.0,
        'pdev-jmitte_FR': 2.0,
        'pdev-jmitte_GE': 2.0,
        'pdev-jmitte_GL': 2.0,
        'pdev-jmitte_GR': 2.0,
        'pdev-jmitte_JU': 2.0,
        'pdev-jmitte_LU': 2.0,
        'pdev-jmitte_NE': 2.0,
        'pdev-jmitte_NW': 2.0,
        'pdev-jmitte_OW': 2.0,
        'pdev-jmitte_SG': 2.0,
        'pdev-jmitte_SH': 2.0,
        'pdev-jmitte_SO': 2.0,
        'pdev-jmitte_SZ': 2.0,
        'pdev-jmitte_TG': 2.0,
        'pdev-jmitte_TI': 2.0,
        'pdev-jmitte_UR': 2.0,
        'pdev-jmitte_VD': 2.0,
        'pdev-jmitte_VS': 2.0,
        'pdev-jmitte_VSr': 2.0,
        'pdev-jmitte_VSo': 2.0,
        'pdev-jmitte_ZG': 2.0,
        'pdev-jmitte_ZH': 2.0,
        'nr-wahl': 1990.0,
        'w-fdp': 1.1,
        'w-cvp': 2.1,
        'w-sp': 3.1,
        'w-svp': 4.1,
        'w-lps': 5.1,
        'w-ldu': 6.1,
        'w-evp': 7.1,
        'w-csp': 8.1,
        'w-pda': 9.1,
        'w-poch': 10.1,
        'w-gps': 11.1,
        'w-sd': 12.1,
        'w-rep': 13.1,
        'w-edu': 14.1,
        'w-fps': 15.1,
        'w-lega': 16.1,
        'w-kvp': 17.1,
        'w-glp': 18.1,
        'w-bdp': 19.1,
        'w-mcg': 20.2,
        'w-mitte': 20.1,
        'w-ubrige': 21.2,
        'ja-lager': 22.2,
        'nein-lager': 23.2,
        'keinepar-summe': 25.2,
        'leer-summe': 26.2,
        'freigabe-summe': 27.2,
        'neutral-summe': 24.2,
        'unbekannt-summe': 28.2,
        'urheber': 'Initiator D',
        'urheber-fr': 'Initiator F',
        'anneepolitique': 'anneepolitique',
        'bfsmap-de': 'map de',
        'bfsmap-fr': 'map fr',
        'bfsmap-en': 'map en',
        'bfsdash-de': 'https://dashboard.de',
        'bfsdash-fr': 'https://dashboard.fr',
        'bfsdash-en': 'https://dashboard.en',
        'poster_ja_mfg': (
            'https://museum.ch/objects/1 '
            'https://museum.ch/objects/2'
        ),
        'poster_nein_mfg': (
            'https://museum.ch/objects/3 '
            'https://museum.ch/objects/4'
        ),
        'poster_ja_bs': (
            'https://plakatsammlungbasel.ch/objects/1 '
            'https://plakatsammlungbasel.ch/objects/2'
        ),
        'poster_nein_bs': (
            'https://plakatsammlungbasel.ch/objects/3 '
            'https://plakatsammlungbasel.ch/objects/4'
        ),
        'poster_ja_sa': (
            'https://sozialarchiv.ch/objects/1 '
            'https://sozialarchiv.ch/objects/2'
        ),
        'poster_nein_sa': (
            'https://sozialarchiv.ch/objects/3 '
            'https://sozialarchiv.ch/objects/4'
        ),
        'nach_cockpit_d': 'https://post.vote.poll/de',
        'nach_cockpit_f': 'https://post.vote.poll/fr',
        'nach_cockpit_e': 'https://post.vote.poll/en',
        'inserate-total': 1001,
        'inserate-jaanteil': 10.06,
        'mediares-tot': 1007,
        'mediaton-tot': 10.10,
        'web-yes-1-de': 'https://yes1.de',
        'web-yes-2-de': 'https://yes2.de',
        'web-yes-3-de': 'https://yes3.de',
        'web-no-1-de': 'https://no1.de',
        'web-no-2-de': 'https://no2.de',
        'web-no-3-de': 'https://no3.de',
        'web-yes-1-fr': 'https://yes1.fr',
        'web-yes-2-fr': 'https://yes2.fr',
        'web-yes-3-fr': 'https://yes3.fr',
        'web-no-1-fr': 'https://no1.fr',
        'web-no-2-fr': 'https://no2.fr',
        'web-no-3-fr': 'https://no3.fr',
        'finanz-ja-tot': 10000,
        'finanz-nein-tot': 20000,
        'finanz-ja-gr-de': 'Donor 1 D, Donor 2 D',
        'finanz-ja-gr-fr': 'Donor 1 F, Donor 2 F',
        'finanz-nein-gr-de': 'Donor D',
        'finanz-nein-gr-fr': 'Donor F',
        'finanz-link-de': 'https://finances.de',
        'finanz-link-fr': 'https://finances.fr',
    }
    assert xlsx == expected

    assert csv.keys() == xlsx.keys()
