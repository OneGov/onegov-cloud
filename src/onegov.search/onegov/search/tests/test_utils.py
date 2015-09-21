from onegov.search import Searchable
from onegov.search import utils
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base


def test_get_searchable_sqlalchemy_models(postgres_dsn):
    Foo = declarative_base()
    Bar = declarative_base()

    class A(Foo):
        __tablename__ = 'as'
        id = Column(Integer, primary_key=True)

    class B(Foo, Searchable):
        __tablename__ = 'bs'
        id = Column(Integer, primary_key=True)

    class C(Bar):
        __tablename__ = 'cs'
        id = Column(Integer, primary_key=True)

    class D(Bar, Searchable):
        __tablename__ = 'ds'
        id = Column(Integer, primary_key=True)

    assert list(utils.searchable_sqlalchemy_models(Foo)) == [B]
    assert list(utils.searchable_sqlalchemy_models(Bar)) == [D]


def test_get_searchable_sqlalchemy_models_inheritance(postgres_dsn):

    Base = declarative_base()

    class Page(Base, Searchable):
        __tablename__ = 'pages'
        id = Column(Integer, primary_key=True)

    class Topic(Page):
        pass

    class News(Page):
        pass

    assert list(utils.searchable_sqlalchemy_models(Base)) == [
        Page, Topic, News
    ]
