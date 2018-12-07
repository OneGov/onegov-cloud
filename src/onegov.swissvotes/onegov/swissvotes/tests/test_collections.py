from datetime import date
from decimal import Decimal
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.collections import TranslatablePageCollection
from psycopg2.extras import NumericRange
from pytest import skip


def test_pages(session):
    pages = TranslatablePageCollection(session)
    page = pages.add(
        id='about',
        title_translations={'en': "About", 'de': "Über"},
        content_translations={'en': "Placeholder", 'de': "Platzhalter"}
    )

    assert page.id == 'about'
    assert page.title_translations == {'en': "About", 'de': "Über"}
    assert page.content_translations == {
        'en': "Placeholder", 'de': "Platzhalter"
    }


def test_votes(session):
    votes = SwissVoteCollection(session)
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
    # todo: current_sort_by
    # todo: current_sort_order
    # todo: sort_order_by_key
    # todo: by_order
    # todo: order_by
    pass


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
    # todo: update
    pass


def test_votes_export(session):
    # todo: export_csv
    # todo: export_xlsx
    pass
