from onegov.core.orm.cache import orm_cached
from onegov.core.orm.session_manager import SessionManager
from onegov.core.orm.sql import as_selectable, as_selectable_from_path
from sqlalchemy import event, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import object_session
from sqlalchemy_utils import TranslationHybrid
from zope.sqlalchemy import mark_changed


MISSING = object()


#: The base for all OneGov Core ORM Models
class ModelBase(object):

    #: set by :class:`onegov.core.orm.cache.OrmCacheDescriptor`, this attribute
    #: indicates if the current model was loaded from cache
    is_cached = False

    def __getstate__(self):
        """ Makes sure the session manager attached to the model is not
        pickled (stored in memcached). Not only does it not make sense to
        have connection state stored, it also leads to errors.

        Cached instances have to be merged back into the session as a result,
        but that's something you have to do anyway when pickling sqlalchemy
        models.

        """
        state = self.__dict__.copy()

        for key in ('session_manager', ):
            if key in state:
                del state[key]

        return state

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


def configure_listener(cls, key, instance):
    """ The zope.sqlalchemy transaction mechanism doesn't recognize changes to
    cached objects. The following code intercepts all object changes and marks
    the transaction as changed if there was a change to a cached object.

    """

    def mark_as_changed(obj, *args, **kwargs):
        if obj.is_cached:
            mark_changed(object_session(obj))

    event.listen(instance, 'append', mark_as_changed)
    event.listen(instance, 'remove', mark_as_changed)
    event.listen(instance, 'set', mark_as_changed)
    event.listen(instance, 'init_collection', mark_as_changed)
    event.listen(instance, 'dispose_collection', mark_as_changed)


event.listen(ModelBase, 'attribute_instrument', configure_listener)


__all__ = [
    'Base',
    'SessionManager',
    'as_selectable',
    'as_selectable_from_path',
    'translation_hybrid',
    'find_models',
    'orm_cached'
]
