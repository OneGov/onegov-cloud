from __future__ import annotations

import datetime
from datetime import timedelta
from freezegun import freeze_time
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.collections import PaginatedAgencyCollection
from onegov.agency.collections import PaginatedMembershipCollection
from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedPerson
from sedate import utcnow
from string import ascii_uppercase


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_extended_agencies(session: Session) -> None:
    agencies = ExtendedAgencyCollection(session)
    root = agencies.add_root(title="Agency")
    assert isinstance(root, ExtendedAgency)
    assert isinstance(agencies.query().one(), ExtendedAgency)


def test_extended_agencies_filter_title(session: Session) -> None:
    agency_titles = [
        'Amt für Jagd und Fischerei',
        'Amt für Umwelt und Energie',
        'Amt für Verkehr und Infrastruktur',
    ]

    agencies_ = ExtendedAgencyCollection(session)
    for title in agency_titles:
        agencies_.add_root(title=title)

    agencies = PaginatedAgencyCollection(session)
    agencies = agencies.for_filter(title='Amt')
    assert [a.title for a in agencies.query()] == agency_titles
    agencies = agencies.for_filter(title='Jagd')
    assert [a.title for a in agencies.query()] == [agency_titles[0]]
    agencies = agencies.for_filter(title='umwelt')
    assert [a.title for a in agencies.query()] == [agency_titles[1]]
    agencies = agencies.for_filter(title='energie verkehr')
    assert [a.title for a in agencies.query()] == [agency_titles[1],
                                                   agency_titles[2]]


def test_extended_agencies_filter_gt(session: Session) -> None:
    agencies_ = ExtendedAgencyCollection(session)

    with freeze_time('2023-05-08 09:00'):
        agencies_.add_root(title='Büro früh')
    with freeze_time('2023-05-08 10:00'):
        agencies_.add_root(title='Büro spät')

        agencies = PaginatedAgencyCollection(session)
        agencies = agencies.for_filter(updated_gt=datetime.datetime(
            2023, 5, 8, 8, 59, 0)
        )
        assert [a.title for a in agencies.query()] == [
            'Büro früh', 'Büro spät']

        agencies = agencies.for_filter(updated_gt=datetime.datetime(
            2023, 5, 8, 9, 59, 0)
        )
        assert [a.title for a in agencies.query()] == ['Büro spät']

        agencies = agencies.for_filter(updated_gt=datetime.datetime(
            2023, 5, 8, 10, 0, 0)
        )
        assert [a.title for a in agencies.query()] == list()


def test_extended_agencies_filter_ge(session: Session) -> None:
    agencies_ = ExtendedAgencyCollection(session)

    with freeze_time('2023-05-08 09:00'):
        agencies_.add_root(title='Büro früh')
    with freeze_time('2023-05-08 10:00'):
        agencies_.add_root(title='Büro spät')

    agencies = PaginatedAgencyCollection(session)
    agencies = agencies.for_filter(updated_ge=datetime.datetime(
        2023, 5, 8, 9, 0, 0)
    )
    assert [a.title for a in agencies.query()] == ['Büro früh', 'Büro spät']

    agencies = agencies.for_filter(updated_ge=datetime.datetime(
        2023, 5, 8, 10, 0, 0)
    )
    assert [a.title for a in agencies.query()] == ['Büro spät']

    agencies = agencies.for_filter(updated_ge=datetime.datetime(
        2023, 5, 8, 10, 1, 0)
    )
    assert [a.title for a in agencies.query()] == list()


def test_extended_agencies_filter_eq(session: Session) -> None:
    agencies_ = ExtendedAgencyCollection(session)

    with freeze_time('2023-05-08 09:00'):
        agencies_.add_root(title='Büro früh')
    with freeze_time('2023-05-08 10:00'):
        agencies_.add_root(title='Büro spät')

    agencies = PaginatedAgencyCollection(session)
    agencies = agencies.for_filter(updated_eq=datetime.datetime(
        2023, 5, 8, 9, 0, 0)
    )
    assert [a.title for a in agencies.query()] == ['Büro früh']

    agencies = agencies.for_filter(updated_eq=datetime.datetime(
        2023, 5, 8, 10, 0, 0)
    )
    assert [a.title for a in agencies.query()] == ['Büro spät']

    agencies = agencies.for_filter(updated_eq=datetime.datetime(
        2023, 5, 8, 10, 1, 0)
    )
    assert [a.title for a in agencies.query()] == list()


def test_extended_agencies_filter_le(session: Session) -> None:
    agencies_ = ExtendedAgencyCollection(session)

    with freeze_time('2023-05-08 09:00'):
        agencies_.add_root(title='Büro früh')
    with freeze_time('2023-05-08 10:00'):
        agencies_.add_root(title='Büro spät')

    agencies = PaginatedAgencyCollection(session)
    agencies = agencies.for_filter(updated_le=datetime.datetime(
        2023, 5, 8, 8, 59, 0)
    )
    assert [a.title for a in agencies.query()] == list()

    agencies = agencies.for_filter(updated_le=datetime.datetime(
        2023, 5, 8, 9, 0, 0)
    )
    assert [a.title for a in agencies.query()] == ['Büro früh']

    agencies = agencies.for_filter(updated_le=datetime.datetime(
        2023, 5, 8, 10, 0, 0)
    )
    assert [a.title for a in agencies.query()] == ['Büro früh', 'Büro spät']


def test_extended_agencies_filter_lt(session: Session) -> None:
    agencies_ = ExtendedAgencyCollection(session)

    with freeze_time('2023-05-08 09:00'):
        agencies_.add_root(title='Büro früh')
    with freeze_time('2023-05-08 10:00'):
        agencies_.add_root(title='Büro spät')

    agencies = PaginatedAgencyCollection(session)
    agencies = agencies.for_filter(updated_lt=datetime.datetime(
        2023, 5, 8, 9, 0, 0)
    )
    assert [a.title for a in agencies.query()] == list()

    agencies = agencies.for_filter(updated_lt=datetime.datetime(
        2023, 5, 8, 9, 1, 0)
    )
    assert [a.title for a in agencies.query()] == ['Büro früh']

    agencies = agencies.for_filter(updated_lt=datetime.datetime(
        2023, 5, 8, 10, 1, 0)
    )
    assert [a.title for a in agencies.query()] == ['Büro früh', 'Büro spät']


def test_extended_people(session: Session) -> None:
    people = ExtendedPersonCollection(session)
    person = people.add(first_name="Hans", last_name="Maulwurf")
    assert isinstance(person, ExtendedPerson)
    assert isinstance(people.query().one(), ExtendedPerson)


def test_extended_people_pagination(session: Session) -> None:
    people = ExtendedPersonCollection(session)

    assert people.pages_count == 0
    assert people.batch == ()

    for letter in ascii_uppercase:
        people.add(first_name=letter.lower(), last_name=letter)

    assert people.query().count() == 26

    people = ExtendedPersonCollection(session)
    assert people.subset_count == 26
    assert people.pages_count == 2
    assert len(people.batch) == 20
    assert people.next is not None
    assert len(people.next.batch) == 6
    assert len(people.page_by_index(1).batch) == 6


def test_extended_people_filter_first_last_name(session: Session) -> None:
    people = ExtendedPersonCollection(session)
    people.add(first_name="Hans", last_name="Maulwurf")
    people.add(first_name="Waylon", last_name="Śmithers")
    people.add(first_name="Lenny", last_name="leonard")
    people.add(first_name="Carl", last_name="Çarlson")
    people.add(first_name="Ned", last_name="Flanders")
    people.add(first_name="Anna", last_name="Quinn")
    people.add(first_name="Anna", last_name="Bourqui")

    assert [p.last_name for p in people.query()] == [
        "Bourqui", "Çarlson", "Flanders", "leonard",
        "Maulwurf", "Quinn", "Śmithers"
    ]

    # first character of last name
    people = people.for_filter(letter="C")
    assert [p.last_name for p in people.query()] == ['Çarlson']

    people = people.for_filter(letter="c")
    assert [p.last_name for p in people.query()] == ['Çarlson']

    people = people.for_filter(letter="L")
    assert [p.last_name for p in people.query()] == ['leonard']

    people = people.for_filter(agency="Police")
    assert [p.last_name for p in people.query()] == []

    people = people.for_filter(letter=None)
    assert [p.last_name for p in people.query()] == []

    # first name
    people = ExtendedPersonCollection(session)
    people = people.for_filter(first_name='Max')
    assert [p.first_name for p in people.query()] == []

    people = people.for_filter(first_name='anna')
    assert [(p.first_name, p.last_name) for p in people.query()] == [
        ('Anna', 'Bourqui'), ('Anna', 'Quinn')]

    # last name
    people = ExtendedPersonCollection(session)
    people = people.for_filter(last_name='Flan')
    assert [p.first_name for p in people.query()] == []

    people = people.for_filter(last_name='Flanders')
    assert [p.last_name for p in people.query()] == ['Flanders']

    # first and lastname
    people = ExtendedPersonCollection(session)
    people = people.for_filter(first_name='anna', last_name='Quinn')
    assert [(p.first_name, p.last_name) for p in people.query()] == [
        ('Anna', 'Quinn')]


def test_extended_people_filter_updated_gt(session: Session) -> None:
    people = ExtendedPersonCollection(session)

    with freeze_time('2023-05-08 01:00'):
        people.add(first_name="Hans", last_name="Maulwurf")
    with freeze_time('2023-05-08 01:05'):
        people.add(first_name="Franz", last_name="Müller")

    people = people.for_filter(updated_gt=datetime.datetime(
        2023, 5, 8, 0, 59, 0)
    )
    assert [p.last_name for p in people.query()] == ['Maulwurf', 'Müller']

    people = people.for_filter(updated_gt=datetime.datetime(
        2023, 5, 8, 1, 1, 0)
    )
    assert [p.last_name for p in people.query()] == ['Müller']

    people = people.for_filter(updated_gt=datetime.datetime(
        2023, 5, 8, 1, 6, 0)
    )
    assert [p.last_name for p in people.query()] == []


def test_extended_people_filter_updated_ge(session: Session) -> None:
    people = ExtendedPersonCollection(session)

    with freeze_time('2023-05-08 01:00'):
        people.add(first_name="Hans", last_name="Maulwurf")
    with freeze_time('2023-05-08 01:05'):
        people.add(first_name="Franz", last_name="Müller")

    people = people.for_filter(updated_ge=datetime.datetime(
        2023, 5, 8, 1, 0, 0)
    )
    assert [p.last_name for p in people.query()] == ['Maulwurf', 'Müller']

    people = people.for_filter(updated_ge=datetime.datetime(
        2023, 5, 8, 1, 5, 0)
    )
    assert [p.last_name for p in people.query()] == ['Müller']

    people = people.for_filter(updated_ge=datetime.datetime(
        2023, 5, 8, 1, 6, 0)
    )
    assert [p.last_name for p in people.query()] == []


def test_extended_people_filter_updated_eq(session: Session) -> None:
    people = ExtendedPersonCollection(session)

    with freeze_time('2023-05-08 01:00'):
        people.add(first_name="Hans", last_name="Maulwurf")
    with freeze_time('2023-05-08 01:05'):
        people.add(first_name="Franz", last_name="Müller")

    people = people.for_filter(updated_eq=datetime.datetime(
        2023, 5, 8, 0, 59, 0)
    )
    assert [p.last_name for p in people.query()] == []

    people = people.for_filter(updated_eq=datetime.datetime(
        2023, 5, 8, 1, 0, 0)
    )
    assert [p.last_name for p in people.query()] == ['Maulwurf']

    people = people.for_filter(updated_eq=datetime.datetime(
        2023, 5, 8, 1, 5, 0)
    )
    assert [p.last_name for p in people.query()] == ['Müller']

    people = people.for_filter(updated_eq=datetime.datetime(
        2023, 5, 8, 1, 6, 0)
    )
    assert [p.last_name for p in people.query()] == []


def test_extended_people_filter_updated_le(session: Session) -> None:
    people = ExtendedPersonCollection(session)

    with freeze_time('2023-05-08 01:00'):
        people.add(first_name="Hans", last_name="Maulwurf")
    with freeze_time('2023-05-08 01:05'):
        people.add(first_name="Franz", last_name="Müller")

    people = people.for_filter(updated_le=datetime.datetime(
        2023, 5, 8, 0, 59, 0)
    )
    assert [p.last_name for p in people.query()] == []

    people = people.for_filter(updated_le=datetime.datetime(
        2023, 5, 8, 1, 0, 0)
    )
    assert [p.last_name for p in people.query()] == ['Maulwurf']

    people = people.for_filter(updated_le=datetime.datetime(
        2023, 5, 8, 1, 5, 0)
    )
    assert [p.last_name for p in people.query()] == ['Maulwurf', 'Müller']


def test_extended_people_filter_updated_lt(session: Session) -> None:
    people = ExtendedPersonCollection(session)

    with freeze_time('2023-05-08 01:00'):
        people.add(first_name="Hans", last_name="Maulwurf")
    with freeze_time('2023-05-08 01:05'):
        people.add(first_name="Franz", last_name="Müller")

    people = people.for_filter(updated_lt=datetime.datetime(
        2023, 5, 8, 1, 0, 0)
    )
    assert [p.last_name for p in people.query()] == []

    people = people.for_filter(updated_lt=datetime.datetime(
        2023, 5, 8, 1, 1, 0)
    )
    assert [p.last_name for p in people.query()] == ['Maulwurf']

    people = people.for_filter(updated_lt=datetime.datetime(
        2023, 5, 8, 1, 6, 0)
    )
    assert [p.last_name for p in people.query()] == ['Maulwurf', 'Müller']


def test_extended_people_filter_updated_multiple(session: Session) -> None:
    people = ExtendedPersonCollection(session)

    with freeze_time('2023-05-08 01:00'):
        people.add(first_name="Hans", last_name="Maulwurf")
    with freeze_time('2023-05-08 01:05'):
        people.add(first_name="Franz", last_name="Müller")

    people = people.for_filter(
        updated_ge=datetime.datetime(2023, 5, 8, 1, 0, 0),
        updated_le=datetime.datetime(2023, 5, 8, 1, 5, 0),
    )
    assert [p.last_name for p in people.query()] == ['Maulwurf', 'Müller']

    people = people.for_filter(
        updated_lt=datetime.datetime(2023, 5, 8, 1, 6, 0),
        updated_gt=datetime.datetime(2023, 5, 8, 0, 59, 0)
    )
    assert [p.last_name for p in people.query()] == ['Maulwurf', 'Müller']

    people = people.for_filter(
        updated_eq=datetime.datetime(2023, 5, 8, 1, 0, 0),
        first_name='Hans'
    )
    assert [p.last_name for p in people.query()] == ['Maulwurf']


def test_extended_people_used_letters(session: Session) -> None:
    assert ExtendedPersonCollection(session).used_letters == []

    people = ExtendedPersonCollection(session)
    people.add(first_name="Hans", last_name="Maulwurf")
    people.add(first_name="Waylon", last_name="Śmithers")
    people.add(first_name="Lenny", last_name="leonard")
    people.add(first_name="Carl", last_name="Çarlson")
    people.add(first_name="Ned", last_name="Flanders")

    assert people.used_letters == ['C', 'F', 'L', 'M', 'S']


def test_extended_people_used_agencies(session: Session) -> None:
    assert ExtendedPersonCollection(session).used_agencies == []

    agencies = ExtendedAgencyCollection(session)
    police = agencies.add_root(title="Police")
    hospital = agencies.add_root(title="Ħospital")
    agencies.add_root(title="Moe's Tavern")

    assert ExtendedPersonCollection(session).used_agencies == []

    people = ExtendedPersonCollection(session)
    ned = people.add(first_name="Ned", last_name="Flanders")
    police.add_person(ned.id, "Snitch")
    hospital.add_person(ned.id, "Volunteer")

    assert people.used_agencies == ['Ħospital', 'Police']


def test_extended_people_exclude_hidden(session: Session) -> None:
    people = ExtendedPersonCollection(session)
    assert people.exclude_hidden is False

    person = people.add(first_name="Hans", last_name="Maulwurf")
    assert people.query().count() == 1

    people.exclude_hidden = True
    assert people.query().count() == 1

    person.access = 'private'
    assert people.query().count() == 0

    person.access = 'public'
    assert people.query().count() == 1

    person.publication_start = utcnow() + timedelta(days=7)
    assert people.query().count() == 0

    person.publication_start = None
    person.publication_end = utcnow() - timedelta(days=7)
    assert people.query().count() == 0


def test_paginated_agencies(session: Session) -> None:
    collection = PaginatedAgencyCollection(session)
    assert collection.batch == ()
    assert collection.pages_count == 0
    assert collection.next is None
    assert collection.previous is None

    for number in '012345678':
        parent = collection.add(parent=None, name=number, title=number)
        for letter in 'abcdef':
            name = f'{number}-{letter}'
            child = collection.add(parent=parent, name=name, title=name)

    parent.meta['access'] = 'private'
    child.publication_start = utcnow() + timedelta(days=7)

    collection = PaginatedAgencyCollection(session)
    assert collection.subset_count == 61
    assert collection.pages_count == 7
    assert len(collection.batch) == 10
    assert collection.query().count() == 61
    assert collection.next is not None
    assert collection.next.next is not None
    assert len(collection.next.next.batch) == 10
    assert collection.next.previous == collection
    assert len(collection.page_by_index(6).batch) == 1

    collection = PaginatedAgencyCollection(
        session, joinedload=['organigram'], undefer=['content']
    )
    assert collection.subset_count == 61

    def count(**kwargs: Any) -> int:
        return PaginatedAgencyCollection(session, **kwargs).subset_count

    assert count(exclude_hidden=False) == 63
    assert count(parent=parent.id) == 5
    assert count(parent=parent.id, exclude_hidden=False) == 6
    assert count(parent=False) == 8
    assert count(parent=False, exclude_hidden=False) == 9


def test_paginated_memberships(session: Session) -> None:
    agencies = ExtendedAgencyCollection(session)
    a = agencies.add_root(title="A")
    b = agencies.add_root(title="B")
    c = agencies.add_root(title="C")
    d = agencies.add_root(title="D")

    c.meta['access'] = 'private'
    d.publication_start = utcnow() + timedelta(days=7)

    people = ExtendedPersonCollection(session)
    v = people.add(first_name="V", last_name="V")
    w = people.add(first_name="W", last_name="W")
    x = people.add(first_name="X", last_name="X")
    y = people.add(first_name="Y", last_name="Y")
    z = people.add(first_name="z", last_name="z")

    v.meta['access'] = 'private'
    w.publication_start = utcnow() + timedelta(days=7)

    for number in '012345678':
        a.add_person(v.id, number)
        a.add_person(w.id, number)
        a.add_person(x.id, number)
        a.add_person(y.id, number)
        n = a.add_person(z.id, number)
        m = b.add_person(x.id, number)
        c.add_person(x.id, number)
        d.add_person(y.id, number)

    n.meta['access'] = 'private'
    m.publication_start = utcnow() + timedelta(days=7)

    collection = PaginatedMembershipCollection(session)
    assert collection.subset_count == 34
    assert collection.pages_count == 4
    assert len(collection.batch) == 10
    assert collection.query().count() == 34
    assert collection.next is not None
    assert collection.next.next is not None
    assert len(collection.next.next.batch) == 10
    assert collection.next.previous == collection
    assert len(collection.page_by_index(3).batch) == 4

    def count(**kwargs: Any) -> int:
        return PaginatedMembershipCollection(session, **kwargs).subset_count

    assert count(exclude_hidden=False) == 72

    assert count(agency=a.id) == 26
    assert count(agency=b.id) == 8
    assert count(agency=c.id) == 0
    assert count(agency=d.id) == 0

    assert count(agency=a.id, exclude_hidden=False) == 45
    assert count(agency=b.id, exclude_hidden=False) == 9
    assert count(agency=c.id, exclude_hidden=False) == 9
    assert count(agency=d.id, exclude_hidden=False) == 9

    assert count(person=v.id) == 0
    assert count(person=w.id) == 0
    assert count(person=x.id) == 17
    assert count(person=y.id) == 9
    assert count(person=z.id) == 8

    assert count(person=v.id, exclude_hidden=False) == 9
    assert count(person=w.id, exclude_hidden=False) == 9
    assert count(person=x.id, exclude_hidden=False) == 27
    assert count(person=y.id, exclude_hidden=False) == 18
    assert count(person=z.id, exclude_hidden=False) == 9

    assert count(agency=a.id, person=v.id) == 0
    assert count(agency=b.id, person=v.id) == 0
    assert count(agency=c.id, person=v.id) == 0
    assert count(agency=d.id, person=v.id) == 0
    assert count(agency=a.id, person=w.id) == 0
    assert count(agency=b.id, person=w.id) == 0
    assert count(agency=c.id, person=w.id) == 0
    assert count(agency=d.id, person=w.id) == 0
    assert count(agency=a.id, person=x.id) == 9
    assert count(agency=b.id, person=x.id) == 8
    assert count(agency=c.id, person=x.id) == 0
    assert count(agency=d.id, person=x.id) == 0
    assert count(agency=a.id, person=y.id) == 9
    assert count(agency=b.id, person=y.id) == 0
    assert count(agency=c.id, person=y.id) == 0
    assert count(agency=d.id, person=y.id) == 0
    assert count(agency=a.id, person=z.id) == 8
    assert count(agency=b.id, person=z.id) == 0
    assert count(agency=c.id, person=z.id) == 0
    assert count(agency=d.id, person=z.id) == 0

    assert count(agency=a.id, person=v.id, exclude_hidden=False) == 9
    assert count(agency=b.id, person=v.id, exclude_hidden=False) == 0
    assert count(agency=c.id, person=v.id, exclude_hidden=False) == 0
    assert count(agency=d.id, person=v.id, exclude_hidden=False) == 0
    assert count(agency=a.id, person=w.id, exclude_hidden=False) == 9
    assert count(agency=b.id, person=w.id, exclude_hidden=False) == 0
    assert count(agency=c.id, person=w.id, exclude_hidden=False) == 0
    assert count(agency=d.id, person=w.id, exclude_hidden=False) == 0
    assert count(agency=a.id, person=x.id, exclude_hidden=False) == 9
    assert count(agency=b.id, person=x.id, exclude_hidden=False) == 9
    assert count(agency=c.id, person=x.id, exclude_hidden=False) == 9
    assert count(agency=d.id, person=x.id, exclude_hidden=False) == 0
    assert count(agency=a.id, person=y.id, exclude_hidden=False) == 9
    assert count(agency=b.id, person=y.id, exclude_hidden=False) == 0
    assert count(agency=c.id, person=y.id, exclude_hidden=False) == 0
    assert count(agency=d.id, person=y.id, exclude_hidden=False) == 9
    assert count(agency=a.id, person=z.id, exclude_hidden=False) == 9
    assert count(agency=b.id, person=z.id, exclude_hidden=False) == 0
    assert count(agency=c.id, person=z.id, exclude_hidden=False) == 0
    assert count(agency=d.id, person=z.id, exclude_hidden=False) == 0


def setup_membership_filter_test(session: Session) -> None:
    agencies = ExtendedAgencyCollection(session)
    a = agencies.add_root(title="The Agency")

    people = ExtendedPersonCollection(session)
    p1 = people.add(first_name="Hans", last_name="Maulwurf")
    p2 = people.add(first_name="Franz", last_name="Müller")

    with freeze_time('2023-05-08 01:00'):
        a.add_person(p1.id, 'Hänsu')
    with freeze_time('2023-05-08 01:05'):
        a.add_person(p2.id, 'Fränz')


def test_membership_filters_gt(session: Session) -> None:
    setup_membership_filter_test(session)

    # filter greater than
    memberships = PaginatedMembershipCollection(session)
    memberships = memberships.for_filter(updated_gt=datetime.datetime(
        2023, 5, 8, 0, 59, 0)
    )
    assert [p.title for p in memberships.query()] == ['Hänsu', 'Fränz']

    memberships = memberships.for_filter(updated_gt=datetime.datetime(
        2023, 5, 8, 1, 0, 0)
    )
    assert [p.title for p in memberships.query()] == ['Fränz']

    memberships = memberships.for_filter(updated_gt=datetime.datetime(
        2023, 5, 8, 1, 5, 0)
    )
    assert [p.title for p in memberships.query()] == list()


def test_membership_filters_ge(session: Session) -> None:
    setup_membership_filter_test(session)

    # filter greater equal
    memberships = PaginatedMembershipCollection(session)
    memberships = memberships.for_filter(updated_ge=datetime.datetime(
        2023, 5, 8, 1, 0, 0)
    )
    assert [p.title for p in memberships.query()] == ['Hänsu', 'Fränz']

    memberships = memberships.for_filter(updated_ge=datetime.datetime(
        2023, 5, 8, 1, 5, 0)
    )
    assert [p.title for p in memberships.query()] == ['Fränz']

    memberships = memberships.for_filter(updated_ge=datetime.datetime(
        2023, 5, 8, 1, 6, 0)
    )
    assert [p.title for p in memberships.query()] == list()


def test_membership_filters_eq(session: Session) -> None:
    setup_membership_filter_test(session)

    # filter equal
    memberships = PaginatedMembershipCollection(session)
    memberships = memberships.for_filter(updated_eq=datetime.datetime(
        2023, 5, 8, 0, 0, 0)
    )
    assert [p.title for p in memberships.query()] == list()

    memberships = memberships.for_filter(updated_eq=datetime.datetime(
        2023, 5, 8, 1, 0, 0)
    )
    assert [p.title for p in memberships.query()] == ['Hänsu']

    memberships = memberships.for_filter(updated_eq=datetime.datetime(
        2023, 5, 8, 1, 5, 0)
    )
    assert [p.title for p in memberships.query()] == ['Fränz']


def test_membership_filters_le(session: Session) -> None:
    setup_membership_filter_test(session)

    # filter lower equal
    memberships = PaginatedMembershipCollection(session)
    memberships = memberships.for_filter(updated_le=datetime.datetime(
        2023, 5, 8, 1, 5, 0)
    )
    assert [p.title for p in memberships.query()] == ['Hänsu', 'Fränz']

    memberships = memberships.for_filter(updated_le=datetime.datetime(
        2023, 5, 8, 1, 0, 0)
    )
    assert [p.title for p in memberships.query()] == ['Hänsu']

    memberships = memberships.for_filter(updated_le=datetime.datetime(
        2023, 5, 8, 0, 0, 0)
    )
    assert [p.title for p in memberships.query()] == list()


def test_membership_filters_lt(session: Session) -> None:
    setup_membership_filter_test(session)

    # filter lower than
    memberships = PaginatedMembershipCollection(session)
    memberships = memberships.for_filter(updated_lt=datetime.datetime(
        2023, 5, 8, 1, 6, 0)
    )
    assert [p.title for p in memberships.query()] == ['Hänsu', 'Fränz']

    memberships = memberships.for_filter(updated_lt=datetime.datetime(
        2023, 5, 8, 1, 5, 0)
    )
    assert [p.title for p in memberships.query()] == ['Hänsu']

    memberships = memberships.for_filter(updated_lt=datetime.datetime(
        2023, 5, 8, 0, 0, 0)
    )
    assert [p.title for p in memberships.query()] == list()
