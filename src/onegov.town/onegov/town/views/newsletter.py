""" The newsletter view. """

import morepath

from onegov.core.security import Public, Private
from onegov.core.templates import render_template
from onegov.event import Occurrence, OccurrenceCollection
from onegov.newsletter import Newsletter
from onegov.newsletter import NewsletterCollection
from onegov.newsletter import RecipientCollection
from onegov.town import _, TownApp
from onegov.town.forms import NewsletterForm, SignupForm
from onegov.town.layout import DefaultMailLayout, NewsletterLayout
from onegov.town.models import News
from sqlalchemy import desc
from sqlalchemy.orm import undefer


def get_newsletter_form(model, request):

    form = NewsletterForm

    query = request.app.session().query(News)
    query = query.filter(News.parent != None)
    query = query.order_by(desc(News.created))
    query = query.options(undefer('created'))
    form = form.with_news(request, query.all())

    query = OccurrenceCollection(request.app.session()).query(outdated=False)
    subquery = query.with_entities(Occurrence.id)
    subquery = subquery.order_by(None)
    subquery = subquery.order_by(
        Occurrence.event_id,
        Occurrence.start
    )
    subquery = subquery.distinct(Occurrence.event_id).subquery()
    query.filter(Occurrence.id.in_(subquery))

    form = form.with_occurrences(request, query.all())

    return form


@TownApp.form(model=NewsletterCollection, template='newsletter_collection.pt',
              permission=Public, form=SignupForm)
def handle_newsletters(self, request, form):

    if form.submitted(request):
        recipients = RecipientCollection(request.app.session())
        recipient = recipients.by_address(form.address.data)

        # do not show a specific error message if the user already signed up,
        # just pretend like everything worked correctly - if someone signed up
        # or not is private

        if not recipient:
            recipient = recipients.add(address=form.address.data)

            title = request.translate(
                _("Welcome to the ${town} Newsletter", mapping={
                    'town': request.app.town.name
                })
            )

            confirm_mail = render_template('mail_confirm.pt', request, {
                'layout': DefaultMailLayout(self, request),
                'newsletters': self,
                'subscription': recipient.subscription,
                'title': title
            })

            request.app.send_email(
                subject=title,
                receivers=(recipient.address, ),
                content=confirm_mail
            )

        request.success(_((
            "Success! We have sent a confirmation link to "
            "${address}, if we didn't send you one already."
        ), mapping={'address': form.address.data}))

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


@TownApp.html(model=Newsletter, template='newsletter.pt', permission=Public)
def view_newsletter(self, request):

    news_ids = self.content.get('news')

    if not news_ids:
        news = None
    else:
        query = request.app.session().query(News)
        query = query.order_by(desc(News.created))
        query = query.options(undefer('created'))
        query = query.filter(News.id.in_(news_ids))

        news = request.exclude_invisible(query.all())

    occurrence_ids = self.content.get('occurrences')

    if not occurrence_ids:
        occurrences = None
    else:
        query = request.app.session().query(Occurrence)
        query = query.order_by(Occurrence.start, Occurrence.title)
        query = query.filter(Occurrence.id.in_(occurrence_ids))

        occurrences = query.all()

    return {
        'layout': NewsletterLayout(self, request),
        'newsletter': self,
        'news': news,
        'occurrences': occurrences,
        'title': self.title,
    }


@TownApp.form(model=NewsletterCollection, name='neu', template='form.pt',
              permission=Public, form=get_newsletter_form)
def handle_new_newsletter(self, request, form):

    if form.submitted(request):
        newsletter = self.add(title=form.title.data, html='')
        form.update_model(newsletter, request)

        request.success(_("Added a new newsletter"))
        return morepath.redirect(request.link(newsletter))

    return {
        'form': form,
        'layout': NewsletterLayout(self, request),
        'title': _("New Newsletter"),
        'size': 'large'
    }


@TownApp.form(model=Newsletter, template='form.pt', name='bearbeiten',
              permission=Private, form=get_newsletter_form)
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
        'title': _("Edit Newsletter"),
        'size': 'large'
    }


@TownApp.view(model=Newsletter, request_method='DELETE', permission=Private)
def delete_page(self, request):
    request.assert_valid_csrf_token()

    NewsletterCollection(request.app.session()).delete(self)
    request.success("The newsletter was deleted")
