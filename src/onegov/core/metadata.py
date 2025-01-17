""" Metadata about the instance, available through HTTP. """
from __future__ import annotations

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


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from .request import CoreRequest

    # NOTE: For the purposes of type checking we treat them like
    #       regular properties, that way we get support for all
    #       the property features without having to implement a
    #       complete Protocol that implements all the features
    #
    #       Technically it isn't quite correct, since we can't
    #       use the full property constructor with these, but
    #       it's good enough for now...
    public_property = secret_property = property  # noqa: TC009

else:
    def public_property(fn: Callable[[Any], Any]) -> property:
        fn.audience = 'public'
        return property(fn)

    def secret_property(fn: Callable[[Any], Any]) -> property:
        fn.audience = 'secret'
        return property(fn)


class Metadata:

    def __init__(self, app: Framework, absorb: str | None = None):
        self.app = app
        self.absorb = absorb
        self.path = self.absorb and self.absorb.replace('/', '.')

    def for_audiences(
        self,
        *audiences: Literal['public', 'secret']
    ) -> dict[str, Any]:
        """ Returns a dict with the metadata for the given audience(s). """

        def pick(
            properties: list[tuple[str, Any]]
        ) -> Iterator[tuple[str, Any]]:

            for name, prop in properties:
                if not hasattr(prop, 'fget'):
                    continue

                audience = getattr(prop.fget, 'audience', None)

                if audience is None or audience not in audiences:
                    continue

                assert prop.fget is not None
                yield name, prop.fget(self)

        props = inspect.getmembers(self.__class__, inspect.isdatadescriptor)
        return dict(pick(props))

    @secret_property
    def fqdn(self) -> str:
        """ Returns the fqdn of the host running the site. """

        return socket.getfqdn()

    @secret_property
    def application_id(self) -> str:
        return self.app.application_id

    @public_property
    def identity(self) -> str:
        """ Each instance has a unqiue identity formed out of the hostname and
        the application id.

        """

        digest = hashlib.sha256()
        digest.update(self.fqdn.encode('utf-8'))
        digest.update(self.application_id.encode('utf-8'))
        return digest.hexdigest()


class PublicMetadata(Metadata):

    def as_dict(self) -> dict[str, Any]:
        return super().for_audiences('public')


class SecretMetadata(Metadata):

    def as_dict(self) -> dict[str, Any]:
        return super().for_audiences('public', 'secret')


@Framework.path(model=PublicMetadata, path='/metadata/public', absorb=True)
def get_public_metadata(app: Framework, absorb: str) -> PublicMetadata:
    return PublicMetadata(app, absorb)


@Framework.path(model=SecretMetadata, path='/metadata/secret', absorb=True)
def get_private_metadata(app: Framework, absorb: str) -> SecretMetadata:
    return SecretMetadata(app, absorb)


@Framework.json(model=PublicMetadata, permission=Public)
def view_public_metadata(
    self: PublicMetadata,
    request: CoreRequest
) -> morepath.Response:
    return render_metadata(self, request)


@Framework.json(model=SecretMetadata, permission=Secret)
def view_secret_metadata(
    self: PublicMetadata,
    request: CoreRequest
) -> morepath.Response:
    return render_metadata(self, request)


def render_metadata(
    self: PublicMetadata | SecretMetadata,
    request: CoreRequest
) -> morepath.Response:

    data = self.as_dict()

    if self.path:
        try:
            response = morepath.Response(dict_path(data, self.path))
            response.content_type = 'text/plain'
            return response
        except KeyError as exception:
            raise exc.HTTPNotFound() from exception

    return morepath.render_json(data, request)
