import pytest

from onegov.search import utils
from onegov.search.indexer import IndexManager


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
