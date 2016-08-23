""" Newsletter subscription management. """

import morepath

from onegov.core.security import Public
from onegov.newsletter import NewsletterCollection, Subscription
from onegov.org import _, OrgApp


# use an english name for this view, so robots know what we use it for
@OrgApp.view(model=Subscription, name='confirm', permission=Public)
def view_confirm(self, request):
    if self.confirm():
        request.success(_(
            "the subscription for ${address} was successfully confirmed",
            mapping={'address': self.recipient.address}
        ))
    else:
        request.alert(_(
            "the subscription for ${address} could not be confirmed, "
            "wrong token",
            mapping={'address': self.recipient.address}
        ))

    return morepath.redirect(
        request.link(NewsletterCollection(request.app.session()))
    )


# use an english name for this view, so robots know what we use it for
@OrgApp.view(model=Subscription, name='unsubscribe', permission=Public)
def view_unsubscribe(self, request):

    address = self.recipient.address

    if self.unsubscribe():
        request.success(_(
            "${address} successfully unsubscribed",
            mapping={'address': address}
        ))
    else:
        request.alert(_(
            "${address} could not be unsubscribed, wrong token",
            mapping={'address': address}
        ))

    return morepath.redirect(
        request.link(NewsletterCollection(request.app.session()))
    )
