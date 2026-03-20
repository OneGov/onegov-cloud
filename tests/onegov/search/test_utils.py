from __future__ import annotations

from onegov.search import ORMSearchable, Searchable, SearchableContent
from onegov.search import utils
from sqlalchemy.orm import mapped_column, registry, DeclarativeBase, Mapped


from typing import Any


def test_get_searchable_sqlalchemy_models() -> None:
    class Foo(DeclarativeBase):
        registry = registry()

    class Bar(DeclarativeBase):
        registry = registry()

    class A(Foo):
        __tablename__ = 'as'
        id: Mapped[int] = mapped_column(primary_key=True)

    class B(Foo, Searchable):
        __tablename__ = 'bs'
        id: Mapped[int] = mapped_column(primary_key=True)

    class C(Bar):
        __tablename__ = 'cs'
        id: Mapped[int] = mapped_column(primary_key=True)

    class D(Bar, Searchable):
        __tablename__ = 'ds'
        id: Mapped[int] = mapped_column(primary_key=True)

    assert list(utils.searchable_sqlalchemy_models(Foo)) == [B]
    assert list(utils.searchable_sqlalchemy_models(Bar)) == [D]


def test_get_searchable_sqlalchemy_models_inheritance() -> None:
    class Base(DeclarativeBase):
        registry = registry()

    class Page(Base, Searchable):
        __tablename__ = 'pages'
        id: Mapped[int] = mapped_column(primary_key=True)

    class Topic(Page):
        pass

    class News(Page):
        pass

    class B(Base):
        id: Mapped[int] = mapped_column(primary_key=True)
        __tablename__ = 'b'

    assert list(utils.searchable_sqlalchemy_models(Base)) == [
        Page, Topic, News
    ]


def test_get_polymorphic_base() -> None:
    class Base(DeclarativeBase):
        registry = registry()

    class Ticket(Base, ORMSearchable):
        __tablename__ = 'tickets'
        id: Mapped[int] = mapped_column(primary_key=True)
        type: Mapped[str] = mapped_column(default=lambda: 'ticketi')

        __mapper_args__ = {
            'polymorphic_on': 'type',
            'polymorphic_identity': 'ticketi'
        }

    class XTicket(Ticket):
        __mapper_args__ = {'polymorphic_identity': 'ticketi-x'}

    class YTicket(Ticket):
        __mapper_args__ = {'polymorphic_identity': 'ticketi-y'}

    def filter_for_base_models(models: set[type[Any]]) -> set[type[Any]]:
        return {utils.get_polymorphic_base(model) for model in models}

    assert filter_for_base_models({XTicket, YTicket, Ticket}) == {Ticket}

    class Letter(Base, Searchable):
        __tablename__ = 'letter'

        id: Mapped[int] = mapped_column(primary_key=True)
        type: Mapped[str] = mapped_column(default=lambda: 'letter')

        __mapper_args__ = {
            'polymorphic_on': 'type',
            'polymorphic_identity': 'letter'
        }

    class A(Letter):
        __mapper_args__ = {'polymorphic_identity': 'a'}

    class AA(A):
        __mapper_args__ = {'polymorphic_identity': 'aa'}

    class B(Letter, Searchable):
        __mapper_args__ = {'polymorphic_identity': 'b'}

    class C(Letter, Searchable):
        __mapper_args__ = {'polymorphic_identity': 'c'}

    class CC(C):
        __mapper_args__ = {'polymorphic_identity': 'cc'}

    assert filter_for_base_models({Letter, A, AA, B, C, CC}) == {Letter}

    class AdjacencyList(Base):
        __abstract__ = True

        id: Mapped[int] = mapped_column(primary_key=True)
        type: Mapped[str] = mapped_column(default=lambda: 'generic')

        __mapper_args__ = {
            'polymorphic_on': 'type',
            'polymorphic_identity': 'generic'
        }

    class Page(AdjacencyList):
        __tablename__ = 'pages'

    class Topic(Page, SearchableContent):
        __mapper_args__ = {'polymorphic_identity': 'topic'}

    class News(Page, SearchableContent):
        __mapper_args__ = {'polymorphic_identity': 'news'}

    assert filter_for_base_models({Page, Topic, News}) == {Page}

    searchable_models = {
        m for m in utils.searchable_sqlalchemy_models(Base)}
    assert filter_for_base_models(searchable_models) == {
        Ticket, Letter, Page}
