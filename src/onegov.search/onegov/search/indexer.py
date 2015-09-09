from elasticsearch import Elasticsearch
from onegov.search import utils


class TypeMapping(object):

    __slots__ = ['mapping', 'version']

    def __init__(self, mapping):
        self.mapping = mapping
        self.version = utils.hash_mapping(mapping)


class IndexManager(object):
    """ Manages the creation/destruction of indices. The indices it creates
    have an internal name and an external alias. To facilitate that, versions
    are used.

    """

    def __init__(self, hostname, es_url=None, es_client=None):
        assert hostname and (es_url or es_client)

        self.hostname = hostname
        self.es_client = es_client or Elasticsearch(es_url)
        self.mappings = {}
        self.created_indices = set()

    def register_type(self, type_name, mapping):
        """ Registers the given type with the given mapping. The mapping is
        as dictionary representing the part below the ``mappings/type_name``.

        See:

        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/\
        indices-create-index.html#mappings>`_

        When the mapping changes, a new index is created internally and the
        alias to this index (the external name of the index) is pointed to
        this new index.

        As a consequence, a change in the mapping requires a reindex.

        """

        assert type_name not in self.mappings
        self.mappings[type_name] = TypeMapping(mapping)

    def query_indices(self):
        """ Queryies the elasticsearch cluster for indices belonging to this
        hostname. """

        hostname = utils.normalize_index_segment(self.hostname)

        return set(
            ix for ix in self.es_client.indices.get(
                '{}-*'.format(hostname), feature='_settings'
            )
        )

    def query_aliases(self):
        """ Queryies the elasticsearch cluster for aliases belonging to this
        hostname. """

        result = set()

        hostname = utils.normalize_index_segment(self.hostname)
        infos = self.es_client.indices.get_aliases('{}-*'.format(hostname))

        for info in infos.values():
            for alias in info['aliases']:
                result.add(alias)

        return result

    def ensure_index(self, schema, language, type_name):
        """ Takes the given database schema, language and type name and
        creates an internal index with a version number and an external
        alias without the version number.

        :schema:
            The database schema this index is based on.

        :language:
            The language in ISO 639-1 format.

        :type:
            The type used in this index (must be registered through
            :meth:`register_type`)

        :return:
            The (external/aliased) name of the created index.

        """
        assert schema and language and type_name
        assert len(language) == 2

        mapping = self.mappings[type_name]

        external = self.get_external_index_name(schema, language, type_name)
        internal = self.get_internal_index_name(
            schema, language, type_name, mapping.version)

        if internal in self.created_indices:
            return external

        if self.es_client.indices.exists(internal):
            self.created_indices.add(internal)
            return external

        # create the index
        self.es_client.indices.create(internal, {
            'properties': {
                type_name: mapping.mapping
            }
        })

        # point the alias to the new index
        self.es_client.indices.put_alias(external, index=internal)

        # cache the result
        self.created_indices.add(internal)

        return external

    def remove_expired_indices(self):
        """ Removes all expired indices. An index is expired if it's version
        number is no longer known in the current mappings.

        :return: The number of indices that were deleted.

        """
        active_versions = set(m.version for m in self.mappings.values())

        count = 0
        for index in self.query_indices():
            info = self.parse_index_name(index)

            if info['version'] and info['version'] not in active_versions:
                self.es_client.indices.delete(index)
                self.created_indices.remove(index)
                count += 1

        return count

    def parse_index_name(self, index_name):
        """ Takes the given index name and returns the hostname, schema,
        language and type_name in a dictionary.

        * If the index_name doesn't match the pattern, all values are None.
        * If the index_name has no version, the version is None.

        """
        if index_name.count('-') == 3:
            hostname, schema, language, type_name = index_name.split('-')
            version = None
        elif index_name.count('-') == 4:
            hostname, schema, language, type_name, version =\
                index_name.split('-')
        else:
            hostname = None
            schema = None
            language = None
            type_name = None
            version = None

        return {
            'hostname': hostname,
            'schema': schema,
            'language': language,
            'type_name': type_name,
            'version': version
        }

    def get_external_index_name(self, schema, language, type_name):
        """ Generates the external index name from the given parameters. """

        segments = (self.hostname, schema, language, type_name)
        segments = (utils.normalize_index_segment(s) for s in segments)

        return '-'.join(segments)

    def get_internal_index_name(self, schema, language, type_name, version):
        """ Generates the internal index name from the given parameters. """

        return '-'.join((
            self.get_external_index_name(schema, language, type_name),
            utils.normalize_index_segment(version)
        ))
