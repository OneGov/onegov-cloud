from cached_property import cached_property


class ApiExcpetion(Exception):

    def __init__(self, message='', exception=None, status_code=400,
                 headers=None):
        self.message = message
        self.status_code = status_code
        self.headers = headers or {}
        if exception and not message:
            self.message = (
                getattr(exception, 'message', '')
                or str(exception)
                or repr(exception)
            )


class ApiEndpointCollection:

    def __init__(self, app):
        self.app = app

    @cached_property
    def endpoints(self):
        return {
            endpoint.endpoint: endpoint
            for endpoint in self.app.config.setting_registry.api.endpoints
        }


class ApiEndpointItem:

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

    name = ''
    filters = []

    def __init__(self, app, extra_parameters=None, page=None):
        self.app = app
        self.extra_parameters = extra_parameters
        self.page = int(page) if page else page
        self.batch_size = 100

    def for_page(self, page):
        return self.__class__(self.app, self.extra_parameters, page)

    def for_filter(self, **extra_parameters):
        return self.__class__(self.app, extra_parameters)

    def for_item(self, item):
        if not item:
            return
        return ApiEndpointItem(
            self.app,
            self.endpoint,
            getattr(item.id, 'hex', str(item.id))
        )

    def get_filter(self, name):
        return (self.extra_parameters or {}).get(name, None)

    @property
    def collection(self):
        raise NotImplementedError()

    def by_id(self, id_):
        return self.__class__(self.app).collection.by_id(id_)

    @property
    def session(self):
        return self.app.session()

    def item_title(self, item):
        return item.title

    def item_data(self, item):
        raise NotImplementedError()

    def item_links(self, item):
        raise NotImplementedError()

    @property
    def links(self):
        result = {}
        if self.collection.next:
            result['next'] = self.for_page(self.collection.next.page)
        if self.collection.previous:
            result['prev'] = self.for_page(self.collection.previous.page)
        return result

    @property
    def batch(self):
        return {
            self.for_item(item): self.item_title(item)
            for item in self.collection.batch
        }
