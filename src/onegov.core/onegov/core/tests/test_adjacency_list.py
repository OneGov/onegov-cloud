import pytest

from onegov.core.orm.abstract import (
    AdjacencyList,
    AdjacencyListCollection,
    MoveDirection,
    sort_siblings,
)


class FamilyMember(AdjacencyList):
    __tablename__ = 'familymembers'


class UnusedList(AdjacencyList):
    # this class leads to errors if we didn't abstract the adjacency list
    # properly (duplicate indexes and so on)
    __tablename__ = 'unusedlist'


class DeadFamilyMember(FamilyMember):
    __mapper_args__ = {'polymorphic_identity': 'dead'}


class FamilyMemberCollection(AdjacencyListCollection):
    __listclass__ = FamilyMember


def test_add(session):

    family = FamilyMemberCollection(session)

    adam = family.add_root('Adam')

    assert adam.name == 'adam'
    assert adam.title == 'Adam'
    assert adam.root is adam
    assert list(adam.ancestors) == []
    assert adam.path == 'adam'
    assert adam.absorb == 'adam'
    assert adam.type is None

    child = family.add(parent=adam, title='Cain')

    assert child.name == 'cain'
    assert child.title == 'Cain'
    assert child.root is adam
    assert list(child.ancestors) == [adam]
    assert child.path == 'adam/cain'
    assert child.absorb == 'adam/cain'

    with pytest.raises(AssertionError):
        # normalized names are enforced
        child.name = 'Cain'

    grandchild = family.add(parent=child, title='Enoch')
    assert list(grandchild.ancestors) == [adam, child]
    assert repr(grandchild) == "FamilyMember(name='enoch', id=3, parent_id=2)"


def test_add_unique_page(session):

    family = FamilyMemberCollection(session)
    r1 = family.add_root(title='Test')
    r2 = family.add_root(title='Test')
    r3 = family.add_root(title='Test')

    assert r1.name == 'test'
    assert r2.name == 'test-1'
    assert r3.name == 'test-2'

    c1 = family.add(parent=r1, title='Test')
    c2 = family.add(parent=r1, title='Test')
    c3 = family.add(parent=r1, title='Test')

    assert c1.name == 'test'
    assert c2.name == 'test-1'
    assert c3.name == 'test-2'


def test_add_or_get_page(session):

    family = FamilyMemberCollection(session)
    root = family.add_or_get_root(title='Wurzel', name='root')

    assert root.title == 'Wurzel'
    assert root.name == 'root'

    root = family.add_or_get_root(title='Wurzel', name='root')

    assert root.title == 'Wurzel'
    assert root.name == 'root'


def test_page_by_path(session):

    family = FamilyMemberCollection(session)

    news = family.add_root('News')
    assert family.by_path('/news') is news
    assert family.by_path('/news/') is news
    assert family.by_path('news/') is news
    assert family.by_path('news') is news
    assert family.by_path('/neues') is None

    toast = family.add(parent=news, title='Yeah Toast')
    assert family.by_path('/news/yeah-toast') is toast
    assert family.by_path('news/yeah-toast') is toast
    assert family.by_path('news/yeah-toast/') is toast
    assert family.by_path('/news/yeah-toast/') is toast
    assert family.by_path('/news/jah-toast') is None


def test_delete(session):
    family = FamilyMemberCollection(session)

    news = family.add_root('News')
    assert family.by_path('/news') is news

    family.delete(news)

    assert family.by_path('/news') is None


def test_polymorphic(session):
    family = FamilyMemberCollection(session)
    eve = family.add_root("Eve")

    member = family.add(parent=eve, title='Lara', type='dead')
    assert isinstance(member, DeadFamilyMember)

    member = family.add(parent=eve, title='Steve')
    assert not isinstance(member, DeadFamilyMember)

    with pytest.raises(AssertionError) as assertion_info:
        member = family.add(parent=eve, title='Don', type='other')

    assert "No such polymorphic_identity: other" in str(assertion_info.value)

    assert isinstance(family.by_path('/eve'), FamilyMember)
    assert isinstance(family.by_path('/eve/lara'), DeadFamilyMember)
    assert isinstance(family.by_path('/eve/steve'), FamilyMember)

    assert family.by_path('/eve/lara')
    assert family.by_path('/eve/lara', ensure_type='dead')
    assert not family.by_path('/eve/lara', ensure_type='missing')
    assert not family.by_path('/eve/inexistant', ensure_type='dead')


def test_move_root(session):

    family = FamilyMemberCollection(session)
    a = family.add_root("a")
    b = family.add_root("b")
    assert family.query(ordered=True).all() == [a, b]

    family.move_below(target=a, subject=b)
    assert family.query(ordered=True).all() == [a, b]

    family.move_above(target=a, subject=b)
    assert family.query(ordered=True).all() == [b, a]

    family.move_below(target=b, subject=a)
    assert family.query(ordered=True).all() == [b, a]

    family.move_above(target=b, subject=a)
    assert family.query(ordered=True).all() == [a, b]


def test_move(session):

    family = FamilyMemberCollection(session)

    root = family.add_root("root")
    a = family.add(parent=root, title='a')
    b = family.add(parent=root, title='b')

    assert a.siblings.all() == [a, b]

    family.move_below(target=a, subject=b)
    assert a.siblings.all() == [a, b]

    family.move_above(target=a, subject=b)
    assert a.siblings.all() == [b, a]

    family.move_below(target=b, subject=a)
    assert a.siblings.all() == [b, a]

    family.move_above(target=b, subject=a)
    assert a.siblings.all() == [a, b]


def test_move_keep_hierarchy(session):

    family = FamilyMemberCollection(session)

    a = family.add_root("a")
    b = family.add(parent=a, title='b')
    c = family.add(parent=b, title='c')

    for direction in MoveDirection:
        for target in (a, b, c):
            with pytest.raises(AssertionError):
                family.move(target=target, subject=a, direction=direction)

            with pytest.raises(AssertionError):
                family.move(target=target, subject=b, direction=direction)

            with pytest.raises(AssertionError):
                family.move(target=target, subject=c, direction=direction)


def test_add_sorted(session):
    family = FamilyMemberCollection(session)

    root = family.add_root("root")
    e = family.add(parent=root, title='e')
    c = family.add(parent=root, title='c')
    a = family.add(parent=root, title='a')

    query = family.query(ordered=True).filter(FamilyMember.parent_id != None)

    assert query.all() == [a, c, e]

    b = family.add(parent=root, title='b')

    assert query.all() == [a, b, c, e]

    # once the tree is unsorted, items are added at the bottom
    family.move_above(target=a, subject=e)
    assert query.all() == [e, a, b, c]

    d = family.add(parent=root, title='d')

    assert query.all() == [e, a, b, c, d]

    # until it is sorted again
    sort_siblings(a.siblings.all(), family.sort_key)
    assert query.all() == [a, b, c, d, e]

    aa = family.add(parent=root, title='aa')
    assert query.all() == [a, aa, b, c, d, e]


def test_change_title(session):
    family = FamilyMemberCollection(session)

    root = family.add_root("root")
    a = family.add(parent=root, title='a')
    b = family.add(parent=root, title='b')
    c = family.add(parent=root, title='c')

    assert a.siblings.all() == [a, b, c]

    b.title = 'd'

    assert a.siblings.all() == [a, c, b]


def test_change_title_unordered(session):
    family = FamilyMemberCollection(session)

    root = family.add_root("root")
    a = family.add(parent=root, title='a', order=3)
    b = family.add(parent=root, title='b', order=1)
    c = family.add(parent=root, title='c', order=2)

    assert a.siblings.all() == [b, c, a]

    b.title = 'z'

    assert a.siblings.all() == [b, c, a]
