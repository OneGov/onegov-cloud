""" The newsletter view. """

import morepath

from collections import OrderedDict
from itertools import groupby
from onegov.core.security import Public, Private
from onegov.core.templates import render_template
from onegov.core.utils import linkify
from onegov.event import Occurrence, OccurrenceCollection
from onegov.newsletter import (
    Newsletter,
    NewsletterCollection,
    Recipient,
    RecipientCollection
)
from onegov.newsletter.errors import AlreadyExistsError
from onegov.org import _, OrgApp
from onegov.org.forms import NewsletterForm, NewsletterSendForm, SignupForm
from onegov.org.layout import (
    DefaultMailLayout,
    NewsletterLayout,
    RecipientLayout
)
from onegov.org.models import News

from sedate import utcnow
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


def get_newsletter_send_form(model, request):
    query = RecipientCollection(request.app.session()).query()
    query = query.order_by(Recipient.address)

    return NewsletterSendForm.for_newsletter(model, query.all())


def news_by_newsletter(newsletter, request):
    news_ids = newsletter.content.get('news')

    if not news_ids:
        return None

    query = request.app.session().query(News)
    query = query.order_by(desc(News.created))
    query = query.options(undefer('created'))
    query = query.options(undefer('content'))
    query = query.filter(News.id.in_(news_ids))

    return request.exclude_invisible(query.all())


def occurrences_by_newsletter(newsletter, request):
    occurrence_ids = newsletter.content.get('occurrences')

    if not occurrence_ids:
        return None

    query = request.app.session().query(Occurrence)
    query = query.order_by(Occurrence.start, Occurrence.title)
    query = query.filter(Occurrence.id.in_(occurrence_ids))

    return query.all()


@OrgApp.form(model=NewsletterCollection, template='newsletter_collection.pt',
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
                _("Welcome to the ${org} Newsletter", mapping={
                    'org': request.app.org.title
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
    if not request.is_manager:
        query = query.filter(Newsletter.sent != None)

    # the recipients count is only shown to logged in users
    if request.is_manager:
        recipients_count = RecipientCollection(self.session).query()\
            .filter(Recipient.confirmed == True)\
            .count()
    else:
        recipients_count = 0

    return {
        'form': form,
        'layout': NewsletterLayout(self, request),
        'newsletters': query.all(),
        'title': _("Newsletter"),
        'recipients_count': recipients_count
    }


@OrgApp.html(model=Newsletter, template='newsletter.pt', permission=Public)
def view_newsletter(self, request):

    return {
        'layout': NewsletterLayout(self, request),
        'newsletter': self,
        'news': news_by_newsletter(self, request),
        'occurrences': occurrences_by_newsletter(self, request),
        'title': self.title,
        'lead': linkify(self.lead),
    }


@OrgApp.html(model=RecipientCollection, template='recipients.pt',
             permission=Private)
def view_subscribers(self, request):

    # i18n:attributes translations do not support variables, so we need
    # to do this ourselves
    warning = request.translate(_("Do you really want to unsubscribe \"{}\"?"))

    recipients = self.query().order_by(Recipient.address).all()
    by_letter = OrderedDict()

    for key, values in groupby(recipients, key=lambda r: r.address[0].upper()):
        by_letter[key] = list(values)

    return {
        'layout': RecipientLayout(self, request),
        'title': _("Subscribers"),
        'by_letter': by_letter,
        'warning': warning,
    }


@OrgApp.form(model=NewsletterCollection, name='neu', template='form.pt',
             permission=Public, form=get_newsletter_form)
def handle_new_newsletter(self, request, form):

    if form.submitted(request):
        try:
            newsletter = self.add(title=form.title.data, html='')
        except AlreadyExistsError:
            request.alert(_("A newsletter with this name already exists"))
        else:
            form.update_model(newsletter, request)

            request.success(_("Added a new newsletter"))
            return morepath.redirect(request.link(newsletter))

    return {
        'form': form,
        'layout': NewsletterLayout(self, request),
        'title': _("New Newsletter"),
        'size': 'large'
    }


@OrgApp.form(model=Newsletter, template='form.pt', name='bearbeiten',
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


@OrgApp.view(model=Newsletter, request_method='DELETE', permission=Private)
def delete_page(self, request):
    request.assert_valid_csrf_token()

    NewsletterCollection(request.app.session()).delete(self)
    request.success("The newsletter was deleted")


@OrgApp.form(model=Newsletter, template='send_newsletter.pt', name='senden',
             permission=Private, form=get_newsletter_send_form)
def handle_send_newsletter(self, request, form):

    if form.submitted(request):
        query = RecipientCollection(request.app.session()).query()
        query = query.filter(Recipient.id.in_(form.recipients.data))
        recipients = (r for r in query.all() if r not in self.recipients)

        sent_mails = 0

        for recipient in recipients:

            # one mail per recipient (each has a specific unsubscribe link)
            mail = render_template(
                'mail_newsletter.pt', request, {
                    'layout': DefaultMailLayout(self, request),
                    'lead': linkify(self.lead).replace('\n', '<br>'),
                    'newsletter': self,
                    'title': self.title,
                    'unsubscribe': request.link(
                        recipient.subscription,
                        'unsubscribe'
                    ),
                    'news': news_by_newsletter(self, request),
                    'occurrences': occurrences_by_newsletter(self, request),
                }
            )

            request.app.send_email(
                subject=self.title,
                receivers=(recipient.address, ),
                content=mail
            )

            self.recipients.append(recipient)
            sent_mails += 1

        if not self.sent:
            self.sent = utcnow()

        request.success(_('Sent "${title}" to ${n} recipients', mapping={
            'title': self.title,
            'n': sent_mails
        }))
        return morepath.redirect(request.link(self))

    return {
        'layout': NewsletterLayout(self, request),
        'form': form,
        'title': self.title,
        'newsletter': self,
        'previous_recipients': self.recipients
    }
