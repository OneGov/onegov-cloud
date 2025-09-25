from onegov.search import ORMSearchable, Searchable, SearchableContent
from onegov.search import utils
from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base, declared_attr


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


def test_get_polymorphic_base():
    Base = declarative_base()

    class Ticket(Base, ORMSearchable):
        __tablename__ = 'tickets'
        id = Column(Integer, primary_key=True)
        type: 'Column[str]' = Column(
            Text, nullable=False, default=lambda: 'ticketi')

        @declared_attr
        def __mapper_args__(cls):  # type:ignore
            return {
                'polymorphic_on': cls.type,
                'polymorphic_identity': 'ticketi'
            }

    class XTicket(Ticket):
        __mapper_args__ = {'polymorphic_identity': 'ticketi-x'}  # type:ignore

    class YTicket(Ticket):
        __mapper_args__ = {'polymorphic_identity': 'ticketi-y'}  # type:ignore

    def filter_for_base_models(models):
        return {utils.get_polymorphic_base(model) for model in models}

    assert filter_for_base_models({XTicket, YTicket, Ticket}) == {Ticket}

    class Letter(Base, Searchable):
        __tablename__ = 'letter'

        id = Column(Integer, primary_key=True)
        type: 'Column[str]' = Column(
            Text, nullable=False, default=lambda: 'type')

        @declared_attr
        def __mapper_args__(cls):  # type:ignore
            return {
                'polymorphic_on': 'type',
                'polymorphic_identity': 'letter'
            }

    class A(Letter):
        __mapper_args__ = {'polymorphic_identity': 'a'}

    class AA(A):
        __mapper_args__ = {'polymorphic_identity': 'aa'}  # type:ignore

    class B(Letter, Searchable):
        __mapper_args__ = {'polymorphic_identity': 'b'}  # type:ignore

    class C(Letter, Searchable):
        __mapper_args__ = {'polymorphic_identity': 'c'}  # type:ignore

    class CC(C):
        __mapper_args__ = {'polymorphic_identity': 'cc'}  # type:ignore

    assert filter_for_base_models({Letter, A, AA, B, C, CC}) == {Letter}

    class AdjacencyList(Base):
        __abstract__ = True

        id: 'Column[int]' = Column(Integer, primary_key=True)
        type: 'Column[str]' = Column(
            Text, nullable=False, default=lambda: 'generic')

        @declared_attr
        def __mapper_args__(cls):  # type:ignore
            return {
                'polymorphic_on': cls.type,
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
