from onegov.core.orm.session_manager import SessionManager
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import TranslationHybrid

MISSING = object()


#: The base for all OneGov Core ORM Models
class ModelBase(object):
    def __getstate__(self):
        """ Makes sure the session manager attached to the model is not
        pickled (stored in memcached). Not only does it not make sense to
        have connection state stored, it also leads to errors.

        Cached instances have to be merged back into the session as a result,
        but that's something you have to do anyway when pickling sqlalchemy
        models.

        """
        if 'session_manager' in self.__dict__:
            del self.__dict__['session_manager']

        return self.__dict__.copy()

    def __setstate__(self, state):
        self.__dict__ = state

    @classmethod
    def get_polymorphic_class(cls, identity_value, default=MISSING):
        """ Returns the polymorphic class if it exists, given the value
        of the polymorphic identity.

        Asserts that the identity is actually found, unless a default is
        provided.

        """
        mapper = inspect(cls).polymorphic_map.get(identity_value)

        if default is MISSING:
            assert mapper, "No such polymorphic_identity: {}".format(
                identity_value
            )

        return mapper and mapper.class_ or default

Base = declarative_base(cls=ModelBase)

#: A translation hybrid integrated with OneGov Core. See also:
#: http://sqlalchemy-utils.readthedocs.org/en/latest/internationalization.html
translation_hybrid = TranslationHybrid(
    current_locale=lambda obj: obj.session_manager.current_locale,
    default_locale=lambda obj: obj.session_manager.default_locale,
)


def find_models(base, is_match):
    """ Finds the ORM models in the given ORM base class that match a filter.

    The filter is called with each class in the instance and it is supposed
    to return True if it matches.

    For example, find all SQLAlchemy models that use
    :class:`~onegov.core.orm.mixins.ContentMixin`::

        from onegov.core.orm.mixins import ContentMixin
        find_models(base, is_match=lambda cls: issubclass(cls, ContentMixin))

    """
    for cls in base.__subclasses__():
        if is_match(cls):
            yield cls

        for cls in find_models(cls, is_match):
            yield cls

__all__ = ['Base', 'SessionManager', 'translation_hybrid', 'find_models']
