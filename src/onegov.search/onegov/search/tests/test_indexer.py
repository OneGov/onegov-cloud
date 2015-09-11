import pytest

from onegov.search import utils
from onegov.search.indexer import IndexManager, TypeMapping


def test_index_manager_assertions(es_url):

    with pytest.raises(AssertionError):
        IndexManager(hostname='', es_url=es_url)

    with pytest.raises(AssertionError):
        IndexManager(hostname='example.org', es_url='')

    ixmgr = IndexManager(hostname='test.example.org', es_url=es_url)

    with pytest.raises(AssertionError):
        ixmgr.ensure_index(schema='', language='de', type_name='pages')

    with pytest.raises(AssertionError):
        ixmgr.ensure_index(schema='asdf', language='', type_name='pages')

    with pytest.raises(AssertionError):
        ixmgr.ensure_index(schema='asdf', language='de', type_name='')

    with pytest.raises(AssertionError):
        ixmgr.ensure_index(schema='asdf', language='deu', type_name='pages')

    with pytest.raises(AssertionError):
        ixmgr.ensure_index(schema='asdf', language='de', type_name='')


def test_index_manager_connection(es_url, es_client):
    ixmgr = IndexManager(hostname='foobar', es_client=es_client)
    assert ixmgr.es_client.ping()

    ixmgr = IndexManager(hostname='foobar', es_url=es_url)
    assert ixmgr.es_client.ping()


def test_index_manager_separation(es_url):
    foo = IndexManager(hostname='foo', es_url=es_url)
    bar = IndexManager(hostname='bar', es_url=es_url)

    for mgr in (foo, bar):
        mgr.register_type('page', {
            'properties': {
                'title': {'type': 'string'}
            }
        })

    foo.ensure_index('foo', 'en', 'page')
    bar.ensure_index('bar', 'en', 'page')

    version = foo.mappings['page'].version

    assert foo.query_indices() == {'foo-foo-en-page' + '-' + version}
    assert bar.query_indices() == {'bar-bar-en-page' + '-' + version}
    assert foo.query_aliases() == {'foo-foo-en-page'}
    assert bar.query_aliases() == {'bar-bar-en-page'}


def test_index_creation(es_url):
    ixmgr = IndexManager(hostname='example.org', es_url=es_url)
    ixmgr.register_type('page', {
        'properties': {
            'title': {'type': 'string'}
        }
    })

    # create an index
    index = ixmgr.ensure_index(
        schema='foo_bar',
        language='en',
        type_name='page'
    )
    assert index == 'example_org-foo_bar-en-page'
    assert ixmgr.created_indices == {
        index + '-' + ixmgr.mappings['page'].version
    }
    assert ixmgr.query_indices() == ixmgr.created_indices
    assert ixmgr.query_aliases() == {index}

    # the slight change in the index name should be normalized away
    index = ixmgr.ensure_index(
        schema='foo-bar',
        language='en',
        type_name='page'
    )
    assert index == 'example_org-foo_bar-en-page'
    assert ixmgr.created_indices == {
        index + '-' + ixmgr.mappings['page'].version
    }
    assert ixmgr.query_indices() == ixmgr.created_indices
    assert ixmgr.query_aliases() == {index}

    # if we change a mapping (which we won't usually do at runtime), we
    # should get a new index
    previous_version = ixmgr.mappings['page'].version
    del ixmgr.mappings['page']
    ixmgr.register_type('page', {
        'properties': {
            'title': {'type': 'string'},
            'body': {'type': 'string'}
        }
    })
    index = ixmgr.ensure_index(
        schema='foo-bar',
        language='en',
        type_name='page'
    )
    assert index == 'example_org-foo_bar-en-page'
    assert ixmgr.created_indices == {
        index + '-' + previous_version,
        index + '-' + ixmgr.mappings['page'].version
    }
    assert ixmgr.query_indices() == ixmgr.created_indices
    assert ixmgr.query_aliases() == {index}

    # this leads to some indices no longer being used
    assert ixmgr.remove_expired_indices() == 1


def test_parse_index_name(es_url):
    ixmgr = IndexManager('foo', es_url)
    assert ixmgr.parse_index_name('hostname_org-my_schema-de-posts') == {
        'hostname': 'hostname_org',
        'schema': 'my_schema',
        'language': 'de',
        'type_name': 'posts',
        'version': None
    }

    assert ixmgr.parse_index_name('hostname_org-my_schema-de-posts-1') == {
        'hostname': 'hostname_org',
        'schema': 'my_schema',
        'language': 'de',
        'type_name': 'posts',
        'version': '1'
    }

    assert ixmgr.parse_index_name('asdf') == {
        'hostname': None,
        'schema': None,
        'language': None,
        'type_name': None,
        'version': None
    }


@pytest.mark.parametrize("is_valid", [
    utils.is_valid_index_name,
    utils.is_valid_type_name
])
def test_is_valid_name(is_valid):
    assert is_valid('asdf')
    assert is_valid('asdf.asdf')
    assert is_valid('asdf_asdf')
    assert is_valid('asdf-asdf')
    assert not is_valid('_asdf')
    assert not is_valid('.asdf')
    assert not is_valid('..asdf')
    assert not is_valid('\\')
    assert not is_valid('Abc')
    assert not is_valid('a:b')
    assert not is_valid('a/b')
    assert not is_valid('a*b')
    assert not is_valid('a?b')
    assert not is_valid('a"b')
    assert not is_valid('a<b')
    assert not is_valid('a>b')
    assert not is_valid('a|b')
    assert not is_valid('a b')
    assert not is_valid('a,b')


def test_mapping_for_language():

    mapping = TypeMapping({
        'title': {
            'type': 'localized'
        }
    })

    assert mapping.for_language('en') == {
        'title': {
            'type': 'string',
            'analyzer': 'english'
        }
    }

    mapping = TypeMapping({
        'title': {
            'properties': {
                'type': 'localized'
            }
        }
    })

    assert mapping.for_language('de') == {
        'title': {
            'properties': {
                'type': 'string',
                'analyzer': 'german'
            }
        }
    }
