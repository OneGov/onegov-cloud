""" The newsletter view. """

import morepath

from onegov.core.security import Public, Private
from onegov.newsletter import Newsletter, NewsletterCollection
from onegov.town import _, TownApp
from onegov.town.forms import NewsletterForm, SignupForm
from onegov.town.layout import NewsletterLayout
from sqlalchemy import desc
from sqlalchemy.orm import undefer


@TownApp.form(model=NewsletterCollection, template='newsletter_collection.pt',
              permission=Public, form=SignupForm)
def handle_newsletters(self, request, form):

    query = self.query()
    query = query.options(undefer(Newsletter.created))
    query = query.order_by(desc(Newsletter.created))

    # newsletters which were not sent yet are private
    if not request.is_logged_in:
        query = query.filter(Newsletter.sent != None)

    return {
        'form': form,
        'layout': NewsletterLayout(self, request),
        'newsletters': query.all(),
        'title': _("Newsletter"),
    }


@TownApp.form(model=NewsletterCollection, name='neu', template='form.pt',
              permission=Public, form=NewsletterForm)
def handle_new_newsletter(self, request, form):

    if form.submitted(request):
        newsletter = self.add(title=form.title.data, content='')
        form.update_model(newsletter, request)

        request.success(_("Added a new newsletter"))
        return morepath.redirect(request.link(newsletter))

    return {
        'form': form,
        'layout': NewsletterLayout(self, request),
        'title': _("New Newsletter"),
    }


@TownApp.html(model=Newsletter, template='newsletter.pt', permission=Public)
def view_newsletter(self, request):

    return {
        'layout': NewsletterLayout(self, request),
        'newsletter': self,
        'title': self.title,
    }


@TownApp.form(model=Newsletter, template='form.pt', name='bearbeiten',
              permission=Private, form=NewsletterForm)
def edit_newsletter(self, request, form):

    if form.submitted(request):
        form.update_model(self, request)

        request.success(_("Your changes were saved"))
        return morepath.redirect(request.link(self))

    elif request.method == 'GET':
        form.apply_model(self)

    return {
        'layout': NewsletterLayout(self, request),
        'form': form,
        'title': _("Edit Newsletter")
    }


@TownApp.view(model=Newsletter, request_method='DELETE', permission=Private)
def delete_page(self, request):
    request.assert_valid_csrf_token()

    NewsletterCollection(request.app.session()).delete(self)
    request.success("The newsletter was deleted")
