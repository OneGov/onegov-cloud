import morepath
import pytest
import sedate
import transaction

from datetime import timedelta
from elasticsearch_dsl.function import SF
from elasticsearch_dsl.query import MatchPhrase, FunctionScore
from onegov.core import Framework
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.utils import scan_morepath_modules
from onegov.search import ElasticsearchApp, ORMSearchable
from sqlalchemy import Boolean, Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from time import sleep
from webtest import TestApp as Client


def test_app_integration(es_url):

    class App(Framework, ElasticsearchApp):
        pass

    app = App()
    app.configure_application(elasticsearch_hosts=[es_url])

    assert app.es_client.ping()

    # make sure we got the testing host
    assert len(app.es_client.transport.hosts) == 1
    assert app.es_client.transport.hosts[0]['port'] \
        == int(es_url.split(':')[-1])


def test_search_query(es_url, postgres_dsn):

    class App(Framework, ElasticsearchApp):
        pass

    Base = declarative_base()

    class Document(Base, ORMSearchable):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)
        title = Column(Text, nullable=False)
        body = Column(Text, nullable=True)
        public = Column(Boolean, nullable=False)
        language = Column(Text, nullable=False)

        es_properties = {
            'title': {'type': 'localized'},
            'body': {'type': 'localized'}
        }

        @property
        def es_suggestion(self):
            return self.title

        @property
        def es_public(self):
            return self.public

        @property
        def es_language(self):
            return self.language

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        elasticsearch_hosts=[es_url]
    )

    app.namespace = 'documents'
    app.set_application_id('documents/home')

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
    app.es_indexer.process()
    app.es_client.indices.refresh(index='_all')

    assert app.es_search().execute().hits.total == 2
    assert app.es_search(include_private=True).execute().hits.total == 4

    result = app.es_search(languages=['en']).execute()
    assert result.hits.total == 1

    result = app.es_search(languages=['de'], include_private=True).execute()
    assert result.hits.total == 2

    search = app.es_search(languages=['de'])
    assert search.query('match', body='Dokumente').execute().hits.total == 1

    search = app.es_search(languages=['de'], include_private=True)
    assert search.query('match', body='Dokumente').execute().hits.total == 2

    # test result loading in one query
    result = app.es_search(languages=['de'], include_private=True).execute()
    records = result.load()
    assert len(records) == 2
    assert isinstance(records[0], Document)
    assert True in (records[0].es_public, records[1].es_public)
    assert False in (records[0].es_public, records[1].es_public)

    # test result loading query
    result = app.es_search(languages=['de'], include_private=True).execute()
    query = result.query(type='documents')
    assert query.count() == 2
    assert query.filter(Document.public == True).count() == 1

    # test single result loading
    document = app.es_search(languages=['de']).execute()[0].load()
    assert document.title == "Öffentlich"
    assert document.public

    # test single result query
    document = app.es_search(languages=['de']).execute()[0].query().one()
    assert document.title == "Öffentlich"
    assert document.public


def test_orm_integration(es_url, postgres_dsn, redis_url):

    class App(Framework, ElasticsearchApp):
        pass

    Base = declarative_base()

    class Document(Base, ORMSearchable):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)
        title = Column(Text, nullable=False)
        body = Column(Text, nullable=True)

        @property
        def es_suggestion(self):
            return self.title

        es_public = True
        es_language = 'en'
        es_properties = {
            'title': {'type': 'localized'},
            'body': {'type': 'localized'}
        }

    @App.path(path='/')
    class Root(object):
        pass

    @App.json(model=Root)
    def view_documents(self, request):

        # make sure the changes are propagated in testing
        request.app.es_client.indices.refresh(index='_all')

        query = request.params.get('q')
        if query:
            return request.app.es_client.search(index='_all', body={
                'query': {
                    'multi_match': {
                        'query': query,
                        'fields': ['title', 'body']
                    }
                }
            })
        else:
            return request.app.es_client.search(index='_all')

    @App.json(model=Root, name='new')
    def view_add_document(self, request):
        session = request.session
        session.add(Document(
            id=request.params.get('id'),
            title=request.params.get('title'),
            body=request.params.get('body')
        ))

    @App.json(model=Root, name='update')
    def view_update_document(self, request):
        session = request.session
        query = session.query(Document)
        query = query.filter(Document.id == request.params.get('id'))

        document = query.one()
        document.title = request.params.get('title'),
        document.body = request.params.get('body'),

    @App.json(model=Root, name='delete')
    def view_delete_document(self, request):
        session = request.session
        query = session.query(Document)
        query = query.filter(Document.id == request.params.get('id'))
        query.delete('fetch')

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        elasticsearch_hosts=[es_url],
        redis_url=redis_url
    )

    app.namespace = 'documents'
    app.set_application_id('documents/home')

    client = Client(app)
    client.get('/new?id=1&title=Shop&body=We sell things and stuff')
    client.get('/new?id=2&title=About&body=We are a company')
    client.get('/new?id=3&title=Terms&body=Stuff we pay lawyers for')

    documents = client.get('/').json
    assert documents['hits']['total'] == 3

    documents = client.get('/?q=stuff').json
    assert documents['hits']['total'] == 2

    documents = client.get('/?q=company').json
    assert documents['hits']['total'] == 1

    client.get('/delete?id=3')

    documents = client.get('/?q=stuff').json
    assert documents['hits']['total'] == 1

    client.get('/update?id=2&title=About&body=We are a business')

    documents = client.get('/?q=company').json
    assert documents['hits']['total'] == 0

    documents = client.get('/?q=business').json
    assert documents['hits']['total'] == 1


def test_alternate_id_property(es_url, postgres_dsn):

    class App(Framework, ElasticsearchApp):
        pass

    Base = declarative_base()

    class User(Base, ORMSearchable):
        __tablename__ = 'users'

        name = Column(Text, primary_key=True)
        fullname = Column(Text, nullable=False)

        @property
        def es_suggestion(self):
            return self.name

        es_id = 'name'
        es_properties = {
            'fullname': {'type': 'text'},
        }
        es_language = 'en'
        es_public = True

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        elasticsearch_hosts=[es_url]
    )

    app.namespace = 'users'
    app.set_application_id('users/corporate')

    session = app.session()
    session.add(User(
        name="root",
        fullname="Lil' Root"
    ))
    session.add(User(
        name="user",
        fullname="Lil' User"
    ))
    transaction.commit()
    app.es_indexer.process()
    app.es_client.indices.refresh(index='_all')

    assert app.es_search().count() == 2
    assert app.es_search().query('match', fullname='Root').count() == 1

    assert app.es_search().execute().query(type='users').count() == 2
    assert len(app.es_search().execute().load()) == 2

    root = app.es_search().query('match', fullname='Root').execute()[0]
    assert root.query().count() == 1
    assert root.load().name == 'root'
    assert root.load().fullname == "Lil' Root"


def test_orm_polymorphic(es_url, postgres_dsn):

    class App(Framework, ElasticsearchApp):
        pass

    Base = declarative_base()

    class Page(Base, ORMSearchable):
        __tablename__ = 'pages'

        es_properties = {
            'content': {'type': 'localized'}
        }
        es_language = 'en'
        es_public = True

        @property
        def es_suggestion(self):
            return self.content

        id = Column(Integer, primary_key=True)
        content = Column(Text, nullable=True)
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

    class Breaking(News):
        __mapper_args__ = {'polymorphic_identity': 'breaking'}
        es_type_name = 'breaking'

    scan_morepath_modules(App)
    morepath.commit()

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        elasticsearch_hosts=[es_url]
    )

    app.namespace = 'pages'
    app.set_application_id('pages/site')

    session = app.session()
    session.add(Topic(content="Topic", type='topic'))
    session.add(News(content="News", type='news'))
    session.add(Breaking(content="Breaking", type='breaking'))

    def update():
        transaction.commit()
        app.es_indexer.process()
        app.es_client.indices.refresh(index='_all')

    update()
    assert app.es_search().count() == 3

    newsitem = session.query(Page).filter(Page.type == 'news').one()
    assert isinstance(newsitem, News)

    newsitem.content = 'Story'
    update()
    assert app.es_search().query('match', content='story').count() == 1

    session.query(Page).filter(Page.type == 'news').delete()
    update()
    assert app.es_search().count() == 2

    session.delete(session.query(Page).filter(Page.type == 'breaking').one())
    update()
    assert app.es_search().count() == 1

    session.query(Page).delete()
    update()
    assert app.es_search().count() == 0


def test_orm_polymorphic_sublcass_only(es_url, postgres_dsn):

    class App(Framework, ElasticsearchApp):
        pass

    Base = declarative_base()

    class Secret(Base):
        __tablename__ = 'secrets'

        id = Column(Integer, primary_key=True)
        content = Column(Text, nullable=True)
        type = Column(Text, nullable=True)

        __mapper_args__ = {
            "polymorphic_on": 'type'
        }

    class Open(Secret, ORMSearchable):
        __mapper_args__ = {'polymorphic_identity': 'open'}

        es_public = True
        es_properties = {
            'content': {'type': 'localized'}
        }

        @property
        def es_suggestion(self):
            return self.content

    scan_morepath_modules(App)
    morepath.commit()

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        elasticsearch_hosts=[es_url]
    )

    app.namespace = 'pages'
    app.set_application_id('pages/site')

    session = app.session()

    session.add(Secret(content="nobody knows"))
    session.add(Open(content="everybody knows"))

    transaction.commit()
    app.es_indexer.process()
    app.es_client.indices.refresh(index='_all')

    assert app.es_search().query('match', content='nobody').count() == 0
    assert app.es_search().query('match', content='everybody').count() == 1


def test_suggestions(es_url, postgres_dsn):

    class App(Framework, ElasticsearchApp):
        pass

    Base = declarative_base()

    class Document(Base, ORMSearchable):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)
        title = Column(Text, nullable=False)
        public = Column(Boolean, nullable=False)
        language = Column(Text, nullable=False)

        es_properties = {
            'title': {'type': 'localized'}
        }

        @property
        def es_public(self):
            return self.public

        @property
        def es_language(self):
            return self.language

    class Person(Base, ORMSearchable):
        __tablename__ = 'people'
        id = Column(Integer, primary_key=True)
        first_name = Column(Text, nullable=False)
        last_name = Column(Text, nullable=False)

        @property
        def title(self):
            return ' '.join((self.first_name, self.last_name))

        es_properties = {'title': {'type': 'localized'}}
        es_public = True
        es_language = 'en'

        @property
        def es_suggestion(self):
            return [
                ' '.join((self.first_name, self.last_name)),
                ' '.join((self.last_name, self.first_name))
            ]

    scan_morepath_modules(App)
    morepath.commit()

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        elasticsearch_hosts=[es_url]
    )

    app.namespace = 'documents'
    app.set_application_id('documents/home')

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
    session.add(Person(
        first_name='Jeff',
        last_name='Winger'
    ))
    transaction.commit()
    app.es_indexer.process()
    app.es_client.indices.refresh(index='_all')

    assert set(app.es_suggestions(query='p')) == {"Public Document"}
    assert set(app.es_suggestions(query='p', include_private=True)) == {
        "Public Document",
        "Private Document",
        "Privates Dokument"
    }
    assert set(app.es_suggestions(query='ö', languages=['de'])) == {
        "Öffentliches Dokument",
    }

    assert set(app.es_suggestions(
        query='ö', languages=['de'], include_private=True)) == {
        "Öffentliches Dokument",
    }

    assert set(app.es_suggestions(
        query='p', languages=['de'], include_private=True)) == {
        "Privates Dokument",
    }

    assert set(app.es_suggestions(query='j', languages=['en'])) == {
        'Jeff Winger'
    }

    assert set(app.es_suggestions(query='w', languages=['en'])) == {
        'Winger Jeff'
    }


def test_language_detection(es_url, postgres_dsn):

    class App(Framework, ElasticsearchApp):
        pass

    Base = declarative_base()

    class Document(Base, ORMSearchable):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)
        title = Column(Text, nullable=False)

        es_properties = {
            'title': {'type': 'localized'}
        }

        es_public = True

    scan_morepath_modules(App)
    morepath.commit()

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        elasticsearch_hosts=[es_url]
    )

    app.namespace = 'documents'
    app.set_application_id('documents/home')

    session = app.session()
    session.add(Document(title="Mein Dokument"))
    session.add(Document(title="My document"))
    session.add(Document(title="Mon document"))
    transaction.commit()
    app.es_indexer.process()
    app.es_client.indices.refresh(index='_all')

    german = app.es_search(languages=['de']).execute().load()
    english = app.es_search(languages=['en']).execute().load()
    french = app.es_search(languages=['fr']).execute().load()

    # this illustrates that language detection is not exact (esp. if the
    # text is rather short)
    assert len(german) == 1
    assert len(english) == 0
    assert len(french) == 2

    assert german[0].title == "Mein Dokument"
    assert french[0].title == "My document"
    assert french[1].title == "Mon document"


def test_language_update(es_url, postgres_dsn):
    class App(Framework, ElasticsearchApp):
        pass

    Base = declarative_base()

    class Document(Base, ORMSearchable):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)
        title = Column(Text, nullable=False)

        es_properties = {
            'title': {'type': 'localized'}
        }

        es_public = True

    scan_morepath_modules(App)
    morepath.commit()

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        elasticsearch_hosts=[es_url]
    )

    app.namespace = 'documents'
    app.set_application_id('documents/home')

    session = app.session()
    session.add(Document(title="Mein Dokument"))
    transaction.commit()
    app.es_indexer.process()
    app.es_client.indices.refresh(index='_all')

    german = app.es_search(languages=['de']).execute().load()
    french = app.es_search(languages=['fr']).execute().load()
    assert german
    assert not french

    session.query(Document).one().title = "Mon document"
    transaction.commit()
    app.es_indexer.process()
    app.es_client.indices.refresh(index='_all')

    german = app.es_search(languages=['de']).execute().load()
    french = app.es_search(languages=['fr']).execute().load()
    assert not german
    assert french


@pytest.mark.flaky(reruns=3)
def test_date_decay(es_url, postgres_dsn):

    class App(Framework, ElasticsearchApp):
        pass

    Base = declarative_base()

    class Document(Base, ORMSearchable, TimestampMixin):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)
        title = Column(Text, nullable=False)
        body = Column(Text, nullable=False)

        es_properties = {'title': {'type': 'localized'}}
        es_public = True

    scan_morepath_modules(App)
    morepath.commit()

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        elasticsearch_hosts=[es_url]
    )

    app.namespace = 'documents'
    app.set_application_id('documents/home')

    session = app.session()

    one = Document(id=1, title="Dokument", body="Eins")
    two = Document(id=2, title="Dokument", body="Zwei")

    one.created = sedate.utcnow() - timedelta(days=30)
    two.created = sedate.utcnow()

    session.add(one)
    session.add(two)

    transaction.commit()

    def search(title):
        app.es_indexer.process()
        app.es_client.indices.refresh(index='_all')

        search = app.es_search(languages=['de'])
        search = search.query(MatchPhrase(title={"query": title}))

        search.query = FunctionScore(query=search.query, functions=[
            SF('gauss', es_last_change={
                'offset': '7d',
                'scale': '90d',
                'decay': '0.5'
            })
        ])

        return search.execute()

    assert search("Dokument")[0].meta.id == '2'
    assert search("Dokument")[1].meta.id == '1'

    one = session.query(Document).filter_by(id=1).one()
    two = session.query(Document).filter_by(id=2).one()

    one.created = sedate.utcnow()
    two.created = sedate.utcnow() - timedelta(days=30)

    transaction.commit()

    # Travis needs some time to catch-up, no problem locally
    for _ in range(0, 60):
        result = search("Dokument")

        if result[0].meta.id == '1' and result[1].meta.id == '2':
            break

        sleep(1.0)

    else:
        assert search("Dokument")[0].meta.id == '1'
        assert search("Dokument")[1].meta.id == '2'
