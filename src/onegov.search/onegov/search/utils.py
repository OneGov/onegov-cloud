import hashlib
import json
import re


def searchable_sqlalchemy_models(base):
    """ Searches through the given SQLAlchemy base and returns the classes
    of all SQLAlchemy models found which inherit from the
    :class:`onegov.search.mixins.Searchable` interface.

    """
    from onegov.search import Searchable

    for class_ in base.__subclasses__():
        if issubclass(class_, Searchable):
            yield class_

        for class_ in searchable_sqlalchemy_models(class_):
            yield class_


_invalid_index_characters = re.compile(r'[\\/?"<>|\s,A-Z:]+')


def is_valid_index_name(name):
    """ Checks if the given name is a valid elasticsearch index name.
    Elasticsearch does it's own checks, but we can do it earlier and we are
    a bit stricter.

    """

    if name.startswith(('_', '.')):
        return False

    if _invalid_index_characters.search(name):
        return False

    if '*' in name:
        return False

    return True


def is_valid_type_name(name):
    # the type name may be part of the index name, so we use the same check
    return is_valid_index_name(name)


def normalize_index_segment(segment, allow_wildcards):
    valid = _invalid_index_characters.sub('_', segment).lower()

    if not allow_wildcards:
        valid = valid.replace('*', '_')

    return valid.replace('.', '_').replace('-', '_')


def hash_mapping(mapping):
    dump = json.dumps(mapping, sort_keys=True).encode('utf-8')
    return hashlib.sha1(dump).hexdigest()


class classproperty(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


def iter_subclasses(baseclass):
    for subclass in baseclass.__subclasses__():
        yield subclass

        for subclass in subclass.__subclasses__():
            yield subclass


def related_types(model):
    """ Gathers all related es type names from the given model. A type is
    counted as related a model is part of a polymorphic setup.

    If no polymorphic identity is found, the result is simply a set with the
    model's type itself.

    """

    result = {model.es_type_name}

    if hasattr(model, '__mapper_args__'):
        if 'polymorphic_on' in model.__mapper_args__:
            for subclass in iter_subclasses(model):
                if getattr(subclass, 'es_type_name', None):
                    result.add(subclass.es_type_name)

        elif 'polymorphic_identity' in model.__mapper_args__:
            for parentclass in model.__mro__:
                if not hasattr(model, '__mapper_args__'):
                    continue

                if 'polymorphic_on' in parentclass.__mapper_args__:
                    return related_types(parentclass)

    return result
