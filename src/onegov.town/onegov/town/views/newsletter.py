""" The newsletter view. """

from onegov.core.security import Public
from onegov.newsletter import Newsletter, NewsletterCollection
from onegov.town import _, TownApp
from onegov.town.forms import SignupForm
from onegov.town.layout import NewsletterLayout


@TownApp.form(model=NewsletterCollection, template='newsletter.pt',
              permission=Public, form=SignupForm)
def handle_newsletters(self, request, form):

    # newsletters which were not sent yet are private
    if request.is_logged_in:
        newsletters = self.query().all()
    else:
        newsletters = self.query().filter(Newsletter.sent == True).all()

    return {
        'form': form,
        'layout': NewsletterLayout(self, request),
        'newsletters': newsletters,
        'title': _("Newsletter"),
    }
