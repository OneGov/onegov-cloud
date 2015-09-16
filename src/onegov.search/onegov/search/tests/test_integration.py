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
