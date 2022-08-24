from cached_property import cached_property
from logging import getLogger
from logging import NullHandler


log = getLogger('onegov.api')
log.addHandler(NullHandler())


class ApiExcpetion(Exception):

    """ Base class for all API exceptions.

    Mainly used to ensure that all exceptions regarding the API are rendered
    with the correct content type.

    """

    def __init__(self, message='', exception=None, status_code=400,
                 headers=None):
        self.message = message
        self.status_code = status_code
        self.headers = headers or {}
        if exception:
            log.exception(exception)
            self.status_code = 500
            self.message = 'Internal Server Error'


class ApiEndpointCollection:

    """ A collection of all available API endpoints. """

    def __init__(self, app):
        self.app = app

    @cached_property
    def endpoints(self):
        return {
            endpoint.endpoint: endpoint
            for endpoint in self.app.config.setting_registry.api.endpoints
        }


class ApiEndpointItem:

    """ A single instance of an item of a specific endpoint.

    Passes all functionality to the specific API endpoint and is mainly used
    for routing.

    """

    def __init__(self, app, endpoint, id):
        self.app = app
        self.endpoint = endpoint
        self.id = id

    @property
    def api_endpoint(self):
        cls = ApiEndpointCollection(self.app).endpoints.get(self.endpoint)
        return cls(self.app)

    @property
    def item(self):
        return self.api_endpoint.by_id(self.id)

    @property
    def data(self):
        return self.api_endpoint.item_data(self.item)

    @property
    def links(self):
        return self.api_endpoint.item_links(self.item)


class ApiEndpoint:

    """ An API endpoint.

    API endpoints wrap collection and do some filter mapping.

    To add a new endpoint, inherit from this class and provide the missing
    functions and properties at the bottom. Note that the collection is
    expected to be to provide the functionality of
    ``onegov.core.collection.Pagination``.

    """

    name = ''
    filters = []

    def __init__(self, app, extra_parameters=None, page=None):
        self.app = app
        self.extra_parameters = extra_parameters or {}
        self.page = int(page) if page else page
        self.batch_size = 100

    def for_page(self, page):
        """ Return a new endpoint instance with the given page while keeping
        the current filters.

        """

        return self.__class__(self.app, self.extra_parameters, page)

    def for_filter(self, **filters):
        """ Return a new endpoint instance with the given filters while
        discarding the current filters and page.

        """

        return self.__class__(self.app, filters)

    def for_item(self, item):
        """ Return a new endpoint item instance with the given item. """

        if not item:
            return

        return ApiEndpointItem(
            self.app,
            self.endpoint,
            getattr(item.id, 'hex', str(item.id))
        )

    def get_filter(self, name):
        """ Returns the filter value with the given name. """

        return (self.extra_parameters or {}).get(name, None)

    def by_id(self, id_):
        """ Return the item with the given ID from the collection. """

        return self.__class__(self.app).collection.by_id(id_)

    @property
    def session(self):
        return self.app.session()

    def item_title(self, item):
        """ Return the title of the collection item. """

        return getattr(item, 'title', '')

    @property
    def links(self):
        """ Returns a dictionary with pagination instances. """

        result = {'prev': None, 'next': None}
        if self.collection.previous:
            result['prev'] = self.for_page(self.collection.previous.page)
        if self.collection.next:
            result['next'] = self.for_page(self.collection.next.page)
        return result

    @property
    def batch(self):
        """ Returns a dictionary with endpoint item instances and their
        titles.

        """

        return {
            self.for_item(item): self.item_title(item)
            for item in self.collection.batch
        }

    def item_data(self, item):
        """ Return the data properties of the collection item as a dictionary.

        For example:
            {
                'name': 'Paul',
                'age': 40
            }

        """

        raise NotImplementedError()

    def item_links(self, item):
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
    def collection(self):
        """ Return an instance of the collection with filters and page set.
        """

        raise NotImplementedError()
