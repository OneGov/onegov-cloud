from onegov.core.utils import normalize_for_url
from onegov.libres.models import Resource
from uuid import uuid4


class ResourceCollection(object):
    """ Manages a list of resources. Resources retrieved through this
    collection are bound to the scheduler associated with the libres_context
    passed to the collection.

    That means, you don't need to do this::

        collection.by_name('test').get_scheduler(libres_context)

    Instead, you can do this (with greater speed):

        collection.by_name('test').scheduler

    """
    def __init__(self, libres_context):
        self.libres_context = libres_context
        self.session = libres_context.get_service('session_provider').session()

    def query(self):
        return self.session.query(Resource)

    def bind_scheduler(self, resource):
        if resource:
            resource.scheduler = resource.get_scheduler(self.libres_context)
            return resource

    def add(self, title, timezone,
            meta={}, content={}, first_hour=7, last_hour=18):

        resource = Resource(
            id=uuid4(),
            name=normalize_for_url(title),
            title=title,
            timezone=timezone,
            meta=meta,
            content=content,
            first_hour=first_hour,
            last_hour=last_hour
        )

        self.session.add(resource)
        self.session.flush()

        return self.bind_scheduler(resource)

    def by_id(self, id):
        return self.bind_scheduler(
            self.query().filter(Resource.id == id).first())

    def by_name(self, name):
        return self.bind_scheduler(
            self.query().filter(Resource.name == name).first())
