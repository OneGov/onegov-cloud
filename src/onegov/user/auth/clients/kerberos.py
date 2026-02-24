from __future__ import annotations

import kerberos  # type:ignore
import os

from attr import attrs, attrib
from contextlib import contextmanager
from webob.exc import HTTPUnauthorized


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.request import CoreRequest
    from webob import Response


@attrs()
class KerberosClient:
    """ Kerberos is a computer-network authentication protocol that works on
    the basis of tickets to allow nodes communicating over a non-secure network
    to prove their identity to one another in a secure manner.

    """

    keytab: str = attrib()
    hostname: str = attrib()
    service: str = attrib()

    def try_configuration(self) -> None:
        """ Tries to use the configuration to get the principal.

        If this fails with an exception, the client was not configured
        corectly, so this is a good way to check for that.

        """
        with self.context():
            kerberos.getServerPrincipalDetails(self.service, self.hostname)

    @contextmanager
    def context(self) -> Iterator[None]:
        """ Runs the block inside the context manager with the keytab
        set to the provider's keytab.

        All functions that interact with kerberos must be run inside
        this context.

        For convenience, this context returns the kerberos module
        when invoked.

        """
        previous = os.environ.pop('KRB5_KTNAME', None)
        os.environ['KRB5_KTNAME'] = self.keytab

        try:
            yield
        finally:
            if previous is not None:
                os.environ['KRB5_KTNAME'] = previous

    def authenticated_username(
        self,
        request: CoreRequest
    ) -> Response | str | None:
        """ Authenticates the given request using Kerberos.

        The kerberos handshake is as follows:

        1. An HTTPUnauthorized response (401) is returned, with the
           WWW-Authenticate header set to "Negotiate"

        2. The client sends a request with the Authorization header set
           to the kerberos ticket.

        The result is an authenticated username or None. Note that this
        username is a username separate from our users table (in most cases).

        The kerberos environment defines this username and it is most likely
        the Windows login username.

        """

        # extract the token
        token = request.headers.get('Authorization')
        token = token and ''.join(token.split()[1:]).strip()

        def with_header(
            response: Response,
            include_token: bool = True
        ) -> Response:
            if include_token and token:
                negotiate = f'Negotiate {token}'
            else:
                negotiate = 'Negotiate'

            response.headers['WWW-Authenticate'] = negotiate

            return response

        def negotiate() -> Response:
            # only mirror the token back, if it is valid, which is never
            # the case in the negotiate step
            return with_header(HTTPUnauthorized(), include_token=False)

        # ask for a token
        if not token:
            return negotiate()

        # verify the token
        with self.context():

            # initialization step
            result, state = kerberos.authGSSServerInit(self.service)

            if result != kerberos.AUTH_GSS_COMPLETE:
                return negotiate()

            # challenge step
            result = kerberos.authGSSServerStep(state, token)

            if result != kerberos.AUTH_GSS_COMPLETE:
                return negotiate()

            # extract the final token
            token = kerberos.authGSSServerResponse(state)

            # include the token in the response
            request.after(with_header)

            # extract the user if possible
            return kerberos.authGSSServerUserName(state) or None
