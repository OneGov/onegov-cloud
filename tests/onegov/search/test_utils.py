from onegov.search import ORMSearchable, Searchable
from onegov.search import utils
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base


def test_get_searchable_sqlalchemy_models():
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


def test_get_searchable_sqlalchemy_models_inheritance():
    Base = declarative_base()

    class Page(Base, Searchable):
        __tablename__ = 'pages'
        id = Column(Integer, primary_key=True)

    class Topic(Page):
        pass

    class News(Page):
        pass

    class B(Base):
        id = Column(Integer, primary_key=True)
        __tablename__ = 'b'

    assert list(utils.searchable_sqlalchemy_models(Base)) == [
        Page, Topic, News
    ]


def test_filter_non_base_models():
    Base = declarative_base()

    class Page(Base, Searchable):
        id = Column(Integer, primary_key=True)
        __tablename__ = 'pages'

    class Topic(Page):
        pass

    class News(Page):
        pass

    assert utils.filter_non_base_models({Page, Topic, News}) == {Topic, News}

    class A(Base, Searchable):
        id = Column(Integer, primary_key=True)
        __tablename__ = 'a'

    class AA(A):
        pass

    class B(Base, Searchable):
        id = Column(Integer, primary_key=True)
        __tablename__ = 'b'

    class C(Base, Searchable):
        id = Column(Integer, primary_key=True)
        __tablename__ = 'c'

    class CC(C):
        id_2 = Column(Integer, primary_key=True)
        c_id = Column(Integer, ForeignKey('c.id'))
        __tablename__ = 'cc'

    assert utils.filter_non_base_models({A, AA, B, C, CC}) == {AA, B, C, CC}


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


def test_related_types_unsearchable_base():

    Base = declarative_base()

    # compared to test_related_types, this base class is not searchable
    class Page(Base):
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

    assert utils.related_types(Page) == {'news', 'topic'}
