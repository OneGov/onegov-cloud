from elasticsearch import Elasticsearch
from onegov.core.utils import is_non_string_iterable
from onegov.search import log, utils
from onegov.search.compat import Queue, Full

ES_ANALYZER_MAP = {
    'en': 'english',
    'fr': 'french',
    'de': 'german',
    'it': 'italian'
}


class TypeMapping(object):

    __slots__ = ['mapping', 'version']

    def __init__(self, mapping):
        self.mapping = self.add_defaults(mapping)
        self.version = utils.hash_mapping(mapping)

    def add_defaults(self, mapping):
        mapping['public'] = {'type': 'boolean'}

        return mapping

    def for_language(self, language):
        """ Returns the mapping for the given language. Mappings can
        be slightly different for each language. That is, the analyzer
        changes.

        Because the :class:`IndexManager` puts each language into its own
        index we do not have to worry about creating different versions
        of the same mapping here.

        """
        return self.supplement_analyzer(self.mapping.copy(), language)

    def supplement_analyzer(self, dictionary, language):
        """ Iterate through the dictionary found in the type mapping and
        replace the 'localized' type with a 'string' type that includes a
        language specific analyzer.

        """
        supplement = False

        for key, value in dictionary.items():

            if hasattr(value, 'items'):
                dictionary[key] = self.supplement_analyzer(value, language)

            elif key == 'type' and value == 'localized':
                supplement = True

        if supplement:
            assert 'analyzer' not in dictionary
            dictionary[key] = 'string'
            dictionary['analyzer'] = ES_ANALYZER_MAP[language]

        return dictionary


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
                type_name: mapping.for_language(language)
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


class ORMEventTranslator(object):
    """ Handles the onegov.core orm events, translates them into indexing
    actions and puts the result into a queue for the indexer to consume.

    The queue may be limited. Once the limit is reached, new events are no
    longer processed and an error is logged.

    """

    converters = {
        'date': lambda dt: dt.isoformat(),
    }

    def __init__(self, max_queue_size=0):
        self.queue = Queue(maxsize=max_queue_size)

    def on_insert(self, schema, obj):
        self.index(schema, obj)

    def on_update(self, schema, obj):
        self.index(schema, obj)

    def on_delete(self, schema, obj):
        self.delete(schema, obj)

    def put(self, translation):
        try:
            self.queue.put_nowait(translation)
        except Full:
            log.error("The orm event translator queue is full!")

    def index(self, schema, obj):

        translation = {
            'action': 'index',
            'schema': schema,
            'type': obj.es_type_name,
            'id': obj.es_id,
            'language': obj.es_language,
            'public': obj.es_public,
            'properties': {}
        }

        for prop, mapping in obj.es_properties.items():
            convert = self.converters.get(mapping['type'], lambda v: v)
            raw = getattr(obj, prop)

            if is_non_string_iterable(raw):
                translation['properties'][prop] = [convert(v) for v in raw]
            else:
                translation['properties'][prop] = convert(raw)

        self.put(translation)

    def delete(self, schema, obj):

        translation = {
            'action': 'delete',
            'schema': schema,
            'type': obj.es_type_name,
            'id': obj.es_id
        }

        self.put(translation)
