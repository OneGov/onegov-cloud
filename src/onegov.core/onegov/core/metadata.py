""" Metadata about the instance, available through HTTP. """

import hashlib
import inspect
import morepath
import socket

from onegov.core.framework import Framework
from onegov.core.security import Public, Secret
from onegov.core.utils import dict_path
from webob import exc

# The metadata responses contain either public or public+secret responses,
# depending on the user's authorization. This simply controls the output
# of in the view though. Public properties may still load secret properties
# if they desire to do so. So this is not as much a security feature as it
# is a handy way to control the output.


def public_property(fn):
    fn.audience = 'public'
    return property(fn)


def secret_property(fn):
    fn.audience = 'secret'
    return property(fn)


class Metadata(object):

    def __init__(self, app, absorb=None):
        self.app = app
        self.absorb = absorb
        self.path = self.absorb and self.absorb.replace('/', '.')

    def for_audiences(self, *audiences):
        """ Returns a dict with the metadata for the given audience(s). """

        def pick(properties):
            for name, prop in properties:
                if not hasattr(prop, 'fget'):
                    continue

                audience = getattr(prop.fget, 'audience', None)

                if audience is None or audience not in audiences:
                    continue

                yield name, prop.fget(self)

        props = inspect.getmembers(self.__class__, inspect.isdatadescriptor)
        return dict(pick(props))

    @secret_property
    def fqdn(self):
        """ Returns the fqdn of the host running the site. """

        return socket.getfqdn()

    @secret_property
    def application_id(self):
        return self.app.application_id

    @public_property
    def identity(self):
        """ Each instance has a unqiue identity formed out of the hostname and
        the application id.

        """

        digest = hashlib.sha256()
        digest.update(self.fqdn.encode('utf-8'))
        digest.update(self.application_id.encode('utf-8'))
        return digest.hexdigest()


class PublicMetadata(Metadata):

    def as_dict(self):
        return super().for_audiences('public')


class SecretMetadata(Metadata):

    def as_dict(self):
        return super().for_audiences('public', 'secret')


@Framework.path(model=PublicMetadata, path='/metadata/public', absorb=True)
def get_public_metadata(app, absorb):
    return PublicMetadata(app, absorb)


@Framework.path(model=SecretMetadata, path='/metadata/secret', absorb=True)
def get_private_metadata(app, absorb):
    return SecretMetadata(app, absorb)


@Framework.json(model=PublicMetadata, permission=Public)
def view_public_metadata(self, request):
    return render_metadata(self, request)


@Framework.json(model=SecretMetadata, permission=Secret)
def view_secret_metadata(self, request):
    return render_metadata(self, request)


def render_metadata(self, request):
    data = self.as_dict()

    if self.path:
        try:
            response = morepath.Response(dict_path(data, self.path))
            response.content_type = 'text/plain'
            return response
        except KeyError:
            raise exc.HTTPNotFoundError()

    return morepath.render_json(data, request)
