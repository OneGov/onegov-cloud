from datetime import timedelta
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.collections import PaginatedAgencyCollection
from onegov.agency.collections import PaginatedMembershipCollection
from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedPerson
from sedate import utcnow
from string import ascii_uppercase


def test_extended_agencies(session):
    agencies = ExtendedAgencyCollection(session)
    root = agencies.add_root(title="Agency")
    assert isinstance(root, ExtendedAgency)
    assert isinstance(agencies.query().one(), ExtendedAgency)


def test_extended_people(session):
    people = ExtendedPersonCollection(session)
    person = people.add(first_name="Hans", last_name="Maulwurf")
    assert isinstance(person, ExtendedPerson)
    assert isinstance(people.query().one(), ExtendedPerson)


def test_extended_people_pagination(session):
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

    assert len(people.next.batch) == 6
    assert len(people.page_by_index(1).batch) == 6


def test_extended_people_filter(session):
    people = ExtendedPersonCollection(session)
    people.add(first_name="Hans", last_name="Maulwurf")
    people.add(first_name="Waylon", last_name="Śmithers")
    people.add(first_name="Lenny", last_name="leonard")
    people.add(first_name="Carl", last_name="Çarlson")
    ned = people.add(first_name="Ned", last_name="Flanders")

    agencies = ExtendedAgencyCollection(session)
    agencies.add_root(title="Police").add_person(ned.id, "Snitch")
    agencies.add_root(title="Ħospital").add_person(ned.id, "Volunteer")
    agencies.add_root(title="Moe's Tavern")

    assert [p.last_name for p in people.query()] == [
        "Çarlson", "Flanders", "leonard", "Maulwurf", "Śmithers"
    ]

    people = people.for_filter(letter="C")
    assert [p.last_name for p in people.query()] == ['Çarlson']

    people = people.for_filter(letter="c")
    assert [p.last_name for p in people.query()] == ['Çarlson']

    people = people.for_filter(letter="L")
    assert [p.last_name for p in people.query()] == ['leonard']

    people = people.for_filter(agency="Police")
    assert [p.last_name for p in people.query()] == []

    people = people.for_filter(letter=None)
    assert [p.last_name for p in people.query()] == ['Flanders']


def test_extended_people_used_letters(session):
    assert ExtendedPersonCollection(session).used_letters == []

    people = ExtendedPersonCollection(session)
    people.add(first_name="Hans", last_name="Maulwurf")
    people.add(first_name="Waylon", last_name="Śmithers")
    people.add(first_name="Lenny", last_name="leonard")
    people.add(first_name="Carl", last_name="Çarlson")
    people.add(first_name="Ned", last_name="Flanders")

    assert people.used_letters == ['C', 'F', 'L', 'M', 'S']


def test_extended_people_used_agencies(session):
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


def test_extended_people_exclude_hidden(session):
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


def test_paginated_agencies(session):
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
    assert len(collection.next.next.batch) == 10
    assert collection.next.previous == collection
    assert len(collection.page_by_index(6).batch) == 1

    def count(**kwargs):
        return PaginatedAgencyCollection(session, **kwargs).subset_count

    assert count(exclude_hidden=False) == 63
    assert count(parent=parent.id) == 5
    assert count(parent=parent.id, exclude_hidden=False) == 6


def test_paginated_memberships(session):
    agencies = ExtendedAgencyCollection(session)
    a = agencies.add_root(title="A")
    b = agencies.add_root(title="B")

    people = ExtendedPersonCollection(session)
    x = people.add(first_name="X", last_name="X")
    y = people.add(first_name="Y", last_name="Y")
    z = people.add(first_name="z", last_name="z")

    for number in '012345678':
        a.add_person(x.id, number)
        a.add_person(y.id, number)
        n = a.add_person(z.id, number)
        m = b.add_person(x.id, number)

    n.meta['access'] = 'private'
    m.publication_start = utcnow() + timedelta(days=7)

    collection = PaginatedMembershipCollection(session)
    assert collection.subset_count == 34
    assert collection.pages_count == 4
    assert len(collection.batch) == 10
    assert collection.query().count() == 34
    assert len(collection.next.next.batch) == 10
    assert collection.next.previous == collection
    assert len(collection.page_by_index(3).batch) == 4

    def count(**kwargs):
        return PaginatedMembershipCollection(session, **kwargs).subset_count

    assert count(exclude_hidden=False) == 36
    assert count(agency=a.id) == 26
    assert count(agency=a.id, exclude_hidden=False) == 27
    assert count(person=x.id) == 17
    assert count(person=x.id, exclude_hidden=False) == 18
    assert count(agency=b.id, person=x.id) == 8
    assert count(agency=b.id, person=x.id, exclude_hidden=False) == 9
