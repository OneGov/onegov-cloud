from onegov.search import ORMSearchable, Searchable
from onegov.search import utils
from sqlalchemy import Column, Integer, Text
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


def test_related_types():

    Base = declarative_base()

    class Page(Base, ORMSearchable):
        __tablename__ = 'pages'
        id = Column(Integer, primary_key=True)
        type = Column(Text, nullable=False)

        __mapper_args__ = {
            "polymorphic_on": 'type'
        }

    class Topic(Page):
        __mapper_args__ = {'polymorphic_identity': 'topic'}
        es_type_name = 'topic'

    class News(Page):
        __mapper_args__ = {'polymorphic_identity': 'news'}
        es_type_name = 'news'

    class Temp(Page):
        __mapper_args__ = {'polymorphic_identity': 'temp'}
        es_type_name = None

    assert utils.related_types(Page) == {'pages', 'topic', 'news'}
    assert utils.related_types(Topic) == {'pages', 'topic', 'news'}
    assert utils.related_types(News) == {'pages', 'topic', 'news'}
    assert utils.related_types(Temp) == {'pages', 'topic', 'news'}
