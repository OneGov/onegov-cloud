import platform
import re

from copy import deepcopy
from elasticsearch.exceptions import NotFoundError, TransportError
from langdetect.lang_detect_exception import LangDetectException
from onegov.core.utils import is_non_string_iterable
from onegov.search import log, Searchable, utils
from queue import Queue, Empty, Full


ES_ANALYZER_MAP = {
    'en': 'english',
    'de': 'german',
    'fr': 'french',
    'en_html': 'english_html',
    'de_html': 'german_html',
    'fr_html': 'french_html',
}

ANALYSIS_CONFIG = {
    "filter": {
        "english_stop": {
            "type": "stop",
            "stopwords": "_english_"
        },
        "english_stemmer": {
            "type": "stemmer",
            "language": "english"
        },
        "english_possessive_stemmer": {
            "type": "stemmer",
            "language": "possessive_english"
        },
        "german_stop": {
            "type": "stop",
            "stopwords": "_german_"
        },
        "german_stemmer": {
            "type": "stemmer",
            "language": "light_german"
        },
        "french_elision": {
            "type": "elision",
            "articles_case": True,
            "articles": [
                "l", "m", "t", "qu", "n", "s",
                "j", "d", "c", "jusqu", "quoiqu",
                "lorsqu", "puisqu"
            ]
        },
        "french_stop": {
            "type": "stop",
            "stopwords": "_french_"
        },
        "french_keywords": {
            "type": "keyword_marker",
            "keywords": ["Exemple"]
        },
        "french_stemmer": {
            "type": "stemmer",
            "language": "light_french"
        }
    },
    "analyzer": {
        "english_html": {
            "tokenizer": "standard",
            "char_filter": [
                "html_strip"
            ],
            "filter": [
                "english_possessive_stemmer",
                "lowercase",
                "english_stop",
                "english_stemmer"
            ]
        },
        "german_html": {
            "tokenizer": "standard",
            "char_filter": [
                "html_strip"
            ],
            "filter": [
                "lowercase",
                "german_stop",
                "german_normalization",
                "german_stemmer"
            ]
        },
        "french_html": {
            "tokenizer": "standard",
            "char_filter": [
                "html_strip"
            ],
            "filter": [
                "french_elision",
                "lowercase",
                "french_stop",
                "french_keywords",
                "french_stemmer"
            ]
        },
        "autocomplete": {
            "type": "custom",
            "char_filter": ["html_strip"],
            "tokenizer": "standard",
            "filter": ["lowercase"]
        }
    }
}


class Indexer(object):
    """ Takes actions from a queue and executes them on the elasticsearch
    cluster. Depends on :class:`IndexManager` for index management and expects
    to have the same :class:`TypeRegistry` as :class:`ORMEventTranslator`.

    The idea is that this class does the indexing/deindexing, the index manager
    sets up the indices and the orm event translator listens for changes in
    the ORM.

    A queue is used so the indexer can be run in a separate thread.

    """

    def __init__(self, mappings, queue, es_client, hostname=None):
        self.es_client = es_client
        self.queue = queue
        self.hostname = hostname or platform.node()
        self.ixmgr = IndexManager(self.hostname, es_client=self.es_client)
        self.mappings = mappings
        self.failed_task = None

    def process(self, block=False, timeout=None):
        """ Processes the queue until it is empty or until there's an error.

        If there's an error, the next call to this function will try to
        execute the failed task again. This is mainly meant for elasticsearch
        outages.

        :block:
            If True, the process waits for the queue to be available. Useful
            if you run this in a separate thread.

        :timeout:
            How long the blocking call should block. Has no effect if
            ``block`` is False.

        :return: The number of successfully processed items

        """
        try:
            processed = 0
            while True:

                # get the previously failed task or a new one
                task = self.failed_task or self.queue.get(block, timeout)
                self.failed_task = None

                if self.process_task(task):
                    processed += 1
                else:
                    # if the task failed, keep it for the next run and give up
                    self.failed_task = task
                    return processed

        except Empty:
            pass

        return processed

    def process_task(self, task):
        try:
            getattr(self, task['action'])(task)
        except TransportError as e:
            log.exception("Failure during elasticsearch index task")
            return False

        self.queue.task_done()
        return True

    def ensure_index(self, task):
        return self.ixmgr.ensure_index(
            task['schema'],
            task['language'],
            self.mappings[task['type_name']],
            return_index='internal'
        )

    def index(self, task):
        index = self.ensure_index(task)

        self.es_client.index(
            index=index,
            doc_type=task['type_name'],
            id=task['id'],
            body=task['properties']
        )

    def delete(self, task):
        # get all the types this model could be stored in (with polymorphic)
        # identites, this could be many
        mapping = self.mappings[task['type_name']]

        if mapping.model:
            types = utils.related_types(mapping.model)
        else:
            types = (mapping.name, )

        # delete the document from all languages (because we don't know
        # which one anymore) - and delete from all related types (polymorphic)
        for type in types:
            ix = self.ixmgr.get_external_index_name(
                schema=task['schema'],
                language='*',
                type_name=type
            )

            # for the delete operation we need the internal index names
            for internal in self.es_client.indices.get_alias(index=ix).keys():
                try:
                    self.es_client.delete(
                        index=internal,
                        doc_type=type,
                        id=task['id']
                    )
                except NotFoundError:
                    pass


class TypeMapping(object):

    __slots__ = ['name', 'mapping', 'version', 'model']

    def __init__(self, name, mapping, model=None):
        self.name = name
        self.mapping = self.add_defaults(mapping)
        self.version = utils.hash_mapping(mapping)
        self.model = model

    def add_defaults(self, mapping):
        mapping['es_public'] = {
            'type': 'boolean',
            'include_in_all': False
        }

        mapping['es_suggestion'] = {
            'analyzer': 'autocomplete',
            'type': 'completion',
            'contexts': [
                {
                    'name': 'es_suggestion_context',
                    'type': 'category'
                }
            ]
        }
        return mapping

    def for_language(self, language):
        """ Returns the mapping for the given language. Mappings can
        be slightly different for each language. That is, the analyzer
        changes.

        Because the :class:`IndexManager` puts each language into its own
        index we do not have to worry about creating different versions
        of the same mapping here.

        """
        return self.supplement_analyzer(deepcopy(self.mapping), language)

    def supplement_analyzer(self, dictionary, language):
        """ Iterate through the dictionary found in the type mapping and
        replace the 'localized' type with a 'text' type that includes a
        language specific analyzer.

        """
        supplement = False

        for key, value in dictionary.items():

            if hasattr(value, 'items'):
                dictionary[key] = self.supplement_analyzer(value, language)

            elif key == 'type' and value.startswith('localized'):
                supplement = value.replace('localized', language)
                break

        if supplement:
            assert 'analyzer' not in dictionary
            dictionary[key] = 'text'
            dictionary['analyzer'] = ES_ANALYZER_MAP[supplement]

        return dictionary


class TypeMappingRegistry(object):

    def __init__(self):
        self.mappings = {}

    def __getitem__(self, key):
        return self.mappings[key]

    def __iter__(self):
        yield from self.mappings.values()

    def register_orm_base(self, base):
        """ Takes the given SQLAlchemy base and registers all
        :class:`~onegov.search.mixins.Searchable` objects.

        """
        for model in utils.searchable_sqlalchemy_models(base):
            self.register_type(model.es_type_name, model.es_properties, model)

    def register_type(self, type_name, mapping, model=None):
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
        self.mappings[type_name] = TypeMapping(type_name, mapping, model)

    @property
    def registered_fields(self):
        """ Goes through all the registered types and returns the a set with
        all fields used by the mappings.

        """
        return {key for mapping in self for key in mapping.mapping.keys()}


class IndexManager(object):
    """ Manages the creation/destruction of indices. The indices it creates
    have an internal name and an external alias. To facilitate that, versions
    are used.

    """

    def __init__(self, hostname, es_client):
        assert hostname and es_client

        self.hostname = hostname
        self.es_client = es_client
        self.created_indices = set()

    @property
    def normalized_hostname(self):
        return utils.normalize_index_segment(
            self.hostname, allow_wildcards=False)

    def query_indices(self):
        """ Queryies the elasticsearch cluster for indices belonging to this
        hostname. """

        return set(
            ix for ix in self.es_client.indices.get(
                '{}-*'.format(self.normalized_hostname), feature='_settings'
            )
        )

    def query_aliases(self):
        """ Queryies the elasticsearch cluster for aliases belonging to this
        hostname. """

        result = set()

        infos = self.es_client.indices.get_alias(
            '{}-*'.format(self.normalized_hostname))

        for info in infos.values():
            for alias in info['aliases']:
                result.add(alias)

        return result

    def ensure_index(self, schema, language, mapping, return_index='external'):
        """ Takes the given database schema, language and type name and
        creates an internal index with a version number and an external
        alias without the version number.

        :schema:
            The database schema this index is based on.

        :language:
            The language in ISO 639-1 format.

        :mapping:
            The :class:`TypeMapping` mapping used in this index.

        :return_index:
            The index name to return. Either 'external' or 'internal'.

        :return:
            The (external/aliased) name of the created index.

        """
        assert schema and language and mapping
        assert len(language) == 2
        assert return_index == 'external' or return_index == 'internal'

        external = self.get_external_index_name(schema, language, mapping.name)
        internal = self.get_internal_index_name(
            schema, language, mapping.name, mapping.version)

        return_value = return_index == 'external' and external or internal

        if internal in self.created_indices:
            return return_value

        if self.es_client.indices.exists(internal):
            self.created_indices.add(internal)
            return return_value

        # create the index
        self.es_client.indices.create(internal, body={
            'mappings': {
                mapping.name: {'properties': mapping.for_language(language)}
            },
            'settings': {
                'analysis': ANALYSIS_CONFIG,
                'index.mapper.dynamic': False
            }
        })

        # point the alias to the new index
        self.es_client.indices.put_alias(name=external, index=internal)

        # cache the result
        self.created_indices.add(internal)

        return return_value

    def remove_expired_indices(self, current_mappings):
        """ Removes all expired indices. An index is expired if it's version
        number is no longer known in the current mappings.

        :return: The number of indices that were deleted.

        """
        active_versions = set(m.version for m in current_mappings)

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

    def get_managed_indices_wildcard(self, schema):
        """ Returns a wildcard index name for all indices managed. """
        return '-'.join((
            utils.normalize_index_segment(
                self.hostname, allow_wildcards=False),
            utils.normalize_index_segment(
                schema, allow_wildcards=False),
            '*'
        ))

    def get_external_index_names(self, schema, languages='*', types='*'):
        """ Returns a comma separated string of external index names that
        match the given arguments. Useful to pass on to elasticsearch when
        targeting multiple indices.

        """
        indices = []

        for language in languages:
            for type_name in types:
                indices.append(
                    self.get_external_index_name(schema, language, type_name))

        return ','.join(indices)

    def get_external_index_name(self, schema, language, type_name):
        """ Generates the external index name from the given parameters. """

        segments = (self.hostname, schema, language, type_name)
        segments = (
            utils.normalize_index_segment(s, allow_wildcards=True)
            for s in segments
        )

        return '-'.join(segments)

    def get_internal_index_name(self, schema, language, type_name, version):
        """ Generates the internal index name from the given parameters. """

        return '-'.join((
            self.get_external_index_name(schema, language, type_name),
            utils.normalize_index_segment(version, allow_wildcards=False)
        ))


class ORMLanguageDetector(utils.LanguageDetector):

    html_strip_expression = re.compile(r'<[^<]+?>')

    def localized_properties(self, obj):
        for key, definition in obj.es_properties.items():
            if definition.get('type', '').startswith('localized'):
                yield key

    def localized_texts(self, obj, max_chars=None):
        chars = 0

        for p in self.localized_properties(obj):
            text = getattr(obj, p, '')

            if not isinstance(text, str):
                continue

            yield text.strip()

            chars += len(text)

            if max_chars is not None and max_chars <= chars:
                break

    def detect_object_language(self, obj):
        properties = self.localized_properties(obj)

        if not properties:
            # here, the mapping will be the same for all languages
            return self.supported_languages[0]

        text = ' '.join(self.localized_texts(obj, max_chars=1024))
        text = self.html_strip_expression.sub('', text).strip()

        if not text:
            return self.supported_languages[0]

        try:
            return self.detect(text)
        except LangDetectException:
            return self.supported_languages[0]


class ORMEventTranslator(object):
    """ Handles the onegov.core orm events, translates them into indexing
    actions and puts the result into a queue for the indexer to consume.

    The queue may be limited. Once the limit is reached, new events are no
    longer processed and an error is logged.

    """

    converters = {
        'date': lambda dt: dt.isoformat(),
    }

    def __init__(self, mappings, max_queue_size=0, languages=(
        'de', 'fr', 'en'
    )):
        self.mappings = mappings
        self.queue = Queue(maxsize=max_queue_size)
        self.detector = ORMLanguageDetector(languages)

    def on_insert(self, schema, obj):
        if isinstance(obj, Searchable):
            self.index(schema, obj)

    def on_update(self, schema, obj):
        if isinstance(obj, Searchable):
            self.index(schema, obj)

    def on_delete(self, schema, obj):
        if isinstance(obj, Searchable):
            self.delete(schema, obj)

    def put(self, translation):
        try:
            self.queue.put_nowait(translation)
        except Full:
            log.error("The orm event translator queue is full!")

    def index(self, schema, obj):
        if obj.es_skip:
            return

        if obj.es_language == 'auto':
            language = self.detector.detect_object_language(obj)
        else:
            language = obj.es_language

        translation = {
            'action': 'index',
            'id': getattr(obj, obj.es_id),
            'schema': schema,
            'type_name': obj.es_type_name,
            'language': language,
            'properties': {}
        }

        mapping = self.mappings[obj.es_type_name].for_language(language)

        for prop, mapping in mapping.items():

            if prop == 'es_suggestion':
                continue

            convert = self.converters.get(mapping['type'], lambda v: v)
            raw = getattr(obj, prop)

            if is_non_string_iterable(raw):
                translation['properties'][prop] = [convert(v) for v in raw]
            else:
                translation['properties'][prop] = convert(raw)

        if obj.es_public:
            contexts = {'es_suggestion_context': ['public']}
        else:
            contexts = {'es_suggestion_context': ['private']}

        suggestion = obj.es_suggestion

        if is_non_string_iterable(suggestion):
            translation['properties']['es_suggestion'] = {
                'input': suggestion,
                'contexts': contexts
            }
        else:
            translation['properties']['es_suggestion'] = {
                'input': [suggestion],
                'contexts': contexts
            }

        self.put(translation)

    def delete(self, schema, obj):

        translation = {
            'action': 'delete',
            'schema': schema,
            'type_name': obj.es_type_name,
            'id': getattr(obj, obj.es_id)
        }

        self.put(translation)
