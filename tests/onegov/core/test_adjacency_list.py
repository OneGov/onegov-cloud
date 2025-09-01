from __future__ import annotations

import pytest

from decimal import Decimal
from onegov.core.orm.abstract import (
    AdjacencyList,
    AdjacencyListCollection,
    MoveDirection,
    sort_siblings,
)
from onegov.core.orm.abstract.adjacency_list import numeric_priority


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class FamilyMember(AdjacencyList):
    __tablename__ = 'familymembers'


class UnusedList(AdjacencyList):
    # this class leads to errors if we didn't abstract the adjacency list
    # properly (duplicate indexes and so on)
    __tablename__ = 'unusedlist'


class DeadFamilyMember(FamilyMember):
    __mapper_args__ = {'polymorphic_identity': 'dead'}


class FamilyMemberCollection(AdjacencyListCollection[FamilyMember]):
    __listclass__ = FamilyMember


def test_add(session: Session) -> None:

    family = FamilyMemberCollection(session)

    adam = family.add_root('Adam')

    assert adam.name == 'adam'
    assert adam.title == 'Adam'
    assert adam.root is adam
    assert list(adam.ancestors) == []
    assert adam.path == 'adam'
    assert adam.absorb == 'adam'
    assert adam.type == 'generic'

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

    assert family.roots == [adam]


def test_add_unique_page(session: Session) -> None:

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


def test_add_or_get_page(session: Session) -> None:

    family = FamilyMemberCollection(session)
    root = family.add_or_get_root(title='Wurzel', name='root')

    assert root.title == 'Wurzel'
    assert root.name == 'root'
    assert family.query().count() == 1

    root = family.add_or_get_root(title='Wurzel', name='root')

    assert root.title == 'Wurzel'
    assert root.name == 'root'
    assert family.query().count() == 1

    # test case-insensitive
    test = family.add_or_get_root(title='Test')
    assert test.title == 'Test'
    assert test.name == 'test'
    assert family.query().count() == 2

    test = family.add_or_get_root(title='test')
    assert test.title == 'Test'
    assert test.name == 'test'
    assert family.query().count() == 2

    # invalid name (not normalized)
    with pytest.raises(
        AssertionError,
        match=r'The given name was not normalized'
    ):
        family.add_or_get_root(title='Test', name='Test')

    assert family.query().count() == 2


def test_page_by_path(session: Session) -> None:

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


def test_delete(session: Session) -> None:
    family = FamilyMemberCollection(session)

    news = family.add_root('News')
    assert family.by_path('/news') is news

    family.delete(news)

    assert family.by_path('/news') is None


def test_polymorphic(session: Session) -> None:
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


def test_move_root(session: Session) -> None:

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


def test_move(session: Session) -> None:

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


def test_move_keep_hierarchy(session: Session) -> None:

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


def test_add_sorted(session: Session) -> None:
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


def test_change_title(session: Session) -> None:
    family = FamilyMemberCollection(session)

    root = family.add_root("root")
    a = family.add(parent=root, title='a')
    b = family.add(parent=root, title='b')
    c = family.add(parent=root, title='c')

    assert a.siblings.all() == [a, b, c]

    b.title = 'd'

    assert a.siblings.all() == [a, c, b]


def test_change_title_unordered(session: Session) -> None:
    family = FamilyMemberCollection(session)

    root = family.add_root("root")
    a = family.add(parent=root, title='a', order=3)
    b = family.add(parent=root, title='b', order=1)
    c = family.add(parent=root, title='c', order=2)

    assert a.siblings.all() == [b, c, a]

    b.title = 'z'

    assert a.siblings.all() == [b, c, a]


def test_numeric_priority() -> None:
    assert numeric_priority('A') == 1000
    assert numeric_priority('AA') == 1100
    assert numeric_priority('BA') == 2100
    assert numeric_priority('ABA') == 1210
    input = (
        'A',
        'AA',
        'BA',
        'ABA',
        'Z',
    )
    assert sorted(input, key=numeric_priority) == [
        'A', 'AA', 'ABA', 'BA', 'Z'
    ]


def test_move_uses_binary_gap(session: Session) -> None:
    family = FamilyMemberCollection(session)
    root = family.add_root("root")

    # Add items - binary gap should assign initial fractional orders
    a = family.add(parent=root, title='a')
    b = family.add(parent=root, title='b')
    c = family.add(parent=root, title='c')
    session.flush()  # Calculate and save initial orders

    # Capture initial orders (should be fractional and ordered)
    order_a1 = a.order
    order_b1 = b.order
    order_c1 = c.order
    assert order_a1 < order_b1 < order_c1
    assert isinstance(order_a1, Decimal)

    # Move 'a' below 'b' -> order should be b, a, c
    family.move_below(subject=a, target=b)

    assert a.siblings.all() == [b, a, c]

    # Capture orders after move
    order_a2 = a.order
    order_b2 = b.order
    order_c2 = c.order

    # Check that 'a' got a new order, 'b' and 'c' kept theirs
    assert order_a2 != order_a1
    assert order_b2 == order_b1
    assert order_c2 == order_c1

    assert (Decimal(str(order_b2)) <
        Decimal(str(order_a2)) < Decimal(str(order_c2)))

    # Move 'c' above 'b' -> order should be c, b, a
    family.move_above(subject=c, target=b)

    assert a.siblings.all() == [c, b, a]

    order_a3 = a.order
    order_b3 = b.order
    order_c3 = c.order

    assert order_c3 != order_c2
    assert order_a3 == order_a2
    assert order_b3 == order_b2
    assert Decimal(str(order_c3)) < Decimal(str(order_b3))


def test_add_uses_binary_gap(session: Session) -> None:
    family = FamilyMemberCollection(session)
    root = family.add_root("root")

    # Add items one by one, flushing each time to see order calculation
    b = family.add(parent=root, title='b')
    order_b1 = b.order
    assert order_b1 == Decimal('65536')  # Default center

    a = family.add(parent=root, title='a')  # Should go before 'b'
    order_a1 = a.order
    order_b2 = b.order
    assert order_a1 < order_b2  # 'a' got order less than 'b'
    assert order_b2 == order_b1  # 'b's order didn't change
    assert order_a1 == order_b1 / 2  # Specifically, half of 'b's original

    c = family.add(parent=root, title='c')  # Should go after 'b'
    order_a2 = a.order
    order_b3 = b.order
    order_c1 = c.order
    assert order_a2 == order_a1  # 'a' didn't change
    assert order_b3 == order_b2  # 'b' didn't change
    assert order_c1 > order_b3  # 'c' got order greater than 'b'
    assert order_c1 == order_b3 + Decimal('1')

    # Verify final list order based on calculated numeric orders
    assert [item.title for item in root.children] == ['a', 'b', 'c']
