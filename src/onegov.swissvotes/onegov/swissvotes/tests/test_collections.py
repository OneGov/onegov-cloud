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


def test_votes(session):
    votes = SwissVoteCollection(session)
    assert votes.last_modified is None

    with freeze_time(datetime(2019, 1, 1, 10, tzinfo=utc)):
        vote = votes.add(
            id=1,
            bfs_number=Decimal('100.1'),
            date=date(1990, 6, 2),
            decade=NumericRange(1990, 1999),
            legislation_number=4,
            legislation_decade=NumericRange(1990, 1994),
            title="Vote",
            votes_on_same_day=2,
            _legal_form=1
        )

    assert vote.id == 1
    assert vote.bfs_number == Decimal('100.1')
    assert vote.date == date(1990, 6, 2)
    assert vote.decade == NumericRange(1990, 1999)
    assert vote.legislation_number == 4
    assert vote.legislation_decade == NumericRange(1990, 1994)
    assert vote.title == "Vote"
    assert vote.votes_on_same_day == 2
    assert vote.legal_form == "Mandatory referendum"

    assert votes.last_modified == datetime(2019, 1, 1, 10, tzinfo=utc)
    assert votes.by_bfs_number('100.1') == vote
    assert votes.by_bfs_number(Decimal('100.1')) == vote


def test_votes_default():
    votes = SwissVoteCollection(
        session=1,
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
    assert votes.session == 1
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
    assert votes.session == 1
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


def test_votes_pagination(session):
    votes = SwissVoteCollection(session)

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
            title="Vote",
            votes_on_same_day=2,
            _legal_form=1
        )

    votes = SwissVoteCollection(session)
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


def test_vote_term_filter():
    assert SwissVoteCollection(None).term_filter == []
    assert SwissVoteCollection(None, term='').term_filter == []
    assert SwissVoteCollection(None, term='', full_text=True).term_filter == []

    def compiled(list_):
        return [
            str(statement.compile(compile_kwargs={"literal_binds": True}))
            for statement in list_
        ]

    assert compiled(
        SwissVoteCollection(None, term='100').term_filter
    ) == [
        'swissvotes.bfs_number = 100',
        'swissvotes.procedure_number = 100',
        """to_tsvector('german', swissvotes.title) MATCH '100'""",
        """to_tsvector('german', swissvotes.keyword) MATCH '100'""",
    ]

    assert compiled(
        SwissVoteCollection(None, term='100.1').term_filter
    ) == [
        'swissvotes.bfs_number = 100.1',
        'swissvotes.procedure_number = 100.1',
        """to_tsvector('german', swissvotes.title) MATCH '100.1'""",
        """to_tsvector('german', swissvotes.keyword) MATCH '100.1'""",
    ]

    assert compiled(
        SwissVoteCollection(None, term='abc').term_filter
    ) == [
        """to_tsvector('german', swissvotes.title) MATCH 'abc'""",
        """to_tsvector('german', swissvotes.keyword) MATCH 'abc'""",
    ]
    assert compiled(
        SwissVoteCollection(None, term='abc', full_text=True).term_filter
    ) == [
        """to_tsvector('german', swissvotes.title) MATCH 'abc'""",
        """to_tsvector('german', swissvotes.keyword) MATCH 'abc'""",
        """to_tsvector('german', swissvotes.initiator) MATCH 'abc'""",
        """swissvotes."searchable_text_de_CH" MATCH 'abc'""",
        """swissvotes."searchable_text_fr_CH" MATCH 'abc'""",
    ]

    assert compiled(
        SwissVoteCollection(None, term='Müller').term_filter
    ) == [
        "to_tsvector('german', swissvotes.title) MATCH 'Müller'",
        "to_tsvector('german', swissvotes.keyword) MATCH 'Müller'",
    ]

    assert compiled(
        SwissVoteCollection(None, term='20,20').term_filter
    ) == [
        "to_tsvector('german', swissvotes.title) MATCH '20,20'",
        "to_tsvector('german', swissvotes.keyword) MATCH '20,20'",
    ]

    assert compiled(
        SwissVoteCollection(None, term='Neu!').term_filter
    ) == [
        "to_tsvector('german', swissvotes.title) MATCH 'Neu'",
        "to_tsvector('german', swissvotes.keyword) MATCH 'Neu'",
    ]

    assert compiled(
        SwissVoteCollection(None, term='Hans Peter Müller').term_filter
    ) == [
        "to_tsvector('german', swissvotes.title) MATCH "
        "'Hans <-> Peter <-> Müller'",
        "to_tsvector('german', swissvotes.keyword) MATCH "
        "'Hans <-> Peter <-> Müller'",
    ]

    assert compiled(
        SwissVoteCollection(None, term='x AND y').term_filter
    ) == [
        "to_tsvector('german', swissvotes.title) MATCH 'x <-> AND <-> y'",
        "to_tsvector('german', swissvotes.keyword) MATCH 'x <-> AND <-> y'",
    ]

    assert compiled(
        SwissVoteCollection(None, term='x | y').term_filter
    ) == [
        "to_tsvector('german', swissvotes.title) MATCH 'x <-> y'",
        "to_tsvector('german', swissvotes.keyword) MATCH 'x <-> y'",
    ]

    assert compiled(
        SwissVoteCollection(None, term='y ! y').term_filter
    ) == [
        "to_tsvector('german', swissvotes.title) MATCH 'y <-> y'",
        "to_tsvector('german', swissvotes.keyword) MATCH 'y <-> y'",
    ]


def test_votes_query(session):
    votes = SwissVoteCollection(session)
    votes.add(
        id=1,
        bfs_number=Decimal('100'),
        date=date(1990, 6, 2),
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title="Vote on that one thing",
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
        title="We want this version the thing",
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
        title="We want that version of the thing",
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
        return SwissVoteCollection(session, **kwargs).query().count()

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

    assert count(term='thing') == 3
    assert count(term='that one thing') == 1
    assert count(term='version') == 2
    assert count(term='variant') == 2
    assert count(term='riant') == 0
    assert count(term='A of X') == 1
    assert count(term='group') == 0
    assert count(term='group', full_text=True) == 1
    assert count(term='The group that wants something', full_text=True) == 1


def test_votes_query_attachments(session, attachments, postgres_version):
    if int(postgres_version.split('.')[0]) < 10:
        skip("PostgreSQL 10+")

    votes = SwissVoteCollection(session)
    votes.add(
        id=1,
        bfs_number=Decimal('100'),
        date=date(1990, 6, 2),
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title="Vote on that one thing",
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
        title="We want this version the thing",
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
        title="We want that version of the thing",
        votes_on_same_day=1,
        _legal_form=2,
    )
    for name, attachment in attachments.items():
        setattr(vote, name, attachment)
        session.flush()

    def count(**kwargs):
        return SwissVoteCollection(session, **kwargs).query().count()

    assert count() == 3

    assert count(term='Abstimmungstext') == 0
    assert count(term='Abstimmungstext', full_text=True) == 1
    assert count(term='council message', full_text=True) == 1
    assert count(term='Parlamentdebatte', full_text=True) == 1
    assert count(term='Réalisation', full_text=True) == 1
    assert count(term='booklet', full_text=True) == 0


def test_votes_order(session):
    votes = SwissVoteCollection(session)

    for index, title in enumerate(('First', 'Śecond', 'Third'), start=1):
        votes.add(
            id=index,
            bfs_number=Decimal(str(index)),
            date=date(1990, 6, index),
            decade=NumericRange(1990, 1999),
            legislation_number=1,
            legislation_decade=NumericRange(1990, 1994),
            title=title,
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

    votes = SwissVoteCollection(session, sort_by='', sort_order='')
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'

    votes = SwissVoteCollection(session, sort_by='xx', sort_order='yy')
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'

    votes = SwissVoteCollection(session, sort_by='date', sort_order='yy')
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'

    votes = SwissVoteCollection(session, sort_by='xx', sort_order='ascending')
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'

    votes = SwissVoteCollection(session, sort_by='result', sort_order='yy')
    assert votes.current_sort_by == 'result'
    assert votes.current_sort_order == 'ascending'

    votes = SwissVoteCollection(session)
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

    votes = votes.by_order(None)
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'

    votes = votes.by_order('')
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'

    votes = votes.by_order('xxx')
    assert votes.current_sort_by == 'date'
    assert votes.current_sort_order == 'descending'


def test_votes_available_descriptors(session):
    votes = SwissVoteCollection(session)
    assert votes.available_descriptors == [set(), set(), set()]

    votes.add(
        id=1,
        bfs_number=Decimal('1'),
        date=date(1990, 6, 2),
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title="Vote",
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
        title="Vote",
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
        title="Vote",
        votes_on_same_day=2,
        _legal_form=1,
        descriptor_3_level_1=Decimal('8'),
        descriptor_3_level_2=Decimal('8.3'),
    )

    assert SwissVoteCollection(session).available_descriptors == [
        {Decimal('1.00'), Decimal('4.00'), Decimal('8.00'), Decimal('10.00')},
        {Decimal('1.60'), Decimal('4.20'), Decimal('8.30'), Decimal('10.30')},
        {Decimal('1.62'), Decimal('4.21'), Decimal('10.33'), Decimal('10.35')}
    ]


def test_votes_update(session):
    votes = SwissVoteCollection(session)

    added, updated = votes.update([
        SwissVote(
            bfs_number=Decimal('1'),
            date=date(1990, 6, 1),
            decade=NumericRange(1990, 1999),
            legislation_number=1,
            legislation_decade=NumericRange(1990, 1994),
            title="First",
            votes_on_same_day=2,
            _legal_form=1,
        ),
        SwissVote(
            bfs_number=Decimal('2'),
            date=date(1990, 6, 1),
            decade=NumericRange(1990, 1999),
            legislation_number=2,
            legislation_decade=NumericRange(1990, 1994),
            title="Second",
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
            title="First",
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
            title="First vote",
            votes_on_same_day=2,
            _legal_form=1,
        )
    ])
    assert added == 0
    assert updated == 1
    assert votes.by_bfs_number(Decimal('1')).title == 'First vote'


def test_votes_export(session):
    votes = SwissVoteCollection(session)
    vote = votes.add(
        bfs_number=Decimal('100.1'),
        date=date(1990, 6, 2),
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title="Vote",
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
    vote._recommendation_fdp = 1
    vote._recommendation_cvp = 1
    vote._recommendation_sps = 1
    vote._recommendation_svp = 1
    vote._recommendation_lps = 2
    vote._recommendation_ldu = 2
    vote._recommendation_evp = 2
    vote._recommendation_csp = 3
    vote._recommendation_pda = 3
    vote._recommendation_poch = 3
    vote._recommendation_gps = 4
    vote._recommendation_sd = 4
    vote._recommendation_rep = 4
    vote._recommendation_edu = 5
    vote._recommendation_fps = 5
    vote._recommendation_lega = 5
    vote._recommendation_kvp = 66
    vote._recommendation_glp = 66
    vote._recommendation_bdp = None
    vote._recommendation_mcg = 9999
    vote._recommendation_sav = 1
    vote._recommendation_eco = 2
    vote._recommendation_sgv = 3
    vote._recommendation_sbv_usp = 3
    vote._recommendation_sgb = 3
    vote._recommendation_travs = 3
    vote._recommendation_vsa = 9999
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
    vote.national_council_share_vague = Decimal('25.10')
    session.flush()
    session.expire_all()

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
        'titel': 'Vote',
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
        'zsa': '1',
        'eco': '2',
        'sgv': '3',
        'sbv': '3',
        'sgb': '3',
        'cng-travs': '3',
        'vsa': '9999',
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
        'neutral': '24,2',
        'unbestimmt': '25,1',
        'urheber': 'Initiator',
        'anneepolitique': 'anneepolitique'
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
        'titel': 'Vote',
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
        'zsa': 1.0,
        'eco': 2.0,
        'sgv': 3.0,
        'sbv': 3.0,
        'sgb': 3.0,
        'cng-travs': 3.0,
        'vsa': 9999.0,
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
        'neutral': 24.2,
        'unbestimmt': 25.1,
        'urheber': 'Initiator',
        'anneepolitique': 'anneepolitique',
    }

    assert csv.keys() == xlsx.keys()
