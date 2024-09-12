""" Provides a simple and mostly transparent way of defining orm-cached
properties on the application class.

For example::

    from onegov.core import Framework
    from onegov.core.orm import orm_cached

    class App(Framework):

        @orm_cached(policy='on-table-change:users')
        def users(self):
            # ... fetch users from database

Properties defined in this way are accessible through the instance::

    app.users

If there are any changes to the users table, the cache is removed. Since the
cache is usually a shared redis instance, this works for multiple processes.

"""

import inspect

from libres.db.models import ORMBase
from sqlalchemy.orm.query import Query


from typing import cast, overload, Any, Generic, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing import Protocol
    from typing import Self

    from . import Base
    from .session_manager import SessionManager
    from ..cache import RedisCacheRegion

    # NOTE: it would be more correct to make OrmCacheApp the first
    #       argument, but this gets a bit complicated for actually
    #       using the decorator
    Creator = Callable[[Any], '_T']
    CachePolicy = str | Callable[[Base], bool]

    class _OrmCacheDecorator(Protocol):
        @overload
        def __call__(
            self,
            fn: 'Creator[Query[_T]]'
        ) -> 'OrmCacheDescriptor[tuple[_T, ...]]': ...

        @overload
        def __call__(
            self,
            fn: 'Creator[_T]'
        ) -> 'OrmCacheDescriptor[_T]': ...

    class _HasApp(Protocol):
        @property
        def app(self) -> 'OrmCacheApp': ...

_T = TypeVar('_T')
_QT = TypeVar('_QT')


class OrmCacheApp:
    """ Integrates the orm cache handling into the application
    (i.e. :class:`onegov.core.framework.Framework`).

    In addition, the application needs to call :meth:`setup_orm_cache` inside
    of `:meth:onegov.server.application.Application.set_application_id` to
    enable the cache evicition mechanism.

    """

    if TYPE_CHECKING:
        # forward declare the attributes we need from Framework
        session_manager: SessionManager
        schema: str
        @property
        def cache(self) -> RedisCacheRegion: ...
        request_cache: dict[str, Any]

    def configure_orm_cache(self, **cfg: Any) -> None:
        self.is_orm_cache_setup = getattr(self, 'is_orm_cache_setup', False)

    def setup_orm_cache(self) -> None:
        """ Sets up the event handlers for the change-detection. """

        assert not self.is_orm_cache_setup

        for descriptor in self.orm_cache_descriptors:
            self.session_manager.on_insert.connect(
                self.descriptor_bound_orm_change_handler(descriptor),
                weak=False)
            self.session_manager.on_update.connect(
                self.descriptor_bound_orm_change_handler(descriptor),
                weak=False)
            self.session_manager.on_delete.connect(
                self.descriptor_bound_orm_change_handler(descriptor),
                weak=False)

        self.is_orm_cache_setup = True

    def descriptor_bound_orm_change_handler(
        self,
        descriptor: 'OrmCacheDescriptor[Any]'
    ) -> 'Callable[[str, Base], None]':
        """ Listens to changes to the database and evicts the cache if the
        policy demands it. Available policies:

        * policy='on-table-change:table': clears the cache if there's a change
          on the given table

        * policy=lambda obj: ...: clears the cache if the given policy function
          returns true (it receives the object which has changed)

        """

        def handle_orm_change(schema: str, obj: 'Base') -> None:

            if callable(descriptor.cache_policy):
                dirty = descriptor.cache_policy(obj)

            elif descriptor.cache_policy.startswith('on-table-change'):
                tablename = descriptor.cache_policy.split(':')[-1]
                dirty = obj.__class__.__tablename__ == tablename

            else:
                raise NotImplementedError()

            if dirty:
                # Two circumstances ensure that only the cache of the current
                # schema is evicted:
                #
                # 1. There's a current schema set when the event is fired.
                # 2. The current cache is bound to the current schema.
                #
                # Still, trust but verify:
                assert self.schema == schema
                for cache_key in descriptor.used_cache_keys:
                    self.cache.delete(cache_key)
                    if cache_key in self.request_cache:
                        del self.request_cache[cache_key]

        return handle_orm_change

    @property
    def orm_cache_descriptors(self) -> 'Iterator[OrmCacheDescriptor[Any]]':
        """ Yields all orm cache descriptors installed on the class. """

        for member_name, member in inspect.getmembers(self.__class__):
            if isinstance(member, OrmCacheDescriptor):
                yield member


class OrmCacheDescriptor(Generic[_T]):
    """ The descriptor implements the protocol for fetching the objects
    either from cache or creating them using the :param:``creator``.

    You are not allowed to store ORM objects in this cache, since it
    leads to unpredictable results when attempting to merge the restored
    objects with the current session.
    """

    #: A set of cache keys that have been accessed
    used_cache_keys: set[str]

    @overload
    def __init__(
        self: 'OrmCacheDescriptor[tuple[_QT, ...]]',
        cache_policy: 'CachePolicy',
        creator: 'Creator[Query[_QT]]',
        by_role: bool = False
    ): ...

    @overload
    def __init__(
        self: 'OrmCacheDescriptor[_T]',
        cache_policy: 'CachePolicy',
        creator: 'Creator[_T]',
        by_role: bool = False
    ): ...

    def __init__(
        self,
        cache_policy: 'CachePolicy',
        creator: 'Creator[Query[Any]] | Creator[_T]',
        by_role: bool = False
    ):
        self.cache_policy = cache_policy
        self.cache_key_prefix = creator.__qualname__
        self.used_cache_keys = set()
        self.creator = creator
        self.by_role = by_role

    def cache_key(self, obj: 'OrmCacheApp | _HasApp') -> str:
        if not self.by_role:
            return self.cache_key_prefix

        role = getattr(getattr(obj, 'identity', None), 'role', None)
        return f'{self.cache_key_prefix}-{role}'

    def assert_no_orm_objects(self, obj: object, depth: int = 0) -> None:
        """ Ensures the object contains no ORM objects

        """
        # FIXME: circular import
        from onegov.core.orm import Base
        assert not isinstance(obj, (Base, ORMBase)), (
            'You are not allowed to cache ORM objects with orm_cached.'
        )

        # for performance reasons we only check the first level of nesting
        # we also run into recursion depth issues if two orm_cached properties
        # rely on one another
        if depth >= 1:
            return

        if isinstance(obj, str):
            # avoid infinite recursion
            pass

        elif hasattr(obj, 'items'):
            # we need to check keys as well as values
            for key, value in obj.items():
                self.assert_no_orm_objects(key, depth + 1)
                self.assert_no_orm_objects(value, depth + 1)

        elif hasattr(obj, '__iter__'):
            # recurse into iterables
            for child in obj:
                self.assert_no_orm_objects(obj, depth + 1)

    def create(self, instance: 'OrmCacheApp | _HasApp') -> _T:
        """ Uses the creator to load the object to be cached.

        Since the return value of the creator might not be something we want
        to cache, this function will turn some return values into something
        more useful (e.g. queries are completely fetched).

        """

        result = self.creator(instance)

        if isinstance(result, Query):
            result = cast('_T', tuple(result))

        self.assert_no_orm_objects(result)
        return result


    def load(self, instance: 'OrmCacheApp | _HasApp') -> _T:
        """ Loads the object from the database or cache. """

        if isinstance(instance, OrmCacheApp):
            app = instance
        else:
            app = instance.app

        cache_key = self.cache_key(instance)
        self.used_cache_keys.add(cache_key)

        # we use a secondary request cache for even more lookup speed and to
        # make sure that inside a request we always get the exact same instance
        # (otherwise we don't see changes reflected)
        if cache_key in app.request_cache:
            return app.request_cache[cache_key]

        else:
            obj = app.cache.get_or_create(
                key=cache_key,
                creator=lambda: self.create(instance)
            )

        app.request_cache[cache_key] = obj

        return obj

    # NOTE: Technically this descriptor should only work on
    #       applications or objects with applications that derive
    #       from OrmCacheApp, however since we heavily use mixins
    #       that restriction becomes tedious, once Intersection
    #       is a thing, we can restrict this once again
    @overload
    def __get__(
        self,
        instance: None,
        owner: type[Any]
    ) -> 'Self': ...

    @overload
    def __get__(
        self,
        instance: Any,
        owner: type[Any]
    ) -> _T: ...

    def __get__(
        self,
        instance: Any | None,
        owner: type[Any]
    ) -> 'Self | _T':
        """ Handles the object/cache access. """

        if instance is None:
            return self

        return self.load(instance)


def orm_cached(
    policy: 'CachePolicy',
    by_role: bool = False
) -> '_OrmCacheDecorator':
    """ The decorator use to setup the cache descriptor.

    See the :mod:`onegov.core.orm.cache` docs for usage.

    """

    @overload
    def orm_cache_decorator(
        fn: 'Creator[Query[_T]]'
    ) -> 'OrmCacheDescriptor[tuple[_T, ...]]': ...

    @overload
    def orm_cache_decorator(
        fn: 'Creator[_T]'
    ) -> 'OrmCacheDescriptor[_T]': ...

    def orm_cache_decorator(fn: 'Creator[Any]') -> 'OrmCacheDescriptor[Any]':
        return OrmCacheDescriptor(policy, fn, by_role)
    return orm_cache_decorator
