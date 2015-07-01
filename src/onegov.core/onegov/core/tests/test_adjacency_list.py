import pytest

from onegov.core.orm.abstract import AdjacencyList, AdjacencyListCollection


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


def test_move_page(session):

    family = FamilyMemberCollection(session)
    root = family.add_root(title='Root')

    c1 = family.add(parent=root, title='One')
    c2 = family.add(parent=root, title='Two')

    family.move(c1, new_parent=c2)

    assert c1.parent is c2
    assert c2.parent is root


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

    member = family.add(parent=eve, title='Don', type='other')
    assert not isinstance(member, DeadFamilyMember)

    assert isinstance(family.by_path('/eve'), FamilyMember)
    assert isinstance(family.by_path('/eve/lara'), DeadFamilyMember)
    assert isinstance(family.by_path('/eve/steve'), FamilyMember)

    with pytest.raises(AssertionError) as assertion_info:
        assert not isinstance(family.by_path('/eve/don'), DeadFamilyMember)

    assert "No such polymorphic_identity" in str(assertion_info.value)

    assert family.by_path('/eve/lara')
    assert family.by_path('/eve/lara', ensure_type='dead')
    assert not family.by_path('/eve/lara', ensure_type='missing')
    assert not family.by_path('/eve/inexistant', ensure_type='dead')
