from functools import cached_property
from logging import getLogger
from logging import NullHandler
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4
from sqlalchemy import Text
from typing_extensions import Self

from onegov.core.orm import Base
from onegov.core.orm.types import UUID, UTCDateTime
from onegov.user import User


from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from onegov.core import Framework
    from sqlalchemy.orm import Session
    from onegov.core.collection import PKType
    from onegov.core.collection import _M
    from onegov.core.types import PaginatedGenericCollection
    import uuid
    from datetime import datetime


log = getLogger('onegov.api')
log.addHandler(NullHandler())


class ApiException(Exception):
    """Base class for all API exceptions.

    Mainly used to ensure that all exceptions regarding the API are rendered
    with the correct content type.

    """

    def __init__(
        self,
        message: str = 'Internal Server Error',
        exception: Exception | None = None,
        status_code: int = 500,
        headers: dict[str, str] | None = None,
    ):
        self.message = (
            exception.message
            if exception and hasattr(exception, 'message') else message
        )
        self.status_code = (
            exception.status_code
            if exception and hasattr(exception, 'status_code') else status_code
        )

        self.headers = headers or {}

        if exception:
            log.exception(exception)


class ApiInvalidParamException(ApiException):
    def __init__(
        self, message: str = 'Invalid Parameter', status_code: int = 400
    ):
        self.message = message
        self.status_code = status_code


class ApiEndpointItem:
    """ A single instance of an item of a specific endpoint.

    Passes all functionality to the specific API endpoint and is mainly used
    for routing.

    """

    def __init__(self, app: 'Framework', endpoint: str, id: str):
        self.app = app
        self.endpoint = endpoint
        self.id = id

    @property
    def api_endpoint(self) -> 'ApiEndpoint | None':
        cls = ApiEndpointCollection(self.app).endpoints.get(self.endpoint)
        return cls(self.app) if cls else None

    @property
    def item(self) -> 'ApiEndpointItem | None':
        if self.api_endpoint:
            return self.api_endpoint.by_id(self.id)
        return None

    @property
    def data(self) -> dict[str, Any] | None:
        if self.api_endpoint:
            return self.api_endpoint.item_data(self.item)
        return None

    @property
    def links(self) -> dict[str, Any] | None:
        if self.api_endpoint:
            return self.api_endpoint.item_links(self.item)
        return None


class ApiEndpoint:
    """ An API endpoint.

    API endpoints wrap collection and do some filter mapping.

    To add a new endpoint, inherit from this class and provide the missing
    functions and properties at the bottom. Note that the collection is
    expected to be to provide the functionality of
    ``onegov.core.collection.Pagination``.

    """

    name: str = ''
    endpoint: str = ''
    filters: list[str] = []

    def __init__(
        self,
        app: 'Framework',
        extra_parameters: dict[str, 'str | int | None'] | None = None,
        page: int | None = None,
    ):
        self.app = app
        self.extra_parameters = extra_parameters or {}
        self.page = int(page) if page else page
        self.batch_size = 100

    def for_page(self, page: int | None) -> 'Self | None':
        """ Return a new endpoint instance with the given page while keeping
        the current filters.

        """

        return self.__class__(self.app, self.extra_parameters, page)

    def for_filter(self, **filters: Any) -> 'Self':
        """ Return a new endpoint instance with the given filters while
        discarding the current filters and page.

        """

        return self.__class__(self.app, filters)

    def for_item(self, item: 'ApiEndpointItem') -> 'ApiEndpointItem | None':
        """ Return a new endpoint item instance with the given item. """

        if not item:
            return None

        target = str(item)
        if hasattr(item, 'id'):
            target = getattr(item.id, 'hex', str(item.id))

        return ApiEndpointItem(self.app, self.endpoint, target)

    def get_filter(
        self, name: str, default: 'int | None' = None, empty: 'int | None' =
        None
    ) -> 'str | int | None':

        """Returns the filter value with the given name."""

        filter_value = self.extra_parameters.get(name)

        if filter_value is not None:
            return filter_value
        elif filter_value is None and default is not None:
            return default
        else:
            return empty

    def by_id(self, id: 'PKType') -> '_M | None':
        """ Return the item with the given ID from the collection. """

        try:
            return self.__class__(self.app).collection.by_id(id)
        except SQLAlchemyError:
            return None

    @property
    def session(self) -> 'Session':
        return self.app.session()

    @property
    def links(self) -> dict[str, 'Self | None']:
        """ Returns a dictionary with pagination instances. """

        result: dict[str, 'Self | None'] = {'prev': None, 'next': None}

        previous = self.collection.previous
        if previous:
            result['prev'] = self.for_page(previous.page)
        next_ = self.collection.next
        if next_:
            result['next'] = self.for_page(next_.page)
        return result

    @property
    def batch(self) -> dict['ApiEndpointItem | None', Any]:
        """ Returns a dictionary with endpoint item instances and their
        titles.

        """
        return {
            self.for_item(item): item
            for item in self.collection.batch
        }

    def item_data(self, item: 'ApiEndpointItem | None') -> dict[str, Any]:
        """ Return the data properties of the collection item as a dictionary.

        For example:
            {
                'name': 'Paul',
                'age': 40
            }

        """

        raise NotImplementedError()

    def item_links(self, item: 'ApiEndpointItem | None') -> dict[str, Any]:
        """ Return the link properties of the collection item as a dictionary.
        Links can either be string or a linkable object.

        For example:
            {
                'website': 'https://onegov.ch',
                'friends': FriendsApiEndpoint(app).for_item(paul),
                'home': ApiEndpointCollection(app)
            }

        """

        raise NotImplementedError()

    @property
    def collection(self) -> 'PaginatedGenericCollection[Any]':
        """ Return an instance of the collection with filters and page set.
        """

        raise NotImplementedError()


class ApiEndpointCollection:
    """ A collection of all available API endpoints. """

    def __init__(self, app: 'Framework'):
        self.app = app

    @cached_property
    def endpoints(self) -> dict[str, type[ApiEndpoint]]:
        return {
            endpoint.endpoint: endpoint
            for endpoint in self.app.config.setting_registry.api.endpoints
        }


class AuthEndpoint:

    def __init__(self, app: 'Framework'):
        self.app = app


class ApiKey(Base):

    __tablename__ = 'api_keys'

    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type: ignore[arg-type]
        nullable=False,
        primary_key=True,
        default=uuid4
    )

    # the user that created the api key
    user_id: 'Column[uuid.UUID]' = Column(
        UUID,  # type: ignore[arg-type]
        ForeignKey('users.id'),
        nullable=False
    )

    # the name of the api key, may be any string
    name: 'Column[str]' = Column(Text, nullable=False)

    # For now, we only support read-only api keys
    read_only: 'Column[bool]' = Column(Boolean, default=True, nullable=False)

    # the last time a token was generated based on this api key
    last_used: 'Column[datetime | None]' = Column(UTCDateTime, nullable=True)

    # the key itself
    key: 'Column[uuid.UUID]' = Column(
        UUID,  # type: ignore[arg-type]
        nullable=False,
        default=uuid4
    )

    user: 'relationship[User]' = relationship(
        User,
        backref=backref(
            'api_keys', cascade='all,delete-orphan', lazy='dynamic'
        )
    )
