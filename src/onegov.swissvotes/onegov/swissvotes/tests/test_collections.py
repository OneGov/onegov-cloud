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
from psycopg2.extras import NumericRange
from pytest import skip
from xlrd import open_workbook
from pytz import utc


def test_pages(session):
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


def test_votes(swissvotes_app):
    votes = SwissVoteCollection(swissvotes_app)
    assert votes.last_modified is None

    with freeze_time(datetime(2019, 1, 1, 10, tzinfo=utc)):
        vote = votes.add(
            id=1,
            bfs_number=Decimal('100.1'),
            date=date(1990, 6, 2),
            decade=NumericRange(1990, 1999),
            legislation_number=4,
            legislation_decade=NumericRange(1990, 1994),
            title_de="Vote DE",
            title_fr="Vote FR",
            short_title_de="V D",
            short_title_fr="V F",
            votes_on_same_day=2,
            _legal_form=1
        )

    assert vote.id == 1
    assert vote.bfs_number == Decimal('100.1')
    assert vote.date == date(1990, 6, 2)
    assert vote.decade == NumericRange(1990, 1999)
    assert vote.legislation_number == 4
    assert vote.legislation_decade == NumericRange(1990, 1994)
    assert vote.title_de == "Vote DE"
    assert vote.title_fr == "Vote FR"
    assert vote.short_title_de == "V D"
    assert vote.short_title_fr == "V F"
    assert vote.votes_on_same_day == 2
    assert vote.legal_form == "Mandatory referendum"

    assert votes.last_modified == datetime(2019, 1, 1, 10, tzinfo=utc)
    assert votes.by_bfs_number('100.1') == vote
    assert votes.by_bfs_number(Decimal('100.1')) == vote


def test_votes_default(swissvotes_app):
    votes = SwissVoteCollection(
        swissvotes_app,
        page=2,
        from_date=3,
        to_date=4,
        legal_form=5,
        result=6,
        policy_area=7,
        term=8,
        full_text=9,
        position_federal_council=10,
        position_national_council=11,
        position_council_of_states=12,
        sort_by=13,
        sort_order=14
    )
    assert votes.page == 2
    assert votes.from_date == 3
    assert votes.to_date == 4
    assert votes.legal_form == 5
    assert votes.result == 6
    assert votes.policy_area == 7
    assert votes.term == 8
    assert votes.full_text == 9
    assert votes.position_federal_council == 10
    assert votes.position_national_council == 11
    assert votes.position_council_of_states == 12
    assert votes.sort_by == 13
    assert votes.sort_order == 14

    votes = votes.default()
    assert votes.page is None
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


def test_votes_pagination(swissvotes_app):
    votes = SwissVoteCollection(swissvotes_app)

    assert votes.pages_count == 0
    assert votes.batch == []
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
            decade=NumericRange(1990, 1999),
            legislation_number=4,
            legislation_decade=NumericRange(1990, 1994),
            title_de="Vote",
            title_fr="Vote",
            short_title_de="Vote",
            short_title_fr="Vote",
            votes_on_same_day=2,
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


def test_votes_term_expression(swissvotes_app):
    def term_expression(term):
        return SwissVoteCollection(swissvotes_app, term=term).term_expression

    assert term_expression(None) == ''
    assert term_expression('') == ''
    assert term_expression('a,1.$b !c*d*') == 'a,1.b <-> cd:*'


def test_votes_term_filter(swissvotes_app):
    assert SwissVoteCollection(swissvotes_app).term_filter == []
    assert SwissVoteCollection(swissvotes_app, term='').term_filter == []
    assert SwissVoteCollection(swissvotes_app, term='', full_text=True)\
        .term_filter == []

    def compiled(**kwargs):
        list_ = SwissVoteCollection(swissvotes_app, **kwargs).term_filter
        return [
            str(statement.compile(compile_kwargs={"literal_binds": True}))
            for statement in list_
        ]

    c_title_de = "to_tsvector('german', swissvotes.title_de)"
    c_title_fr = "to_tsvector('french', swissvotes.title_fr)"
    c_short_title_de = "to_tsvector('german', swissvotes.short_title_de)"
    c_short_title_fr = "to_tsvector('french', swissvotes.short_title_fr)"
    c_keyword = "to_tsvector('german', swissvotes.keyword)"
    c_initiator = "to_tsvector('german', swissvotes.initiator)"
    c_text_de = 'swissvotes."searchable_text_de_CH"'
    c_text_fr = 'swissvotes."searchable_text_fr_CH"'

    assert compiled(term='100') == [
        'swissvotes.bfs_number = 100',
        'swissvotes.procedure_number = 100',
        f"{c_title_de} @@ to_tsquery('german', '100')",
        f"{c_title_fr} @@ to_tsquery('french', '100')",
        f"{c_short_title_de} @@ to_tsquery('german', '100')",
        f"{c_short_title_fr} @@ to_tsquery('french', '100')",
        f"{c_keyword} @@ to_tsquery('german', '100')",
    ]

    assert compiled(term='100.1') == [
        'swissvotes.bfs_number = 100.1',
        'swissvotes.procedure_number = 100.1',
        f"{c_title_de} @@ to_tsquery('german', '100.1')",
        f"{c_title_fr} @@ to_tsquery('french', '100.1')",
        f"{c_short_title_de} @@ to_tsquery('german', '100.1')",
        f"{c_short_title_fr} @@ to_tsquery('french', '100.1')",
        f"{c_keyword} @@ to_tsquery('german', '100.1')",
    ]

    assert compiled(term='abc') == [
        f"{c_title_de} @@ to_tsquery('german', 'abc')",
        f"{c_title_fr} @@ to_tsquery('french', 'abc')",
        f"{c_short_title_de} @@ to_tsquery('german', 'abc')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'abc')",
        f"{c_keyword} @@ to_tsquery('german', 'abc')",
    ]
    assert compiled(term='abc', full_text=True) == [
        f"{c_title_de} @@ to_tsquery('german', 'abc')",
        f"{c_title_fr} @@ to_tsquery('french', 'abc')",
        f"{c_short_title_de} @@ to_tsquery('german', 'abc')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'abc')",
        f"{c_keyword} @@ to_tsquery('german', 'abc')",
        f"{c_initiator} @@ to_tsquery('german', 'abc')",
        f"{c_text_de} @@ to_tsquery('german', 'abc')",
        f"{c_text_fr} @@ to_tsquery('french', 'abc')",
    ]

    assert compiled(term='Müller') == [
        f"{c_title_de} @@ to_tsquery('german', 'Müller')",
        f"{c_title_fr} @@ to_tsquery('french', 'Müller')",
        f"{c_short_title_de} @@ to_tsquery('german', 'Müller')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'Müller')",
        f"{c_keyword} @@ to_tsquery('german', 'Müller')",
    ]

    assert compiled(term='20,20') == [
        f"{c_title_de} @@ to_tsquery('german', '20,20')",
        f"{c_title_fr} @@ to_tsquery('french', '20,20')",
        f"{c_short_title_de} @@ to_tsquery('german', '20,20')",
        f"{c_short_title_fr} @@ to_tsquery('french', '20,20')",
        f"{c_keyword} @@ to_tsquery('german', '20,20')",
    ]

    assert compiled(term='Neu!') == [
        f"{c_title_de} @@ to_tsquery('german', 'Neu')",
        f"{c_title_fr} @@ to_tsquery('french', 'Neu')",
        f"{c_short_title_de} @@ to_tsquery('german', 'Neu')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'Neu')",
        f"{c_keyword} @@ to_tsquery('german', 'Neu')",
    ]

    assert compiled(term='H P Müller') == [
        f"{c_title_de} @@ to_tsquery('german', 'H <-> P <-> Müller')",
        f"{c_title_fr} @@ to_tsquery('french', 'H <-> P <-> Müller')",
        f"{c_short_title_de} @@ to_tsquery('german', 'H <-> P <-> Müller')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'H <-> P <-> Müller')",
        f"{c_keyword} @@ to_tsquery('german', 'H <-> P <-> Müller')",
    ]

    assert compiled(term='x AND y') == [
        f"{c_title_de} @@ to_tsquery('german', 'x <-> AND <-> y')",
        f"{c_title_fr} @@ to_tsquery('french', 'x <-> AND <-> y')",
        f"{c_short_title_de} @@ to_tsquery('german', 'x <-> AND <-> y')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'x <-> AND <-> y')",
        f"{c_keyword} @@ to_tsquery('german', 'x <-> AND <-> y')",
    ]

    assert compiled(term='x | y') == [
        f"{c_title_de} @@ to_tsquery('german', 'x <-> y')",
        f"{c_title_fr} @@ to_tsquery('french', 'x <-> y')",
        f"{c_short_title_de} @@ to_tsquery('german', 'x <-> y')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'x <-> y')",
        f"{c_keyword} @@ to_tsquery('german', 'x <-> y')",
    ]

    assert compiled(term='y ! y') == [
        f"{c_title_de} @@ to_tsquery('german', 'y <-> y')",
        f"{c_title_fr} @@ to_tsquery('french', 'y <-> y')",
        f"{c_short_title_de} @@ to_tsquery('german', 'y <-> y')",
        f"{c_short_title_fr} @@ to_tsquery('french', 'y <-> y')",
        f"{c_keyword} @@ to_tsquery('german', 'y <-> y')",
    ]


def test_votes_query(swissvotes_app):
    votes = SwissVoteCollection(swissvotes_app)
    votes.add(
        id=1,
        bfs_number=Decimal('100'),
        date=date(1990, 6, 2),
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title_de="Abstimmung über diese Sache",
        title_fr="Vote sur cette question",
        short_title_de="diese Sache",
        short_title_fr="cette question",
        votes_on_same_day=1,
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
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title_de="Wir wollen diese Version die Sache",
        title_fr="Nous voulons cette version de la chose",
        short_title_de="diese Version",
        short_title_fr="cette version",
        keyword="Variant A of X",
        initiator="The group that wants something",
        votes_on_same_day=1,
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
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title_de="Wir wollen nochmal etwas anderes",
        title_fr="Nous voulons encore une autre version de la chose",
        short_title_de="Nochmals etwas anderes",
        short_title_fr="encore une autre version",
        keyword="Variant B of X",
        votes_on_same_day=1,
        _legal_form=2,
        descriptor_3_level_1=Decimal('8'),
        descriptor_3_level_2=Decimal('8.3'),
        _position_federal_council=1,
        _position_council_of_states=1,
        _position_national_council=1,
        _result=2
    )

    def count(**kwargs):
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
    assert count(term='riant') == 0
    assert count(term='A of X') == 1
    assert count(term='group') == 0
    assert count(term='group', full_text=True) == 1
    assert count(term='The group that wants something', full_text=True) == 1


def test_votes_query_attachments(swissvotes_app, attachments,
                                 postgres_version):
    if int(postgres_version.split('.')[0]) < 10:
        skip("PostgreSQL 10+")

    votes = SwissVoteCollection(swissvotes_app)
    votes.add(
        id=1,
        bfs_number=Decimal('100'),
        date=date(1990, 6, 2),
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title_de="Vote on that one thing",
        title_fr="Vote on that one thing",
        short_title_de="Vote on that one thing",
        short_title_fr="Vote on that one thing",
        votes_on_same_day=1,
        _legal_form=1,
    )
    votes.add(
        id=2,
        bfs_number=Decimal('200.1'),
        date=date(1990, 9, 2),
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title_de="We want this version the thing",
        title_fr="We want this version the thing",
        short_title_de="We want this version the thing",
        short_title_fr="We want this version the thing",
        votes_on_same_day=1,
        _legal_form=2,
    )
    vote = votes.add(
        id=3,
        bfs_number=Decimal('200.2'),
        date=date(1990, 9, 2),
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title_de="We want that version of the thing",
        title_fr="We want that version of the thing",
        short_title_de="We want that version of the thing",
        short_title_fr="We want that version of the thing",
        votes_on_same_day=1,
        _legal_form=2,
    )
    for name, attachment in attachments.items():
        setattr(vote, name, attachment)
    votes.session.flush()

    def count(**kwargs):
        return SwissVoteCollection(swissvotes_app, **kwargs).query().count()

    assert count() == 3

    assert count(term='Abstimmungstext') == 0
    assert count(term='Abstimmungstext', full_text=True) == 1
    assert count(term='Abst*', full_text=True) == 1
    assert count(term='conseil', full_text=True) == 1
    assert count(term='Parlamentdebatte', full_text=True) == 1
    assert count(term='Réalisation', full_text=True) == 1
    assert count(term='booklet', full_text=True) == 0


def test_votes_order(swissvotes_app):
    votes = SwissVoteCollection(swissvotes_app)

    for index, title in enumerate(('Firsţ', 'Śecond', 'Thirḓ'), start=1):
        votes.add(
            id=index,
            bfs_number=Decimal(str(index)),
            date=date(1990, 6, index),
            decade=NumericRange(1990, 1999),
            legislation_number=1,
            legislation_decade=NumericRange(1990, 1994),
            title_de=title,
            title_fr=''.join(reversed(title)),
            short_title_de=title,
            short_title_fr=''.join(reversed(title)),
            votes_on_same_day=1,
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

    votes.app.session_manager.current_locale = 'fr_CH'
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


def test_votes_available_descriptors(swissvotes_app):
    votes = SwissVoteCollection(swissvotes_app)
    assert votes.available_descriptors == [set(), set(), set()]

    votes.add(
        id=1,
        bfs_number=Decimal('1'),
        date=date(1990, 6, 2),
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        votes_on_same_day=2,
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
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        votes_on_same_day=2,
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
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        votes_on_same_day=2,
        _legal_form=1,
        descriptor_3_level_1=Decimal('8'),
        descriptor_3_level_2=Decimal('8.3'),
    )

    assert SwissVoteCollection(swissvotes_app).available_descriptors == [
        {Decimal('1.00'), Decimal('4.00'), Decimal('8.00'), Decimal('10.00')},
        {Decimal('1.60'), Decimal('4.20'), Decimal('8.30'), Decimal('10.30')},
        {Decimal('1.62'), Decimal('4.21'), Decimal('10.33'), Decimal('10.35')}
    ]


def test_votes_update(swissvotes_app):
    votes = SwissVoteCollection(swissvotes_app)

    added, updated = votes.update([
        SwissVote(
            bfs_number=Decimal('1'),
            date=date(1990, 6, 1),
            decade=NumericRange(1990, 1999),
            legislation_number=1,
            legislation_decade=NumericRange(1990, 1994),
            title_de="First",
            title_fr="First",
            short_title_de="First",
            short_title_fr="First",
            votes_on_same_day=2,
            _legal_form=1,
        ),
        SwissVote(
            bfs_number=Decimal('2'),
            date=date(1990, 6, 1),
            decade=NumericRange(1990, 1999),
            legislation_number=2,
            legislation_decade=NumericRange(1990, 1994),
            title_de="Second",
            title_fr="Second",
            short_title_de="Second",
            short_title_fr="Second",
            votes_on_same_day=2,
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
            decade=NumericRange(1990, 1999),
            legislation_number=1,
            legislation_decade=NumericRange(1990, 1994),
            title_de="First",
            title_fr="First",
            short_title_de="First",
            short_title_fr="First",
            votes_on_same_day=2,
            _legal_form=1,
        )
    ])
    assert added == 0
    assert updated == 0

    added, updated = votes.update([
        SwissVote(
            bfs_number=Decimal('1'),
            date=date(1990, 6, 1),
            decade=NumericRange(1990, 1999),
            legislation_number=1,
            legislation_decade=NumericRange(1990, 1994),
            title_de="First vote",
            title_fr="First vote",
            short_title_de="First vote",
            short_title_fr="First vote",
            votes_on_same_day=2,
            _legal_form=1,
        )
    ])
    assert added == 0
    assert updated == 1
    assert votes.by_bfs_number(Decimal('1')).title == 'First vote'


def test_votes_export(swissvotes_app):
    votes = SwissVoteCollection(swissvotes_app)
    vote = votes.add(
        bfs_number=Decimal('100.1'),
        date=date(1990, 6, 2),
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title_de="Vote DE",
        title_fr="Vote FR",
        short_title_de="V D",
        short_title_fr="V F",
        keyword="Keyword",
        votes_on_same_day=2,
        _legal_form=1,
        initiator="Initiator",
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
        result_eligible_voters=2,
        result_votes_empty=3,
        result_votes_invalid=4,
        result_votes_valid=5,
        result_votes_total=6,
        result_turnout=Decimal('20.01'),
        _result_people_accepted=1,
        result_people_yeas=8,
        result_people_nays=9,
        result_people_yeas_p=Decimal('40.01'),
        _result_cantons_accepted=1,
        result_cantons_yeas=Decimal('1.5'),
        result_cantons_nays=Decimal('24.5'),
        result_cantons_yeas_p=Decimal('60.01')
    )
    vote.result_ag_eligible_voters = 101
    vote.result_ag_votes_valid = 102
    vote.result_ag_votes_total = 103
    vote.result_ag_turnout = Decimal('10.40')
    vote.result_ag_yeas = 105
    vote.result_ag_nays = 107
    vote.result_ag_yeas_p = Decimal('10.80')
    vote._result_ag_accepted = 0
    vote.result_ai_eligible_voters = 101
    vote.result_ai_votes_valid = 102
    vote.result_ai_votes_total = 103
    vote.result_ai_turnout = Decimal('10.40')
    vote.result_ai_yeas = 105
    vote.result_ai_nays = 107
    vote.result_ai_yeas_p = Decimal('10.80')
    vote._result_ai_accepted = 0
    vote.result_ar_eligible_voters = 101
    vote.result_ar_votes_valid = 102
    vote.result_ar_votes_total = 103
    vote.result_ar_turnout = Decimal('10.40')
    vote.result_ar_yeas = 105
    vote.result_ar_nays = 107
    vote.result_ar_yeas_p = Decimal('10.80')
    vote._result_ar_accepted = 0
    vote.result_be_eligible_voters = 101
    vote.result_be_votes_valid = 102
    vote.result_be_votes_total = 103
    vote.result_be_turnout = Decimal('10.40')
    vote.result_be_yeas = 105
    vote.result_be_nays = 107
    vote.result_be_yeas_p = Decimal('10.80')
    vote._result_be_accepted = 0
    vote.result_bl_eligible_voters = 101
    vote.result_bl_votes_valid = 102
    vote.result_bl_votes_total = 103
    vote.result_bl_turnout = Decimal('10.40')
    vote.result_bl_yeas = 105
    vote.result_bl_nays = 107
    vote.result_bl_yeas_p = Decimal('10.80')
    vote._result_bl_accepted = 0
    vote.result_bs_eligible_voters = 101
    vote.result_bs_votes_valid = 102
    vote.result_bs_votes_total = 103
    vote.result_bs_turnout = Decimal('10.40')
    vote.result_bs_yeas = 105
    vote.result_bs_nays = 107
    vote.result_bs_yeas_p = Decimal('10.80')
    vote._result_bs_accepted = 0
    vote.result_fr_eligible_voters = 101
    vote.result_fr_votes_valid = 102
    vote.result_fr_votes_total = 103
    vote.result_fr_turnout = Decimal('10.40')
    vote.result_fr_yeas = 105
    vote.result_fr_nays = 107
    vote.result_fr_yeas_p = Decimal('10.80')
    vote._result_fr_accepted = 0
    vote.result_ge_eligible_voters = 101
    vote.result_ge_votes_valid = 102
    vote.result_ge_votes_total = 103
    vote.result_ge_turnout = Decimal('10.40')
    vote.result_ge_yeas = 105
    vote.result_ge_nays = 107
    vote.result_ge_yeas_p = Decimal('10.80')
    vote._result_ge_accepted = 0
    vote.result_gl_eligible_voters = 101
    vote.result_gl_votes_valid = 102
    vote.result_gl_votes_total = 103
    vote.result_gl_turnout = Decimal('10.40')
    vote.result_gl_yeas = 105
    vote.result_gl_nays = 107
    vote.result_gl_yeas_p = Decimal('10.80')
    vote._result_gl_accepted = 0
    vote.result_gr_eligible_voters = 101
    vote.result_gr_votes_valid = 102
    vote.result_gr_votes_total = 103
    vote.result_gr_turnout = Decimal('10.40')
    vote.result_gr_yeas = 105
    vote.result_gr_nays = 107
    vote.result_gr_yeas_p = Decimal('10.80')
    vote._result_gr_accepted = 0
    vote.result_ju_eligible_voters = 101
    vote.result_ju_votes_valid = 102
    vote.result_ju_votes_total = 103
    vote.result_ju_turnout = Decimal('10.40')
    vote.result_ju_yeas = 105
    vote.result_ju_nays = 107
    vote.result_ju_yeas_p = Decimal('10.80')
    vote._result_ju_accepted = 0
    vote.result_lu_eligible_voters = 101
    vote.result_lu_votes_valid = 102
    vote.result_lu_votes_total = 103
    vote.result_lu_turnout = Decimal('10.40')
    vote.result_lu_yeas = 105
    vote.result_lu_nays = 107
    vote.result_lu_yeas_p = Decimal('10.80')
    vote._result_lu_accepted = 0
    vote.result_ne_eligible_voters = 101
    vote.result_ne_votes_valid = 102
    vote.result_ne_votes_total = 103
    vote.result_ne_turnout = Decimal('10.40')
    vote.result_ne_yeas = 105
    vote.result_ne_nays = 107
    vote.result_ne_yeas_p = Decimal('10.80')
    vote._result_ne_accepted = 0
    vote.result_nw_eligible_voters = 101
    vote.result_nw_votes_valid = 102
    vote.result_nw_votes_total = 103
    vote.result_nw_turnout = Decimal('10.40')
    vote.result_nw_yeas = 105
    vote.result_nw_nays = 107
    vote.result_nw_yeas_p = Decimal('10.80')
    vote._result_nw_accepted = 0
    vote.result_ow_eligible_voters = 101
    vote.result_ow_votes_valid = 102
    vote.result_ow_votes_total = 103
    vote.result_ow_turnout = Decimal('10.40')
    vote.result_ow_yeas = 105
    vote.result_ow_nays = 107
    vote.result_ow_yeas_p = Decimal('10.80')
    vote._result_ow_accepted = 0
    vote.result_sg_eligible_voters = 101
    vote.result_sg_votes_valid = 102
    vote.result_sg_votes_total = 103
    vote.result_sg_turnout = Decimal('10.40')
    vote.result_sg_yeas = 105
    vote.result_sg_nays = 107
    vote.result_sg_yeas_p = Decimal('10.80')
    vote._result_sg_accepted = 0
    vote.result_sh_eligible_voters = 101
    vote.result_sh_votes_valid = 102
    vote.result_sh_votes_total = 103
    vote.result_sh_turnout = Decimal('10.40')
    vote.result_sh_yeas = 105
    vote.result_sh_nays = 107
    vote.result_sh_yeas_p = Decimal('10.80')
    vote._result_sh_accepted = 0
    vote.result_so_eligible_voters = 101
    vote.result_so_votes_valid = 102
    vote.result_so_votes_total = 103
    vote.result_so_turnout = Decimal('10.40')
    vote.result_so_yeas = 105
    vote.result_so_nays = 107
    vote.result_so_yeas_p = Decimal('10.80')
    vote._result_so_accepted = 0
    vote.result_sz_eligible_voters = 101
    vote.result_sz_votes_valid = 102
    vote.result_sz_votes_total = 103
    vote.result_sz_turnout = Decimal('10.40')
    vote.result_sz_yeas = 105
    vote.result_sz_nays = 107
    vote.result_sz_yeas_p = Decimal('10.80')
    vote._result_sz_accepted = 0
    vote.result_tg_eligible_voters = 101
    vote.result_tg_votes_valid = 102
    vote.result_tg_votes_total = 103
    vote.result_tg_turnout = Decimal('10.40')
    vote.result_tg_yeas = 105
    vote.result_tg_nays = 107
    vote.result_tg_yeas_p = Decimal('10.80')
    vote._result_tg_accepted = 0
    vote.result_ti_eligible_voters = 101
    vote.result_ti_votes_valid = 102
    vote.result_ti_votes_total = 103
    vote.result_ti_turnout = Decimal('10.40')
    vote.result_ti_yeas = 105
    vote.result_ti_nays = 107
    vote.result_ti_yeas_p = Decimal('10.80')
    vote._result_ti_accepted = 0
    vote.result_ur_eligible_voters = 101
    vote.result_ur_votes_valid = 102
    vote.result_ur_votes_total = 103
    vote.result_ur_turnout = Decimal('10.40')
    vote.result_ur_yeas = 105
    vote.result_ur_nays = 107
    vote.result_ur_yeas_p = Decimal('10.80')
    vote._result_ur_accepted = 0
    vote.result_vd_eligible_voters = 101
    vote.result_vd_votes_valid = 102
    vote.result_vd_votes_total = 103
    vote.result_vd_turnout = Decimal('10.40')
    vote.result_vd_yeas = 105
    vote.result_vd_nays = 107
    vote.result_vd_yeas_p = Decimal('10.80')
    vote._result_vd_accepted = 0
    vote.result_vs_eligible_voters = 101
    vote.result_vs_votes_valid = 102
    vote.result_vs_votes_total = 103
    vote.result_vs_turnout = Decimal('10.40')
    vote.result_vs_yeas = 105
    vote.result_vs_nays = 107
    vote.result_vs_yeas_p = Decimal('10.80')
    vote._result_vs_accepted = 0
    vote.result_zg_eligible_voters = 101
    vote.result_zg_votes_valid = 102
    vote.result_zg_votes_total = 103
    vote.result_zg_turnout = Decimal('10.40')
    vote.result_zg_yeas = 105
    vote.result_zg_nays = 107
    vote.result_zg_yeas_p = Decimal('10.80')
    vote._result_zg_accepted = 0
    vote.result_zh_eligible_voters = 101
    vote.result_zh_votes_valid = 102
    vote.result_zh_votes_total = 103
    vote.result_zh_turnout = Decimal('10.40')
    vote.result_zh_yeas = 105
    vote.result_zh_nays = 107
    vote.result_zh_yeas_p = Decimal('10.80')
    vote._result_zh_accepted = 0
    vote._department_in_charge = 1
    vote.procedure_number = Decimal('24.557')
    vote._position_federal_council = 1
    vote._position_parliament = 1
    vote._position_national_council = 1
    vote.position_national_council_yeas = 10
    vote.position_national_council_nays = 20
    vote._position_council_of_states = 1
    vote.position_council_of_states_yeas = 30
    vote.position_council_of_states_nays = 40
    vote.duration_federal_assembly = 30
    vote.duration_post_federal_assembly = 31
    vote.duration_initative_collection = 32
    vote.duration_initative_federal_council = 33
    vote.duration_initative_total = 34
    vote.duration_referendum_collection = 35
    vote.duration_referendum_total = 36
    vote.signatures_valid = 40
    vote.signatures_invalid = 41
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
    vote.recommendations_other_yes = "Pro Velo"
    vote.recommendations_other_no = "Biosuisse"
    vote.recommendations_other_free = "Pro Natura, Greenpeace"
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
    }
    vote.national_council_election_year = 1990
    vote.national_council_share_fdp = Decimal('01.10')
    vote.national_council_share_cvp = Decimal('02.10')
    vote.national_council_share_sp = Decimal('03.10')
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
    votes.session.flush()
    votes.session.expire_all()

    file = StringIO()
    votes.export_csv(file)
    file.seek(0)
    rows = list(DictReader(file))
    assert len(rows) == 1
    csv = dict(rows[0])
    assert csv == {
        'anr': '100,1',
        'datum': '02.06.1990',
        'legislatur': '4',
        'legisjahr': '1990-1994',
        'jahrzehnt': '1990-1999',
        'titel_off_d': 'Vote DE',
        'titel_off_f': 'Vote FR',
        'titel_kurz_d': 'V D',
        'titel_kurz_f': 'V F',
        'stichwort': 'Keyword',
        'anzahl': '2',
        'rechtsform': '1',
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
        'berecht': '2',
        'stimmen': '6',
        'bet': '20,01',
        'leer': '3',
        'ungultig': '4',
        'gultig': '5',
        'volkja': '8',
        'volknein': '9',
        'volkja-proz': '40,01',
        'kt-ja': '1,5',
        'kt-nein': '24,5',
        'ktjaproz': '60,01',
        'ag-annahme': '0',
        'ag-berecht': '101',
        'ag-bet': '10,4',
        'ag-gultig': '102',
        'ag-ja': '105',
        'ag-japroz': '10,8',
        'ag-nein': '107',
        'ag-stimmen': '103',
        'ai-annahme': '0',
        'ai-berecht': '101',
        'ai-bet': '10,4',
        'ai-gultig': '102',
        'ai-ja': '105',
        'ai-japroz': '10,8',
        'ai-nein': '107',
        'ai-stimmen': '103',
        'ar-annahme': '0',
        'ar-berecht': '101',
        'ar-bet': '10,4',
        'ar-gultig': '102',
        'ar-ja': '105',
        'ar-japroz': '10,8',
        'ar-nein': '107',
        'ar-stimmen': '103',
        'be-annahme': '0',
        'be-berecht': '101',
        'be-bet': '10,4',
        'be-gultig': '102',
        'be-ja': '105',
        'be-japroz': '10,8',
        'be-nein': '107',
        'be-stimmen': '103',
        'bl-annahme': '0',
        'bl-berecht': '101',
        'bl-bet': '10,4',
        'bl-gultig': '102',
        'bl-ja': '105',
        'bl-japroz': '10,8',
        'bl-nein': '107',
        'bl-stimmen': '103',
        'bs-annahme': '0',
        'bs-berecht': '101',
        'bs-bet': '10,4',
        'bs-gultig': '102',
        'bs-ja': '105',
        'bs-japroz': '10,8',
        'bs-nein': '107',
        'bs-stimmen': '103',
        'fr-annahme': '0',
        'fr-berecht': '101',
        'fr-bet': '10,4',
        'fr-gultig': '102',
        'fr-ja': '105',
        'fr-japroz': '10,8',
        'fr-nein': '107',
        'fr-stimmen': '103',
        'ge-annahme': '0',
        'ge-berecht': '101',
        'ge-bet': '10,4',
        'ge-gultig': '102',
        'ge-ja': '105',
        'ge-japroz': '10,8',
        'ge-nein': '107',
        'ge-stimmen': '103',
        'gl-annahme': '0',
        'gl-berecht': '101',
        'gl-bet': '10,4',
        'gl-gultig': '102',
        'gl-ja': '105',
        'gl-japroz': '10,8',
        'gl-nein': '107',
        'gl-stimmen': '103',
        'gr-annahme': '0',
        'gr-berecht': '101',
        'gr-bet': '10,4',
        'gr-gultig': '102',
        'gr-ja': '105',
        'gr-japroz': '10,8',
        'gr-nein': '107',
        'gr-stimmen': '103',
        'ju-annahme': '0',
        'ju-berecht': '101',
        'ju-bet': '10,4',
        'ju-gultig': '102',
        'ju-ja': '105',
        'ju-japroz': '10,8',
        'ju-nein': '107',
        'ju-stimmen': '103',
        'lu-annahme': '0',
        'lu-berecht': '101',
        'lu-bet': '10,4',
        'lu-gultig': '102',
        'lu-ja': '105',
        'lu-japroz': '10,8',
        'lu-nein': '107',
        'lu-stimmen': '103',
        'ne-annahme': '0',
        'ne-berecht': '101',
        'ne-bet': '10,4',
        'ne-gultig': '102',
        'ne-ja': '105',
        'ne-japroz': '10,8',
        'ne-nein': '107',
        'ne-stimmen': '103',
        'nw-annahme': '0',
        'nw-berecht': '101',
        'nw-bet': '10,4',
        'nw-gultig': '102',
        'nw-ja': '105',
        'nw-japroz': '10,8',
        'nw-nein': '107',
        'nw-stimmen': '103',
        'ow-annahme': '0',
        'ow-berecht': '101',
        'ow-bet': '10,4',
        'ow-gultig': '102',
        'ow-ja': '105',
        'ow-japroz': '10,8',
        'ow-nein': '107',
        'ow-stimmen': '103',
        'sg-annahme': '0',
        'sg-berecht': '101',
        'sg-bet': '10,4',
        'sg-gultig': '102',
        'sg-ja': '105',
        'sg-japroz': '10,8',
        'sg-nein': '107',
        'sg-stimmen': '103',
        'sh-annahme': '0',
        'sh-berecht': '101',
        'sh-bet': '10,4',
        'sh-gultig': '102',
        'sh-ja': '105',
        'sh-japroz': '10,8',
        'sh-nein': '107',
        'sh-stimmen': '103',
        'so-annahme': '0',
        'so-berecht': '101',
        'so-bet': '10,4',
        'so-gultig': '102',
        'so-ja': '105',
        'so-japroz': '10,8',
        'so-nein': '107',
        'so-stimmen': '103',
        'sz-annahme': '0',
        'sz-berecht': '101',
        'sz-bet': '10,4',
        'sz-gultig': '102',
        'sz-ja': '105',
        'sz-japroz': '10,8',
        'sz-nein': '107',
        'sz-stimmen': '103',
        'tg-annahme': '0',
        'tg-berecht': '101',
        'tg-bet': '10,4',
        'tg-gultig': '102',
        'tg-ja': '105',
        'tg-japroz': '10,8',
        'tg-nein': '107',
        'tg-stimmen': '103',
        'ti-annahme': '0',
        'ti-berecht': '101',
        'ti-bet': '10,4',
        'ti-gultig': '102',
        'ti-ja': '105',
        'ti-japroz': '10,8',
        'ti-nein': '107',
        'ti-stimmen': '103',
        'ur-annahme': '0',
        'ur-berecht': '101',
        'ur-bet': '10,4',
        'ur-gultig': '102',
        'ur-ja': '105',
        'ur-japroz': '10,8',
        'ur-nein': '107',
        'ur-stimmen': '103',
        'vd-annahme': '0',
        'vd-berecht': '101',
        'vd-bet': '10,4',
        'vd-gultig': '102',
        'vd-ja': '105',
        'vd-japroz': '10,8',
        'vd-nein': '107',
        'vd-stimmen': '103',
        'vs-annahme': '0',
        'vs-berecht': '101',
        'vs-bet': '10,4',
        'vs-gultig': '102',
        'vs-ja': '105',
        'vs-japroz': '10,8',
        'vs-nein': '107',
        'vs-stimmen': '103',
        'zg-annahme': '0',
        'zg-berecht': '101',
        'zg-bet': '10,4',
        'zg-gultig': '102',
        'zg-ja': '105',
        'zg-japroz': '10,8',
        'zg-nein': '107',
        'zg-stimmen': '103',
        'zh-annahme': '0',
        'zh-berecht': '101',
        'zh-bet': '10,4',
        'zh-gultig': '102',
        'zh-ja': '105',
        'zh-japroz': '10,8',
        'zh-nein': '107',
        'zh-stimmen': '103',
        'dep': '1',
        'gesch_nr': '24,557',
        'br-pos': '1',
        'bv-pos': '1',
        'nr-pos': '1',
        'nrja': '10',
        'nrnein': '20',
        'sr-pos': '1',
        'srja': '30',
        'srnein': '40',
        'dauer_bv': '30',
        'dauer_abst': '31',
        'i-dauer_samm': '32',
        'i-dauer_br': '33',
        'i-dauer_tot': '34',
        'fr-dauer_samm': '35',
        'fr-dauer_tot': '36',
        'unter_g': '40',
        'unter_u': '41',
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
        'p-others_yes': 'Pro Velo',
        'p-others_no': 'Biosuisse',
        'p-others_free': 'Pro Natura, Greenpeace',
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
        'w-ubrige': '21,2',
        'ja-lager': '22,2',
        'nein-lager': '23,2',
        'keinepar-summe': '25,2',
        'leer-summe': '26,2',
        'freigabe-summe': '27,2',
        'neutral-summe': '24,2',
        'unbekannt-summe': '28,2',
        'urheber': 'Initiator',
        'anneepolitique': 'anneepolitique',
        'bfsmap-de': 'map de',
        'bfsmap-fr': 'map fr'
    }

    file = BytesIO()
    votes.export_xlsx(file)
    file.seek(0)
    workbook = open_workbook(file_contents=file.read())
    sheet = workbook.sheet_by_index(0)
    xlsx = dict(
        zip(
            [cell.value for cell in sheet.row(0)],
            [cell.value for cell in sheet.row(1)]
        )
    )
    xlsx = dict(
        zip(
            [cell.value for cell in sheet.row(0)],
            [cell.value for cell in sheet.row(1)]
        )
    )
    assert xlsx == {
        'anr': 100.1,
        'datum': 33026.0,
        'legislatur': 4.0,
        'legisjahr': '1990-1994',
        'jahrzehnt': '1990-1999',
        'titel_off_d': 'Vote DE',
        'titel_off_f': 'Vote FR',
        'titel_kurz_d': 'V D',
        'titel_kurz_f': 'V F',
        'stichwort': 'Keyword',
        'anzahl': 2.0,
        'rechtsform': 1.0,
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
        'berecht': 2.0,
        'stimmen': 6.0,
        'bet': 20.01,
        'leer': 3.0,
        'ungultig': 4.0,
        'gultig': 5.0,
        'volkja': 8.0,
        'volknein': 9.0,
        'volkja-proz': 40.01,
        'kt-ja': 1.5,
        'kt-nein': 24.5,
        'ktjaproz': 60.01,
        'ag-annahme': 0.0,
        'ag-berecht': 101.0,
        'ag-bet': 10.4,
        'ag-gultig': 102.0,
        'ag-ja': 105.0,
        'ag-japroz': 10.8,
        'ag-nein': 107.0,
        'ag-stimmen': 103.0,
        'ai-annahme': 0.0,
        'ai-berecht': 101.0,
        'ai-bet': 10.4,
        'ai-gultig': 102.0,
        'ai-ja': 105.0,
        'ai-japroz': 10.8,
        'ai-nein': 107.0,
        'ai-stimmen': 103.0,
        'ar-annahme': 0.0,
        'ar-berecht': 101.0,
        'ar-bet': 10.4,
        'ar-gultig': 102.0,
        'ar-ja': 105.0,
        'ar-japroz': 10.8,
        'ar-nein': 107.0,
        'ar-stimmen': 103.0,
        'be-annahme': 0.0,
        'be-berecht': 101.0,
        'be-bet': 10.4,
        'be-gultig': 102.0,
        'be-ja': 105.0,
        'be-japroz': 10.8,
        'be-nein': 107.0,
        'be-stimmen': 103.0,
        'bl-annahme': 0.0,
        'bl-berecht': 101.0,
        'bl-bet': 10.4,
        'bl-gultig': 102.0,
        'bl-ja': 105.0,
        'bl-japroz': 10.8,
        'bl-nein': 107.0,
        'bl-stimmen': 103.0,
        'bs-annahme': 0.0,
        'bs-berecht': 101.0,
        'bs-bet': 10.4,
        'bs-gultig': 102.0,
        'bs-ja': 105.0,
        'bs-japroz': 10.8,
        'bs-nein': 107.0,
        'bs-stimmen': 103.0,
        'fr-annahme': 0.0,
        'fr-berecht': 101.0,
        'fr-bet': 10.4,
        'fr-gultig': 102.0,
        'fr-ja': 105.0,
        'fr-japroz': 10.8,
        'fr-nein': 107.0,
        'fr-stimmen': 103.0,
        'ge-annahme': 0.0,
        'ge-berecht': 101.0,
        'ge-bet': 10.4,
        'ge-gultig': 102.0,
        'ge-ja': 105.0,
        'ge-japroz': 10.8,
        'ge-nein': 107.0,
        'ge-stimmen': 103.0,
        'gl-annahme': 0.0,
        'gl-berecht': 101.0,
        'gl-bet': 10.4,
        'gl-gultig': 102.0,
        'gl-ja': 105.0,
        'gl-japroz': 10.8,
        'gl-nein': 107.0,
        'gl-stimmen': 103.0,
        'gr-annahme': 0.0,
        'gr-berecht': 101.0,
        'gr-bet': 10.4,
        'gr-gultig': 102.0,
        'gr-ja': 105.0,
        'gr-japroz': 10.8,
        'gr-nein': 107.0,
        'gr-stimmen': 103.0,
        'ju-annahme': 0.0,
        'ju-berecht': 101.0,
        'ju-bet': 10.4,
        'ju-gultig': 102.0,
        'ju-ja': 105.0,
        'ju-japroz': 10.8,
        'ju-nein': 107.0,
        'ju-stimmen': 103.0,
        'lu-annahme': 0.0,
        'lu-berecht': 101.0,
        'lu-bet': 10.4,
        'lu-gultig': 102.0,
        'lu-ja': 105.0,
        'lu-japroz': 10.8,
        'lu-nein': 107.0,
        'lu-stimmen': 103.0,
        'ne-annahme': 0.0,
        'ne-berecht': 101.0,
        'ne-bet': 10.4,
        'ne-gultig': 102.0,
        'ne-ja': 105.0,
        'ne-japroz': 10.8,
        'ne-nein': 107.0,
        'ne-stimmen': 103.0,
        'nw-annahme': 0.0,
        'nw-berecht': 101.0,
        'nw-bet': 10.4,
        'nw-gultig': 102.0,
        'nw-ja': 105.0,
        'nw-japroz': 10.8,
        'nw-nein': 107.0,
        'nw-stimmen': 103.0,
        'ow-annahme': 0.0,
        'ow-berecht': 101.0,
        'ow-bet': 10.4,
        'ow-gultig': 102.0,
        'ow-ja': 105.0,
        'ow-japroz': 10.8,
        'ow-nein': 107.0,
        'ow-stimmen': 103.0,
        'sg-annahme': 0.0,
        'sg-berecht': 101.0,
        'sg-bet': 10.4,
        'sg-gultig': 102.0,
        'sg-ja': 105.0,
        'sg-japroz': 10.8,
        'sg-nein': 107.0,
        'sg-stimmen': 103.0,
        'sh-annahme': 0.0,
        'sh-berecht': 101.0,
        'sh-bet': 10.4,
        'sh-gultig': 102.0,
        'sh-ja': 105.0,
        'sh-japroz': 10.8,
        'sh-nein': 107.0,
        'sh-stimmen': 103.0,
        'so-annahme': 0.0,
        'so-berecht': 101.0,
        'so-bet': 10.4,
        'so-gultig': 102.0,
        'so-ja': 105.0,
        'so-japroz': 10.8,
        'so-nein': 107.0,
        'so-stimmen': 103.0,
        'sz-annahme': 0.0,
        'sz-berecht': 101.0,
        'sz-bet': 10.4,
        'sz-gultig': 102.0,
        'sz-ja': 105.0,
        'sz-japroz': 10.8,
        'sz-nein': 107.0,
        'sz-stimmen': 103.0,
        'tg-annahme': 0.0,
        'tg-berecht': 101.0,
        'tg-bet': 10.4,
        'tg-gultig': 102.0,
        'tg-ja': 105.0,
        'tg-japroz': 10.8,
        'tg-nein': 107.0,
        'tg-stimmen': 103.0,
        'ti-annahme': 0.0,
        'ti-berecht': 101.0,
        'ti-bet': 10.4,
        'ti-gultig': 102.0,
        'ti-ja': 105.0,
        'ti-japroz': 10.8,
        'ti-nein': 107.0,
        'ti-stimmen': 103.0,
        'ur-annahme': 0.0,
        'ur-berecht': 101.0,
        'ur-bet': 10.4,
        'ur-gultig': 102.0,
        'ur-ja': 105.0,
        'ur-japroz': 10.8,
        'ur-nein': 107.0,
        'ur-stimmen': 103.0,
        'vd-annahme': 0.0,
        'vd-berecht': 101.0,
        'vd-bet': 10.4,
        'vd-gultig': 102.0,
        'vd-ja': 105.0,
        'vd-japroz': 10.8,
        'vd-nein': 107.0,
        'vd-stimmen': 103.0,
        'vs-annahme': 0.0,
        'vs-berecht': 101.0,
        'vs-bet': 10.4,
        'vs-gultig': 102.0,
        'vs-ja': 105.0,
        'vs-japroz': 10.8,
        'vs-nein': 107.0,
        'vs-stimmen': 103.0,
        'zg-annahme': 0.0,
        'zg-berecht': 101.0,
        'zg-bet': 10.4,
        'zg-gultig': 102.0,
        'zg-ja': 105.0,
        'zg-japroz': 10.8,
        'zg-nein': 107.0,
        'zg-stimmen': 103.0,
        'zh-annahme': 0.0,
        'zh-berecht': 101.0,
        'zh-bet': 10.4,
        'zh-gultig': 102.0,
        'zh-ja': 105.0,
        'zh-japroz': 10.8,
        'zh-nein': 107.0,
        'zh-stimmen': 103.0,
        'dep': 1.0,
        'gesch_nr': 24.557,
        'br-pos': 1.0,
        'bv-pos': 1.0,
        'nr-pos': 1.0,
        'nrja': 10.0,
        'nrnein': 20.0,
        'sr-pos': 1.0,
        'srja': 30.0,
        'srnein': 40.0,
        'dauer_bv': 30.0,
        'dauer_abst': 31.0,
        'i-dauer_samm': 32.0,
        'i-dauer_br': 33.0,
        'i-dauer_tot': 34.0,
        'fr-dauer_samm': 35.0,
        'fr-dauer_tot': 36.0,
        'unter_g': 40.0,
        'unter_u': 41.0,
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
        'p-bdp': '',
        'p-mcg': 9999.0,
        'p-sav': 1.0,
        'p-eco': 2.0,
        'p-sgv': 3.0,
        'p-sbv': 3.0,
        'p-sgb': 3.0,
        'p-travs': 3.0,
        'p-vsa': 9999.0,
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
        'p-others_yes': 'Pro Velo',
        'p-others_no': 'Biosuisse',
        'p-others_free': 'Pro Natura, Greenpeace',
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
        'w-ubrige': 21.2,
        'ja-lager': 22.2,
        'nein-lager': 23.2,
        'keinepar-summe': 25.2,
        'leer-summe': 26.2,
        'freigabe-summe': 27.2,
        'neutral-summe': 24.2,
        'unbekannt-summe': 28.2,
        'urheber': 'Initiator',
        'anneepolitique': 'anneepolitique',
        'bfsmap-de': 'map de',
        'bfsmap-fr': 'map fr'
    }

    assert csv.keys() == xlsx.keys()
