from cached_property import cached_property


class ApiEndpointCollection:

    def __init__(self, app):
        self.app = app

    @cached_property
    def endpoints(self):
        return {
            endpoint.endpoint: endpoint
            for endpoint in self.app.config.setting_registry.api.endpoints
        }


class ApiEndpoint:

    def __init__(self, app, extra_parameters=None, order=None, page=None):
        self.app = app
        self.extra_parameters = extra_parameters
        self.order = order
        self.page = int(page) if page else page
        self.batch_size = 100

    @property
    def session(self):
        return self.app.session()

    def get_filter(self, name):
        return self.extra_parameters.get(name, None)

    def next(self, request):
        page = self.collection.next
        if page:
            return request.link(
                self.__class__(
                    self.app, self.extra_parameters, self.order, page.page
                )
            )

    def previous(self, request):
        page = self.collection.previous
        if page:
            return request.link(
                self.__class__(
                    self.app, self.extra_parameters, self.order, page.page
                )
            )

    def query(self, request):
        id_ = self.get_filter('id')
        if id_:
            item = self.by_id(id_)
            return {'items': [self.json(item, request, False)]}

        collection = self.collection
        return {
            'links': {
                'previous': self.previous(request),
                'next': self.next(request),
            },
            'items': [self.json(item, request) for item in collection.batch]
        }

    @classmethod
    def json(cls, item, request, compact=False):
        raise NotImplementedError()

    def by_id(self, id_):
        raise NotImplementedError()

    @property
    def collection(self):
        raise NotImplementedError()
