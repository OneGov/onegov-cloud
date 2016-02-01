""" The newsletter view. """

import morepath

from onegov.core.security import Public
from onegov.newsletter import Newsletter, NewsletterCollection
from onegov.town import _, TownApp
from onegov.town.forms import NewsletterForm, SignupForm
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


@TownApp.form(model=NewsletterCollection, name='neu', template='form.pt',
              permission=Public, form=NewsletterForm)
def handle_new_newsletter(self, request, form):

    if form.submitted(request):
        newsletter = self.add(
            title=form.title.data,
            content=form.get_content(request)
        )
        form.update_model(newsletter)

        return morepath.redirect(request.link(self))

    return {
        'form': form,
        'layout': NewsletterLayout(self, request),
        'title': _("New Newsletter"),
    }
