from onegov.search import Searchable


def searchable_sqlalchemy_models(base):
    """ Searches through the given SQLAlchemy base and returns the classes
    of all SQLAlchemy models found which inherit from the
    :class:`onegov.search.mixins.Searchable` interface.

    """
    for class_ in base.__subclasses__():
        if issubclass(class_, Searchable):
            yield class_
