""" Newsletter subscription management. """
from __future__ import annotations

import morepath

from morepath.request import Response
from onegov.core.security import Public
from onegov.newsletter import NewsletterCollection, Subscription
from onegov.org import _, OrgApp, log

from typing import TYPE_CHECKING

from onegov.org.mail import send_transactional_html_mail

if TYPE_CHECKING:
    from onegov.org.request import OrgRequest
    from webob import Response as BaseResponse


# use an english name for this view, so robots know what we use it for
@OrgApp.view(model=Subscription, name='confirm', permission=Public)
def view_confirm(self: Subscription, request: OrgRequest) -> BaseResponse:
    if self.confirm():
        request.success(_(
            'the subscription for ${address} was successfully confirmed',
            mapping={'address': self.recipient.address}
        ))
    else:
        request.alert(_(
            'the subscription for ${address} could not be confirmed, '
            'wrong token',
            mapping={'address': self.recipient.address}
        ))

    return morepath.redirect(
        request.link(NewsletterCollection(request.session))
    )


# use an english name for this view, so robots know what we use it for
@OrgApp.view(model=Subscription, name='unsubscribe', permission=Public)
def view_unsubscribe(
    self: Subscription,
    request: OrgRequest
) -> BaseResponse:

    address = self.recipient.address

    # RFC-8058: just return an empty response on a POST request
    # don't check for success
    if request.method == 'POST':
        log.debug(f'Unsubscribed POST: {address}')
        self.unsubscribe()
        return Response()

    if self.unsubscribe():
        request.success(_(
            'You have successfully unsubscribed from the newsletter '
            'at ${address}',
            mapping={'address': address}
        ))

        log.debug(f'Unsubscribed: {address}')

        # check if admin wants an email for each unsubscription
        receivers = request.app.org.notify_on_unsubscription or None
        if receivers:
            subject = _(
                'Unsubscription from newsletter',
                mapping={'address': address}
            )
            send_transactional_html_mail(
                request=request,
                template='mail_notify_unsubscribe.pt',
                subject=subject,
                receivers=receivers,
                content={
                    'address': address,
                    'title': subject,
                    'model': None,
                },
            )
    else:
        request.alert(_(
            '${address} could not be unsubscribed, wrong token',
            mapping={'address': address}
        ))

    return morepath.redirect(
        request.link(NewsletterCollection(request.session))
    )


# RFC-8058: respond to POST requests as well
@OrgApp.view(
    model=Subscription,
    name='unsubscribe',
    permission=Public,
    request_method='POST'
)
def view_unsubscribe_rfc8058(
    self: Subscription,
    request: OrgRequest
) -> Response:
    # it doesn't really make sense to check for success here
    # since this is an automated action without verficiation
    self.unsubscribe()
    return Response()
