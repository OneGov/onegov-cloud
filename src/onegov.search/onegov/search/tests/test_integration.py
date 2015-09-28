# -*- coding: utf-8 -*-
import json
import transaction

from morepath import setup
from onegov.core import Framework
from onegov.search import ElasticsearchApp, ORMSearchable
from onegov.testing.utils import scan_morepath_modules
from sqlalchemy import Boolean, Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
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
    config = setup()

    class App(Framework, ElasticsearchApp):
        testing_config = config

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

    scan_morepath_modules(App, config)
    config.commit()

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
        title=u"Öffentlich",
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
    assert document.title == u"Öffentlich"
    assert document.public

    # test single result query
    document = app.es_search(languages=['de']).execute()[0].query().one()
    assert document.title == u"Öffentlich"
    assert document.public


def test_orm_integration(es_url, postgres_dsn):
    config = setup()

    class App(Framework, ElasticsearchApp):
        testing_config = config

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
        session = request.app.session()
        session.add(Document(
            id=request.params.get('id'),
            title=request.params.get('title'),
            body=request.params.get('body')
        ))

    @App.json(model=Root, name='update')
    def view_update_document(self, request):
        session = request.app.session()
        query = session.query(Document)
        query = query.filter(Document.id == request.params.get('id'))

        document = query.one()
        document.title = request.params.get('title'),
        document.body = request.params.get('body'),

    @App.json(model=Root, name='delete')
    def view_delete_document(self, request):
        session = request.app.session()
        query = session.query(Document)
        query = query.filter(Document.id == request.params.get('id'))
        query.delete('fetch')

    scan_morepath_modules(App, config)
    config.commit()

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        elasticsearch_hosts=[es_url]
    )

    app.namespace = 'documents'
    app.set_application_id('documents/home')

    client = Client(app)
    client.get('/new?id=1&title=Shop&body=We sell things and stuff')
    client.get('/new?id=2&title=About&body=We are a company')
    client.get('/new?id=3&title=Terms&body=Stuff we pay lawyers for')

    documents = json.loads(client.get('/').text)
    assert documents['hits']['total'] == 3

    documents = json.loads(client.get('/?q=stuff').text)
    assert documents['hits']['total'] == 2

    documents = json.loads(client.get('/?q=company').text)
    assert documents['hits']['total'] == 1

    client.get('/delete?id=3')

    documents = json.loads(client.get('/?q=stuff').text)
    assert documents['hits']['total'] == 1

    client.get('/update?id=2&title=About&body=We are a business')

    documents = json.loads(client.get('/?q=company').text)
    assert documents['hits']['total'] == 0

    documents = json.loads(client.get('/?q=business').text)
    assert documents['hits']['total'] == 1


def test_alternate_id_property(es_url, postgres_dsn):
    config = setup()

    class App(Framework, ElasticsearchApp):
        testing_config = config

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
            'fullname': {'type': 'string'},
        }
        es_language = 'en'
        es_public = True

    scan_morepath_modules(App, config)
    config.commit()

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
    config = setup()

    class App(Framework, ElasticsearchApp):
        testing_config = config

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

    scan_morepath_modules(App, config)
    config.commit()

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


def test_suggestions(es_url, postgres_dsn):
    config = setup()

    class App(Framework, ElasticsearchApp):
        testing_config = config

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

    scan_morepath_modules(App, config)
    config.commit()

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
        title=u"Öffentliches Dokument",
        language='de',
        public=True
    ))
    session.add(Document(
        title=u"Privates Dokument",
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
        u"Öffentliches Dokument",
    }

    assert set(app.es_suggestions(
        query='ö', languages=['de'], include_private=True)) == {
        u"Öffentliches Dokument",
    }

    assert set(app.es_suggestions(
        query='p', languages=['de'], include_private=True)) == {
        "Privates Dokument",
    }

    assert set(app.es_suggestions(query='j', languages=['en'])) == {
        'Jeff Winger'
    }

    assert set(app.es_suggestions(query='w', languages=['en'])) == {
        'Jeff Winger'
    }
