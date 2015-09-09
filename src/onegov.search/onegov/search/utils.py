import hashlib
import json
import re

from onegov.search import Searchable


def searchable_sqlalchemy_models(base):
    """ Searches through the given SQLAlchemy base and returns the classes
    of all SQLAlchemy models found which inherit from the
    :class:`onegov.search.mixins.Searchable` interface.

    """
    for class_ in base.__subclasses__():
        if issubclass(class_, Searchable):
            yield class_


_invalid_index_characters = re.compile(r'[\\/*?"<>|\s,A-Z:]+')


def is_valid_index_name(name):
    """ Checks if the given name is a valid elasticsearch index name.
    Elasticsearch does it's own checks, but we can do it earlier and we are
    a bit stricter.

    """

    if name.startswith(('_', '.')):
        return False

    if _invalid_index_characters.search(name):
        return False

    return True


def is_valid_type_name(name):
    # the type name may be part of the index name, so we use the same check
    return is_valid_index_name(name)


def normalize_index_segment(segment):
    valid = _invalid_index_characters.sub('_', segment).lower()
    return valid.replace('.', '_').replace('-', '_')


def hash_mapping(mapping):
    dump = json.dumps(mapping, sort_keys=True).encode('utf-8')
    return hashlib.sha1(dump).hexdigest()
