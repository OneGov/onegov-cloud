from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from functools import cached_property
from json import JSONDecodeError
from logging import getLogger
from logging import NullHandler
from onegov.core.orm import Base
from onegov.form.fields import HoneyPotField
from onegov.form.utils import get_fields_from_class
from onegov.user import User
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4, UUID
from webob.exc import HTTPException
from webob.multidict import MultiDict
from wtforms import HiddenField


from typing import TYPE_CHECKING, Any, ClassVar, NoReturn, Self, overload
if TYPE_CHECKING:
    from collections.abc import Collection, Iterator, Mapping
    from onegov.core import Framework
    from onegov.core.collection import PKType
    from onegov.core.request import CoreRequest
    from onegov.form import Form
    from sqlalchemy.orm import DeclarativeBase, Query, Session
    from typing import Protocol
    from webob.request import _FieldStorageWithFile

    class PaginationWithById[
        M: DeclarativeBase,
        IdT: UUID | str | int
    ](Protocol):
        def by_id(self, id: IdT) -> M | None: ...

        # Pagination:
        batch_size: int

        def subset(self) -> Query[M]: ...
        @property
        def cached_subset(self) -> Query[M]: ...
        @property
        def page(self) -> int | None: ...
        @property
        def page_index(self) -> int: ...
        def page_by_index(self, index: int) -> Self: ...
        @property
        def subset_count(self) -> int: ...
        @property
        def batch(self) -> tuple[M, ...]: ...
        @property
        def offset(self) -> int: ...
        @property
        def pages_count(self) -> int: ...
        @property
        def pages(self) -> Iterator[Self]: ...
        @property
        def previous(self) -> Self | None: ...
        @property
        def next(self) -> Self | None: ...

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
        status_code: int = 500,
        headers: dict[str, str] | None = None,
    ):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.headers = headers or {}

    @classmethod
    @contextmanager
    def capture_exceptions(
        cls,
        default_message: str = 'Internal Server Error',
        default_status_code: int = 500,
        headers: dict[str, str] | None = None,
        exception_type: type[Exception] = Exception,
    ) -> Iterator[None]:
        try:
            yield
        except exception_type as exc:
            # NOTE: log unexpected exceptions
            if (
                exception_type is Exception
                and not isinstance(exc, (HTTPException, ApiException))
            ):
                log.exception('Captured OneGov API Exception')

            message = getattr(exc, 'message',
                getattr(exc, 'title', default_message)
            )
            status_code = getattr(exc, 'status_code', default_status_code)
            raise cls(message, status_code, headers) from exc


class ApiInvalidParamException(ApiException):
    def __init__(
        self, message: str = 'Invalid Parameter', status_code: int = 400
    ):
        self.message = message
        self.status_code = status_code


class ApiEndpointItem[M: DeclarativeBase]:
    """ A single instance of an item of a specific endpoint.

    Passes all functionality to the specific API endpoint and is mainly used
    for routing.

    """

    def __init__(self, request: CoreRequest, endpoint: str, id: str):
        self.request = request
        self.app = request.app
        self.endpoint = endpoint
        self.id = id

    @cached_property
    def api_endpoint(self) -> ApiEndpoint[M] | None:
        endpoint = ApiEndpointCollection(
            self.request).endpoints.get(self.endpoint)
        return endpoint if endpoint else None

    @cached_property
    def item(self) -> M | None:
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

    def form(self, request: CoreRequest) -> Form | None:
        if self.api_endpoint and (item := self.item):
            return self.api_endpoint.form(item, request)

        return None


class ApiEndpoint[M: DeclarativeBase]:
    """ An API endpoint.

    API endpoints wrap collection and do some filter mapping.

    To add a new endpoint, inherit from this class and provide the missing
    functions and properties at the bottom. Note that the collection is
    expected to be to provide the functionality of
    ``onegov.core.collection.Pagination``.

    """

    endpoint: str = ''
    form_class: ClassVar[type[Form] | None] = None

    def __init__(
        self,
        request: CoreRequest,
        extra_parameters: dict[str, list[str]] | None = None,
        page: int | None = None,
    ):
        self.request = request
        self.app = request.app
        self.extra_parameters = extra_parameters or {}
        self.page = int(page) if page else page
        self.batch_size = 100

    @cached_property
    def filters(self) -> Mapping[str, Collection[str] | str | None]:
        """ A mapping of the available filter params to their corresponding
        description or a collection of possible values. If possible values
        are specified it is assumed that the filter can be specfied multiple
        times.

        The description is optional and should only be used for non-trivial
        filters that don't just accept arbitrary strings.

        """
        return {}

    @property
    def title(self) -> str | None:
        """ Return a human readable title for this endpoint """
        return None

    @property
    def description(self) -> str | None:
        """ Return a human readable description for this endpoint """
        return None

    def for_page(self, page: int | None) -> Self | None:
        """ Return a new endpoint instance with the given page while keeping
        the current filters.

        """

        return self.__class__(self.request, self.extra_parameters, page)

    def for_filter(self, **filters: list[str]) -> Self:
        """ Return a new endpoint instance with the given filters while
        discarding the current filters and page.

        """

        return self.__class__(self.request, filters)

    @overload
    def for_item(self, item: None) -> None: ...
    @overload
    def for_item(self, item: M) -> ApiEndpointItem[M]: ...

    def for_item(self, item: M | None) -> ApiEndpointItem[M] | None:
        """ Return a new endpoint item instance with the given item. """

        if not item:
            return None

        assert hasattr(item, 'id')
        return self.for_item_id(item.id)

    @overload
    def for_item_id(self, item_id: None) -> None: ...
    @overload
    def for_item_id(self, item_id: Any) -> ApiEndpointItem[M]: ...

    def for_item_id(self, item_id: Any | None) -> ApiEndpointItem[M] | None:
        """ Return a new endpoint item instance with the given item id. """

        if not item_id:
            return None

        target = getattr(item_id, 'hex', str(item_id))
        return ApiEndpointItem(self.request, self.endpoint, target)

    def scalarize_value(
        self,
        name: str,
        values: list[str] | None = None
    ) -> str | None:
        if values is None:
            values = self.extra_parameters.get(name)

        if not values:
            return None

        if len(values) > 1:
            raise ApiInvalidParamException(
                f'Url parameter {name!r} may only be specified once.'
            )
        return values[0]

    @overload
    def get_filter[T1, T2](
        self,
        name: str,
        default: T1,
        empty: T2
    ) -> str | T1 | T2: ...

    @overload
    def get_filter[T](
        self,
        name: str,
        default: T,
        empty: None = None
    ) -> str | T | None: ...

    @overload
    def get_filter[T](
        self,
        name: str,
        default: None = None,
        *,
        empty: T
    ) -> str | T | None: ...

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

        """Returns the scalar filter value with the given name."""

        if name not in self.extra_parameters:
            return default
        return self.scalarize_value(name) or empty

    def by_id(self, id: PKType) -> M | None:
        """ Return the item with the given ID from the collection. """

        try:
            return self.__class__(self.request).collection.by_id(id)
        except SQLAlchemyError:
            return None

    @property
    def session(self) -> Session:
        return self.app.session()

    @property
    def links(self) -> dict[str, Self | None]:
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
    def batch(self) -> dict[ApiEndpointItem[M], M]:
        """ Returns a dictionary with endpoint item instances and their
        titles.

        """
        return {
            self.for_item(item): item
            for item in self.collection.batch
        }

    def item_data(self, item: M) -> dict[str, Any]:
        """ Return the data properties of the collection item as a dictionary.

        For example::

            {
                'name': 'Paul',
                'age': 40
            }

        """

        raise NotImplementedError()

    def item_links(self, item: M) -> dict[str, Any]:
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
        item: M | None,
        request: CoreRequest
    ) -> Form | None:
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
            with ApiException.capture_exceptions(
                exception_type=JSONDecodeError,
                default_message='Malformed payload',
                default_status_code=400,
            ):
                json_data = request.json

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
                    raise ApiException(
                        f'{name}: Unsupported value format', status_code=400
                    )

        else:
            formdata = None

        return request.get_form(
            self.form_class,
            csrf_support=False,
            formdata=formdata,
            model=item
        )

    def apply_changes(self, item: M, form: Any) -> None:
        """ Apply the changes to the item based on the given form data. """

        raise NotImplementedError()

    @property
    def collection(self) -> PaginationWithById[M, Any]:
        """ Return an instance of the collection with filters and page set.
        """

        raise NotImplementedError()

    def assert_valid_filter(self, param: str) -> None:
        if param not in self.filters:
            raise ApiInvalidParamException(
                f'Invalid url parameter {param!r}. Valid params are: '
                f'{", ".join(sorted(self.filters))}')

    # HACK: This gets around the fact that extra_parameters only
    #       supports scalar values, but we want to support lists
    #       of values for extra_parameters.
    def __link_alias__(self) -> str:
        return self.request.class_link(
            self.__class__,
            {
                'endpoint': self.endpoint,
                'page': self.page,
            },
            query_params=MultiDict(
                (key, value)
                for key, values in self.extra_parameters.items()
                for value in values
            )
        )


class ApiEndpointCollection:
    """ A collection of all available API endpoints. """

    def __init__(self, request: CoreRequest):
        self.request = request
        self.app = request.app

    @cached_property
    def endpoints(self) -> dict[str, ApiEndpoint[Any]]:
        return {
            endpoint.endpoint: endpoint
            for endpoint in self.app.config.setting_registry.api.endpoints(
                request=self.request
            )
        }

    def get_endpoint(
            self,
            name: str,
            page: int = 0,
            extra_parameters: dict[str, list[str]] | None = None
    ) -> ApiEndpoint[Any] | None:
        endpoints = self.app.config.setting_registry.api.endpoints(
            request=self.request,
            extra_parameters=extra_parameters,
            page=page
        )
        return next((
            endpoint for endpoint in endpoints
            if endpoint.endpoint == name
        ), None)


class AuthEndpoint:
    """ This is a Dummy, because morepath requires a model for linking. """

    def __init__(self, app: Framework):
        self.app = app


class ApiKey(Base):

    __tablename__ = 'api_keys'

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the id of the user that created the api key
    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'))

    #: the user that created the api key
    user: Mapped[User] = relationship(back_populates='api_keys')

    #: the name of the api key, may be any string
    name: Mapped[str]

    #: whether or not the api key can submit changes
    read_only: Mapped[bool] = mapped_column(default=True)

    #: the last time a token was generated based on this api key
    last_used: Mapped[datetime | None]

    #: the key itself
    key: Mapped[UUID] = mapped_column(default=uuid4)
