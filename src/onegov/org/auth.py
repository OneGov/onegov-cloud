from __future__ import annotations

import morepath

from onegov.core.utils import relative_url
from onegov.org import _, log
from onegov.user.collections import TANCollection
from onegov.user.models import TAN
from sedate import utcnow


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.app import OrgApp
    from onegov.org.request import OrgRequest
    from webob import Response


class MTANAuth:
    """
    Defines a model for mTAN authentication views.

    This is similar in functionality to :class:`onegov.user.auth.core.Auth`
    but it is not tied to a specific user, instead we just remember whether
    or not we're still authenticated using the browser session.

    Even with multiple active sessions, logically we treat all sessions for
    the same phone number as one session, i.e. access limits apply to all
    browser sessions that are tied to that specific number.

    """

    def __init__(self, app: OrgApp, to: str = '/'):
        self.app = app
        self.session = app.session()
        self.application_id = app.application_id
        self.to = relative_url(to)

    def send_mtan(self, request: OrgRequest, number: str) -> Response:

        # we are already authenticated just redirect to the page we wanted
        if request.active_mtan_session:
            return morepath.redirect(request.transform(self.to))

        collection = TANCollection(self.session, scope='mtan_access')
        client = request.client_addr or 'unknown'
        obj = collection.add(
            client=client,
            mobile_number=number,
            redirect_to=self.to
        )
        authenticate_url = request.link(self, 'auth')
        self.app.send_sms(number, request.translate(_(
            '${mtan} - mTAN for ${organisation}.'
            '\n'
            'Or continue here: ${url}',
            mapping={
                'organisation': self.app.org.title,
                'mtan': obj.tan,
                # keep the url in the sms short
                'url': authenticate_url.rsplit('?', 1)[0] + f'?tan={obj.tan}'
            }
        )))
        request.info(_(
            'We sent an mTAN to the specified number. '
            'Please enter it below or follow the instructions in the SMS.'
        ))
        return morepath.redirect(authenticate_url)

    def authenticate(
        self,
        request: OrgRequest,
        tan: str,
    ) -> str | None:

        # we are already authenticated
        if request.active_mtan_session:
            return self.to

        collection = TANCollection(self.session, scope='mtan_access')
        result = collection.by_tan(tan)
        if result is None or 'mobile_number' not in result.meta:
            client = request.client_addr or 'unknown'
            log.info(f'Failed login by {client} (mTAN)')
            return None

        # record date and number in session
        request.browser_session.mtan_verified = utcnow()
        request.browser_session.mtan_number = mobile_number = result.meta[
            'mobile_number']

        # expire the TAN we just used
        result.expire()

        # expire any other TANs issued to the same mobile number
        for tan_obj in collection.query().filter(
            TAN.meta['mobile_number'] == mobile_number
        ):
            tan_obj.expire()
        return result.meta.get('redirect_to', self.to)
