from functools import cached_property
from json import JSONDecodeError
from logging import getLogger
from logging import NullHandler
from onegov.core.collection import _M
from onegov.core.orm import Base
from onegov.core.orm.types import UUID, UTCDateTime
from onegov.form.fields import HoneyPotField
from onegov.form.utils import get_fields_from_class
from onegov.user import User
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4
from webob.multidict import MultiDict
from wtforms import HiddenField


from typing import TYPE_CHECKING, Any, ClassVar, Generic, NoReturn, overload
if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterator
    from datetime import datetime
    from onegov.core import Framework
    from onegov.core.collection import PKType
    from onegov.core.request import CoreRequest
    from onegov.form import Form
    from sqlalchemy.orm import Query, Session
    from typing import Protocol, Self, TypeVar
    from webob.request import _FieldStorageWithFile

    _DefaultT = TypeVar('_DefaultT')
    _EmptyT = TypeVar('_EmptyT')
    _IdT = TypeVar('_IdT', bound=uuid.UUID | str | int, contravariant=True)

    class PaginationWithById(Protocol[_M, _IdT]):
        def by_id(self, id: _IdT) -> _M | None: ...

        # Pagination:
        batch_size: int
        def subset(self) -> Query[_M]: ...
        @property
        def cached_subset(self) -> Query[_M]: ...
        @property
        def page(self) -> int | None: ...
        @property
        def page_index(self) -> int: ...
        def page_by_index(self, index: int) -> 'Self': ...
        @property
        def subset_count(self) -> int: ...
        @property
        def batch(self) -> tuple[_M, ...]: ...
        @property
        def offset(self) -> int: ...
        @property
        def pages_count(self) -> int: ...
        @property
        def pages(self) -> 'Iterator[Self]': ...
        @property
        def previous(self) -> 'Self | None': ...
        @property
        def next(self) -> 'Self | None': ...

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


class ApiEndpointItem(Generic[_M]):
    """ A single instance of an item of a specific endpoint.

    Passes all functionality to the specific API endpoint and is mainly used
    for routing.

    """

    def __init__(self, app: 'Framework', endpoint: str, id: str):
        self.app = app
        self.endpoint = endpoint
        self.id = id

    @cached_property
    def api_endpoint(self) -> 'ApiEndpoint[_M] | None':
        cls = ApiEndpointCollection(self.app).endpoints.get(self.endpoint)
        # type(cls(self.app)) == <class 'onegov.agency.api.AgencyApiEndpoint'>
        return cls(self.app) if cls else None

    @cached_property
    def item(self) -> _M | None:
        if self.api_endpoint:
            return self.api_endpoint.by_id(self.id)  # for. ex. ExtendedAgency
        return None

    @property
    def data(self) -> dict[str, Any] | None:
        if self.api_endpoint and (item := self.item):
            return self.api_endpoint.item_data(item)
        return None

    @property
    def links(self) -> dict[str, Any] | None:
        if self.api_endpoint and (item := self.item):
            return self.api_endpoint.item_links(item)
        return None

    def form(self, request: 'CoreRequest') -> 'Form | None':
        if self.api_endpoint and (item := self.item):
            return self.api_endpoint.form(item, request)

        return None


class ApiEndpoint(Generic[_M]):
    """ An API endpoint.

    API endpoints wrap collection and do some filter mapping.

    To add a new endpoint, inherit from this class and provide the missing
    functions and properties at the bottom. Note that the collection is
    expected to be to provide the functionality of
    ``onegov.core.collection.Pagination``.

    """

    name: ClassVar[str] = ''  # FIXME: Do we ever use this?
    endpoint: ClassVar[str] = ''
    filters: ClassVar[set[str]] = set()
    form_class: ClassVar[type['Form'] | None] = None

    def __init__(
        self,
        app: 'Framework',
        extra_parameters: dict[str, str | None] | None = None,
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

    @overload
    def for_item(self, item: None) -> None: ...
    @overload
    def for_item(self, item: _M) -> 'ApiEndpointItem[_M]': ...

    def for_item(self, item: _M | None) -> 'ApiEndpointItem[_M] | None':
        """ Return a new endpoint item instance with the given item. """

        if not item:
            return None

        target = str(item)
        if hasattr(item, 'id'):
            target = getattr(item.id, 'hex', str(item.id))

        return ApiEndpointItem(self.app, self.endpoint, target)

    @overload
    def get_filter(
        self,
        name: str,
        default: '_DefaultT',
        empty: '_EmptyT'
    ) -> 'str | _DefaultT | _EmptyT': ...

    @overload
    def get_filter(
        self,
        name: str,
        default: '_DefaultT',
        empty: None = None
    ) -> 'str | _DefaultT | None': ...

    @overload
    def get_filter(
        self,
        name: str,
        default: None = None,
        *,
        empty: '_EmptyT'
    ) -> 'str | _EmptyT | None': ...

    @overload
    def get_filter(
        self,
        name: str,
        default: None = None,
        empty: None = None
    ) -> str | None: ...

    def get_filter(
        self,
        name: str,
        default: Any | None = None,
        empty: Any | None = None
    ) -> Any | None:

        """Returns the filter value with the given name."""

        if name not in self.extra_parameters:
            return default
        return self.extra_parameters[name] or empty

    def by_id(self, id: 'PKType') -> _M | None:
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

        result: dict[str, Self | None] = {'prev': None, 'next': None}

        previous = self.collection.previous
        if previous:
            result['prev'] = self.for_page(previous.page)
        next_ = self.collection.next
        if next_:
            result['next'] = self.for_page(next_.page)
        return result

    @property
    def batch(self) -> dict['ApiEndpointItem[_M]', _M]:
        """ Returns a dictionary with endpoint item instances and their
        titles.

        """
        return {
            self.for_item(item): item
            for item in self.collection.batch
        }

    def item_data(self, item: _M) -> dict[str, Any]:
        """ Return the data properties of the collection item as a dictionary.

        For example::

            {
                'name': 'Paul',
                'age': 40
            }

        """

        raise NotImplementedError()

    def item_links(self, item: _M) -> dict[str, Any]:
        """ Return the link properties of the collection item as a dictionary.
        Links can either be string or a linkable object.

        For example::

            {
                'website': 'https://onegov.ch',
                'friends': FriendsApiEndpoint(app).for_item(paul),
                'home': ApiEndpointCollection(app)
            }

        """

        raise NotImplementedError()

    def form(
        self,
        item: _M | None,
        request: 'CoreRequest'
    ) -> 'Form | None':
        """ Return a form for editing items of this collection. """

        if self.form_class is None:
            return None

        def malformed_payload() -> NoReturn:
            raise ApiException(
                'Malformed collection+json payload',
                status_code=400
            )

        # NOTE: In addition to form encoded data we also allow a JSON
        #       payload, although the support for this is currenty
        #       very limited
        formdata: MultiDict[str, str | _FieldStorageWithFile] | None
        if request.method in ('POST', 'PUT') and not request.POST:
            settable_fields = {
                name
                for name, field in get_fields_from_class(self.form_class)
                if not issubclass(
                    field.field_class,
                    (HiddenField, HoneyPotField)
                )
            }
            formdata = MultiDict()
            try:
                json_data = request.json
            except JSONDecodeError as e:
                raise ApiException('Malformed payload', status_code=400) from e

            if not isinstance(json_data, dict):
                malformed_payload()

            data_list = json_data.get('template', {}).get('data')
            if not isinstance(data_list, list):
                malformed_payload()

            for field in data_list:
                if not isinstance(field, dict):
                    malformed_payload()

                name = field.get('name')
                if not isinstance(name, str):
                    malformed_payload()

                if name not in settable_fields:
                    raise ApiException(
                        f'Invalid field "{name}" supplied', status_code=400
                    )

                # TOOD: It would be more robust to use something like pydantic
                #       for parsing/validating the JSON payload, rather than
                #       try to convert the JSON to formdata. For now the only
                #       form we support only has text data, so keep it simple.
                value = field.get('value')
                if value is None:
                    continue
                elif isinstance(value, (str, int, float)):
                    formdata[name] = str(value)
                else:
                    raise ApiException(f'{name}: Unsupported value format')

        else:
            formdata = None

        return request.get_form(
            self.form_class,
            csrf_support=False,
            formdata=formdata,
            model=item
        )

    def apply_changes(self, item: _M, form: Any) -> None:
        """ Apply the changes to the item based on the given form data. """

        raise NotImplementedError()

    @property
    def collection(self) -> 'PaginationWithById[_M, Any]':
        """ Return an instance of the collection with filters and page set.
        """

        raise NotImplementedError()

    def assert_valid_filter(self, param: str) -> None:
        if param not in self.filters:
            raise ApiInvalidParamException(
                f"Invalid url parameter '{param}'. Valid params are: "
                f'{", ".join(sorted(self.filters))}')


class ApiEndpointCollection:
    """ A collection of all available API endpoints. """

    def __init__(self, app: 'Framework'):
        self.app = app

    @cached_property
    def endpoints(self) -> dict[str, type[ApiEndpoint[Any]]]:
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

    #: the id of the user that created the api key
    user_id: 'Column[uuid.UUID]' = Column(
        UUID,  # type: ignore[arg-type]
        ForeignKey('users.id'),
        nullable=False
    )

    #: the user that created the api key
    user: 'relationship[User]' = relationship(
        User,
        backref=backref(
            'api_keys', cascade='all,delete-orphan', lazy='dynamic'
        )
    )

    #: the name of the api key, may be any string
    name: 'Column[str]' = Column(Text, nullable=False)

    #: whether or not the api key can submit changes
    read_only: 'Column[bool]' = Column(Boolean, default=True, nullable=False)

    #: the last time a token was generated based on this api key
    last_used: 'Column[datetime | None]' = Column(UTCDateTime, nullable=True)

    #: the key itself
    key: 'Column[uuid.UUID]' = Column(
        UUID,  # type: ignore[arg-type]
        nullable=False,
        default=uuid4
    )
