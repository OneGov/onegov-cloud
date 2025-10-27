from __future__ import annotations

import math
import morepath
import sedate
import transaction

from datetime import timedelta
from onegov.core import Framework
from onegov.core.orm import Base as RealBase
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.utils import scan_morepath_modules
from onegov.search import ORMSearchable, SearchApp, SearchIndex
from sqlalchemy import func, Boolean, Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from webtest import TestApp as Client


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import Base  # noqa: F401
    from onegov.core.request import CoreRequest


def test_app_integration() -> None:

    class App(Framework, SearchApp):
        pass

    app = App()
    app.namespace = 'test'
    app.configure_application(enable_search=True)
    assert not app.fts_search_enabled


def test_search_query(postgres_dsn: str) -> None:

    class App(Framework, SearchApp):
        pass

    @App.setting(section='i18n', name='locales')
    def locales() -> set[str]:
        return {'en', 'de'}

    @App.setting(section='i18n', name='default_locale')
    def default_locale() -> str:
        return 'en'

    # avoids confusing mypy
    if not TYPE_CHECKING:
        Base = declarative_base()

    class Document(Base, ORMSearchable):
        __tablename__ = 'documents'

        id: Column[int] = Column(Integer, primary_key=True)
        title: Column[str] = Column(Text, nullable=False)
        body: Column[str | None] = Column(Text, nullable=True)
        public: Column[bool] = Column(Boolean, nullable=False)
        language: Column[str] = Column(Text, nullable=False)

        fts_properties = {
            'title': {'type': 'localized', 'weight': 'A'},
            'body': {'type': 'localized', 'weight': 'A'}
        }

        @property
        def fts_suggestion(self) -> str:
            return self.title

        @property
        def fts_public(self) -> bool:
            return self.public

        @property
        def fts_language(self) -> str:
            return self.language

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.namespace = 'documents'
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        enable_search=True
    )
    # replace ORMBase with RealBase (we need RealBase for the search_index)
    app.session_manager.bases[1] = RealBase

    app.set_application_id('documents/home')
    assert app.fts_search_enabled

    session = app.session()
    session.add(Document(
        title="Public",
        body="This document can be seen by anyone",
        language='en',
        public=True
    ))
    session.add(Document(
        title="Private",
        body="This document is a secret",
        language='en',
        public=False
    ))
    session.add(Document(
        title="Öffentlich",
        body="Dieses Dokument kann jeder sehen",
        language='de',
        public=True
    ))
    session.add(Document(
        title="Privat",
        body="Dieses Dokument ist geheim",
        language='de',
        public=False
    ))
    transaction.commit()
    app.fts_indexer.process()

    search = session.query(func.count(SearchIndex.id))
    assert search.scalar() == 4
    assert search.filter_by(public=True).scalar() == 2

    query = search.filter_by(owner_type='Document')
    assert query.scalar() == 4
    assert query.filter_by(public=True).scalar() == 2


def test_orm_integration(
    postgres_dsn: str,
    redis_url: str
) -> None:

    class App(Framework, SearchApp):
        pass

    @App.setting(section='i18n', name='locales')
    def locales() -> set[str]:
        return {'en'}

    @App.setting(section='i18n', name='default_locale')
    def default_locale() -> str:
        return 'en'

    # avoids confusing mypy
    if not TYPE_CHECKING:
        Base = declarative_base()

    class Document(Base, ORMSearchable):
        __tablename__ = 'documents'

        id: Column[int] = Column(Integer, primary_key=True)
        title: Column[str] = Column(Text, nullable=False)
        body: Column[str | None] = Column(Text, nullable=True)

        @property
        def fts_suggestion(self) -> str:
            return self.title

        @property
        def fts_tags(self) -> list[str]:
            if not self.body:
                return []

            return [word for word in self.body.split(' ') if len(word) > 3]

        fts_public = True
        fts_language = 'en'
        fts_properties = {
            'title': {'type': 'localized', 'weight': 'A'},
            'body': {'type': 'localized', 'weight': 'A'}
        }

    @App.path(path='/')
    class Root:
        pass

    @App.json(model=Root)
    def view_documents(self: Root, request: CoreRequest) -> Any:
        assert isinstance(request.app, App)
        assert request.app.fts_search_enabled

        search = request.session.query(func.count(SearchIndex.id))

        query = request.GET.get('q')
        if query:
            if query.startswith('#'):
                search = search.filter(SearchIndex.fts_idx.op('@@')(
                    func.websearch_to_tsquery('simple', query)
                ))
            else:
                search = search.filter(
                    SearchIndex._tags.any_() == query.lstrip('#')
                )
        return search.scalar()

    @App.json(model=Root, name='new')
    def view_add_document(self: Root, request: CoreRequest) -> None:
        session = request.session
        session.add(Document(
            id=int(request.GET['id']),
            title=request.GET['title'],
            body=request.GET.get('body')
        ))

    @App.json(model=Root, name='update')
    def view_update_document(self: Root, request: CoreRequest) -> None:
        session = request.session
        query = session.query(Document)
        query = query.filter(Document.id == request.GET['id'])

        document = query.one()
        document.title = request.GET.get('title', document.title)
        document.body = request.GET.get('body', document.body)

    @App.json(model=Root, name='delete')
    def view_delete_document(self: Root, request: CoreRequest) -> None:
        session = request.session
        query = session.query(Document)
        query = query.filter(Document.id == request.params.get('id'))
        query.delete('fetch')

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.namespace = 'documents'
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        enable_search=True,
        redis_url=redis_url
    )
    # replace ORMBase with RealBase (we need RealBase for the search_index)
    app.session_manager.bases[1] = RealBase

    app.set_application_id('documents/home')

    # NOTE: Because our language is 'simple' the query will be a lot more
    #       case-sensitive than it otherwise might be, so for now we use
    #       all lower-case values, we might consider forcing our search
    #       index to be case-insensitive regardless of config.
    client = Client(app)
    client.get('/new?id=1&title=shop&body=we sell things and stuff')
    client.get('/new?id=2&title=about&body=we are a company')
    client.get('/new?id=3&title=terms&body=stuff we pay lawyers for')

    assert client.get('/').json == 3
    assert client.get('/?q=stuff').json == 2
    assert client.get('/?q=company').json == 1

    # %23 = #
    assert client.get('/?q=%23company').json == 1
    assert client.get('/?q=%23companx').json == 0

    client.get('/delete?id=3')

    assert client.get('/?q=stuff').json == 1

    client.get('/update?id=2&title=about&body=we are a business')

    assert client.get('/?q=company').json == 0
    assert client.get('/?q=business').json == 1


def test_alternate_id_property(postgres_dsn: str) -> None:

    class App(Framework, SearchApp):
        pass

    @App.setting(section='i18n', name='locales')
    def locales() -> set[str]:
        return {'en'}

    @App.setting(section='i18n', name='default_locale')
    def default_locale() -> str:
        return 'en'

    # avoids confusing mypy
    if not TYPE_CHECKING:
        Base = declarative_base()

    class MyUser(Base, ORMSearchable):
        __tablename__ = 'my-users'

        name: Column[str] = Column(Text, primary_key=True)
        fullname: Column[str] = Column(Text, nullable=False)

        @property
        def fts_suggestion(self) -> str:
            return self.name

        fts_id = 'name'
        fts_properties = {
            'fullname': {'type': 'text', 'weight': 'A'},
        }
        fts_language = 'en'
        fts_public = True

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.namespace = 'users'
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        enable_search=True
    )
    # replace ORMBase with RealBase (we need RealBase for the search_index)
    app.session_manager.bases[1] = RealBase

    app.set_application_id('users/corporate')
    assert app.fts_search_enabled

    session = app.session()
    session.add(MyUser(
        name="root",
        fullname="Lil' Root"
    ))
    session.add(MyUser(
        name="user",
        fullname="Lil' User"
    ))
    transaction.commit()
    app.fts_indexer.process()


    search = session.query(func.count(SearchIndex.id))

    assert search.scalar() == 2
    assert search.filter(SearchIndex.fts_idx.op('@@')(
        func.websearch_to_tsquery('english', 'Root')
    )).scalar() == 1
    assert search.filter_by(owner_type='MyUser').scalar() == 2


def test_orm_polymorphic(postgres_dsn: str) -> None:

    class App(Framework, SearchApp):
        pass

    @App.setting(section='i18n', name='locales')
    def locales() -> set[str]:
        return {'en'}

    @App.setting(section='i18n', name='default_locale')
    def default_locale() -> str:
        return 'en'

    # avoids confusing mypy
    if not TYPE_CHECKING:
        Base = declarative_base()

    class MyPage(Base, ORMSearchable):
        __tablename__ = 'my-pages'

        fts_properties = {
            'content': {'type': 'localized', 'weight': 'A'}
        }
        fts_language = 'en'
        fts_public = True

        @property
        def fts_suggestion(self) -> str:
            return self.content or ''

        id: Column[int] = Column(Integer, primary_key=True)
        content: Column[str | None] = Column(Text, nullable=True)
        type: Column[str] = Column(Text, nullable=False)

        __mapper_args__ = {
            "polymorphic_on": 'type'
        }

    class MyTopic(MyPage):
        __mapper_args__ = {'polymorphic_identity': 'topic'}

    class MyNews(MyPage):
        __mapper_args__ = {'polymorphic_identity': 'news'}

    class MyBreaking(MyNews):
        __mapper_args__ = {'polymorphic_identity': 'breaking'}

    scan_morepath_modules(App)
    morepath.commit()

    app = App()
    app.namespace = 'pages'
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        enable_search=True,
    )
    # replace ORMBase with RealBase (we need RealBase for the search_index)
    app.session_manager.bases[1] = RealBase

    app.set_application_id('pages/site')

    session = app.session()
    session.add(MyTopic(content="Topic", type='topic'))
    session.add(MyNews(content="News", type='news'))
    session.add(MyBreaking(content="Breaking", type='breaking'))

    def update() -> None:
        transaction.commit()
        app.fts_indexer.process()

    update()
    search = session.query(func.count(SearchIndex.id))
    assert search.scalar() == 3

    newsitem = session.query(MyPage).filter(MyPage.type == 'news').one()
    assert isinstance(newsitem, MyNews)

    newsitem.content = 'Story'
    update()
    assert search.filter(SearchIndex.fts_idx.op('@@')(
        func.websearch_to_tsquery('simple', 'story')
    )).scalar() == 1

    session.query(MyPage).filter(MyPage.type == 'news').delete()
    update()
    assert search.scalar() == 2

    session.delete(session.query(MyPage).filter(
        MyPage.type == 'breaking').one())
    update()
    assert search.scalar() == 1

    session.query(MyPage).delete()
    update()
    assert search.scalar() == 0


def test_orm_polymorphic_sublcass_only(postgres_dsn: str) -> None:

    class App(Framework, SearchApp):
        pass

    @App.setting(section='i18n', name='locales')
    def locales() -> set[str]:
        return {'en'}

    @App.setting(section='i18n', name='default_locale')
    def default_locale() -> str:
        return 'en'

    # avoids confusing mypy
    if not TYPE_CHECKING:
        Base = declarative_base()

    class Secret(Base):
        __tablename__ = 'secrets'

        id: Column[int] = Column(Integer, primary_key=True)
        content: Column[str | None] = Column(Text, nullable=True)
        type: Column[str | None] = Column(Text, nullable=True)

        __mapper_args__ = {
            "polymorphic_on": 'type'
        }

    class Open(Secret, ORMSearchable):
        __mapper_args__ = {'polymorphic_identity': 'open'}

        fts_public = True
        fts_properties = {
            'content': {'type': 'localized', 'weight': 'A'}
        }

        @property
        def fts_suggestion(self) -> str:
            return self.content or ''

    scan_morepath_modules(App)
    morepath.commit()

    app = App()
    app.namespace = 'pages'
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        enable_search=True
    )
    # replace ORMBase with RealBase (we need RealBase for the search_index)
    app.session_manager.bases[1] = RealBase

    app.set_application_id('pages/site')
    assert app.fts_search_enabled

    session = app.session()

    session.add(Secret(content="Sally knows"))
    session.add(Open(content="Peter knows"))

    transaction.commit()
    app.fts_indexer.process()

    search = session.query(func.count(SearchIndex.id))
    assert search.filter(SearchIndex.fts_idx.op('@@')(
        func.websearch_to_tsquery('english', 'sally')
    )).scalar() == 0
    assert search.filter(SearchIndex.fts_idx.op('@@')(
        func.websearch_to_tsquery('english', 'peter')
    )).scalar() == 1


def test_suggestions(postgres_dsn: str) -> None:

    class App(Framework, SearchApp):
        pass

    @App.setting(section='i18n', name='locales')
    def locales() -> set[str]:
        return {'en', 'de'}

    @App.setting(section='i18n', name='default_locale')
    def default_locale() -> str:
        return 'en'

    # avoids confusing mypy
    if not TYPE_CHECKING:
        Base = declarative_base()

    class Document(Base, ORMSearchable):
        __tablename__ = 'documents'

        id: Column[int] = Column(Integer, primary_key=True)
        title: Column[str] = Column(Text, nullable=False)
        public: Column[bool] = Column(Boolean, nullable=False)
        language: Column[str] = Column(Text, nullable=False)

        fts_properties = {
            'title': {'type': 'localized', 'weight': 'A'}
        }

        @property
        def fts_public(self) -> bool:
            return self.public

        @property
        def fts_language(self) -> str:
            return self.language

    class MyPerson(Base, ORMSearchable):
        __tablename__ = 'my-people'
        id: Column[int] = Column(Integer, primary_key=True)
        first_name: Column[str] = Column(Text, nullable=False)
        last_name: Column[str] = Column(Text, nullable=False)

        @property
        def title(self) -> str:
            return ' '.join((self.first_name, self.last_name))

        fts_properties = {'title': {'type': 'localized', 'weight': 'A'}}
        fts_public = True
        fts_language = 'en'

        @property
        def fts_suggestion(self) -> list[str]:
            return [
                ' '.join((self.first_name, self.last_name)),
                ' '.join((self.last_name, self.first_name))
            ]

    scan_morepath_modules(App)
    morepath.commit()

    app = App()
    app.namespace = 'documents'
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        enable_search=True,
    )
    # replace ORMBase with RealBase (we need RealBase for the search_index)
    app.session_manager.bases[1] = RealBase

    app.set_application_id('documents/home')
    assert app.fts_search_enabled is not None

    session = app.session()
    session.add(Document(
        title="Public Document",
        language='en',
        public=True
    ))
    session.add(Document(
        title="Private Document",
        language='en',
        public=False
    ))
    session.add(Document(
        title="Öffentliches Dokument",
        language='de',
        public=True
    ))
    session.add(Document(
        title="Privates Dokument",
        language='de',
        public=False
    ))
    session.add(MyPerson(
        first_name='Jeff',
        last_name='Winger'
    ))
    transaction.commit()
    app.fts_indexer.process()

    suggestions = session.query(
        func.unnest(
            SearchIndex.suggestion
        ).distinct().label('suggestion'),
        SearchIndex.public.label('public'),
    ).subquery()
    query = session.query(suggestions.c.suggestion)

    assert {s for s, in query.filter(
        suggestions.c.suggestion.ilike('p%')
    )} == {
        "Public Document",
        "Private Document",
        "Privates Dokument"
    }
    assert {s for s, in query.filter(
        suggestions.c.suggestion.ilike('p%')
    ).filter(suggestions.c.public == True)} == {"Public Document"}

    assert {s for s, in query.filter(
        suggestions.c.suggestion.ilike('ö%')
    )} == {
        "Öffentliches Dokument",
    }
    assert {s for s, in query.filter(
        suggestions.c.suggestion.ilike('ö%')
    ).filter(suggestions.c.public == True)} == {
        "Öffentliches Dokument",
    }

    assert {s for s, in query.filter(
        suggestions.c.suggestion.ilike('j%')
    )} == {
        'Jeff Winger'
    }
    assert {s for s, in query.filter(
        suggestions.c.suggestion.ilike('w%')
    )} == {
        'Winger Jeff'
    }


def test_language_detection(postgres_dsn: str) -> None:

    class App(Framework, SearchApp):
        pass

    @App.setting(section='i18n', name='locales')
    def locales() -> set[str]:
        return {'en', 'de', 'fr'}

    @App.setting(section='i18n', name='default_locale')
    def default_locale() -> str:
        return 'en'

    # avoids confusing mypy
    if not TYPE_CHECKING:
        Base = declarative_base()

    class Document(Base, ORMSearchable):
        __tablename__ = 'documents'

        id: Column[int] = Column(Integer, primary_key=True)
        title: Column[str] = Column(Text, nullable=False)

        fts_properties = {
            'title': {'type': 'localized', 'weight': 'A'}
        }

        fts_public = True

    scan_morepath_modules(App)
    morepath.commit()

    app = App()
    app.namespace = 'documents'
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        enable_search=True
    )
    # replace ORMBase with RealBase (we need RealBase for the search_index)
    app.session_manager.bases[1] = RealBase

    app.set_application_id('documents/home')
    assert app.fts_search_enabled is not None

    session = app.session()
    session.add(Document(title="Mein Dokument"))
    session.add(Document(title="My document"))
    session.add(Document(title="Mon document"))
    transaction.commit()
    app.fts_indexer.process()

    # FIXME: Do we want to store the detected language into the index
    #        so we can filter by language if we want to? Currently we
    #        index for all detected and supported languages, but
    #        de-prioritize results that don't match the language.
    #        Currently we can't really verify detection using our
    #        search index very reliably, so this test doesn't do anything
    # german = app.es_search(languages=['de']).execute().load()
    # english = app.es_search(languages=['en']).execute().load()
    # french = app.es_search(languages=['fr']).execute().load()

    # even very short sentences have pretty reliable detection now
    # assert len(german) == 1
    # assert len(english) == 1
    # assert len(french) == 1

    # assert german[0].title == "Mein Dokument"
    # assert english[0].title == "My document"
    # assert french[0].title == "Mon document"


def test_language_update(postgres_dsn: str) -> None:
    class App(Framework, SearchApp):
        pass

    @App.setting(section='i18n', name='locales')
    def locales() -> set[str]:
        return {'de', 'fr'}

    @App.setting(section='i18n', name='default_locale')
    def default_locale() -> str:
        return 'de'

    # avoids confusing mypy
    if not TYPE_CHECKING:
        Base = declarative_base()

    class Document(Base, ORMSearchable):
        __tablename__ = 'documents'

        id: Column[int] = Column(Integer, primary_key=True)
        title: Column[str] = Column(Text, nullable=False)

        fts_properties = {
            'title': {'type': 'localized', 'weight': 'A'}
        }

        fts_public = True

    scan_morepath_modules(App)
    morepath.commit()

    app = App()
    app.namespace = 'documents'
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        enable_search=True
    )
    # replace ORMBase with RealBase (we need RealBase for the search_index)
    app.session_manager.bases[1] = RealBase

    app.set_application_id('documents/home')
    assert app.fts_search_enabled is not None

    session = app.session()
    session.add(Document(title="Mein Dokument"))
    transaction.commit()
    app.fts_indexer.process()

    # FIXME: Same problem as with above test
    # german = app.es_search(languages=['de']).execute().load()
    # french = app.es_search(languages=['fr']).execute().load()
    # assert german
    # assert not french

    # session.query(Document).one().title = "Mon document"
    # transaction.commit()
    # app.fts_indexer.process()

    # german = app.es_search(languages=['de']).execute().load()
    # french = app.es_search(languages=['fr']).execute().load()
    # assert not german
    # assert french


def test_date_decay(postgres_dsn: str) -> None:

    class App(Framework, SearchApp):
        pass

    @App.setting(section='i18n', name='locales')
    def locales() -> set[str]:
        return {'de'}

    @App.setting(section='i18n', name='default_locale')
    def default_locale() -> str:
        return 'de'

    # avoids confusing mypy
    if not TYPE_CHECKING:
        Base = declarative_base()

    class Document(Base, ORMSearchable, TimestampMixin):
        __tablename__ = 'documents'

        id: Column[int] = Column(Integer, primary_key=True)
        title: Column[str] = Column(Text, nullable=False)
        body: Column[str] = Column(Text, nullable=False)

        fts_properties = {'title': {'type': 'localized', 'weight': 'A'}}
        fts_public = True

    scan_morepath_modules(App)
    morepath.commit()

    app = App()
    app.namespace = 'documents'
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        enable_search=True,
    )
    # replace ORMBase with RealBase (we need RealBase for the search_index)
    app.session_manager.bases[1] = RealBase

    app.set_application_id('documents/home')

    session = app.session()

    one = Document(id=1, title="Dokument", body="Eins")
    two = Document(id=2, title="Dokument", body="Zwei")

    one.modified = sedate.utcnow() - timedelta(days=365)
    two.modified = sedate.utcnow()

    session.add(one)
    session.add(two)

    def search(title: str) -> list[int]:
        transaction.commit()
        app.fts_indexer.process()

        search = session.query(SearchIndex.owner_id_int)
        search = search.filter(SearchIndex.fts_idx.op('@@')(
            func.websearch_to_tsquery('german', title)
        ))
        decay = 0.75
        scale = (30 * 24 * 3600)  # 30 days to reach target decay
        offset = (7 * 24 * 3600)  # 7 days without decay
        two_times_variance_squared = -(scale**2 / math.log(decay))
        search = search.order_by(
            func.greatest(
                func.exp(
                    -func.greatest(
                        func.abs(
                            func.extract(
                                'epoch',
                                sedate.utcnow() - func.coalesce(
                                    SearchIndex.last_change,
                                    sedate.utcnow()
                                )
                            )
                        ) - offset,
                        0
                    ).op('^')(2) / two_times_variance_squared
                ),
                1e-6
            ).desc()
        )
        return [doc_id for doc_id, in search]  # type: ignore[misc]

    assert search('Dokument') == [2, 1]

    one = session.query(Document).filter_by(id=1).one()
    two = session.query(Document).filter_by(id=2).one()

    one.modified = sedate.utcnow()
    two.modified = sedate.utcnow() - timedelta(days=365)

    transaction.commit()
    assert app.fts_indexer.queue.qsize() == 2

    assert search('Dokument') == [1, 2]
