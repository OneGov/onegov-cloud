""" The newsletter view. """

import morepath

from collections import OrderedDict
from itertools import groupby
from onegov.core.html import html_to_text
from onegov.core.security import Public, Private
from onegov.core.templates import render_template
from onegov.event import Occurrence, OccurrenceCollection
from onegov.file import File
from onegov.file.utils import name_without_extension
from onegov.newsletter import Newsletter
from onegov.newsletter import NewsletterCollection
from onegov.newsletter import Recipient
from onegov.newsletter import RecipientCollection
from onegov.newsletter.errors import AlreadyExistsError
from onegov.org import _, OrgApp
from onegov.org.forms import NewsletterForm
from onegov.org.forms import NewsletterSendForm
from onegov.org.forms import NewsletterTestForm
from onegov.org.forms import SignupForm
from onegov.org.homepage_widgets import get_lead
from onegov.org.layout import DefaultMailLayout
from onegov.org.layout import NewsletterLayout
from onegov.org.layout import RecipientLayout
from onegov.org.models import News
from onegov.org.models import PublicationCollection
from sedate import utcnow
from sqlalchemy import desc
from sqlalchemy.orm import undefer
from string import Template


def get_newsletter_form(model, request):

    form = NewsletterForm

    def news():
        q = request.session.query(News)
        q = q.filter(News.parent != None)
        q = q.order_by(desc(News.created))
        q = q.options(undefer('created'))

        return q

    form = form.with_news(request, news())

    def publications():
        q = PublicationCollection(request.session).query()
        q = q.order_by(desc(File.created))

        return q

    form = form.with_publications(request, publications())

    def occurrences():
        q = OccurrenceCollection(request.session).query()

        s = q.with_entities(Occurrence.id)
        s = s.order_by(None)
        s = s.order_by(
            Occurrence.event_id,
            Occurrence.start)

        s = s.distinct(Occurrence.event_id).subquery()

        return q.filter(Occurrence.id.in_(s))

    form = form.with_occurrences(request, occurrences())

    return form


def news_by_newsletter(newsletter, request):
    news_ids = newsletter.content.get('news')

    if not news_ids:
        return None

    query = request.session.query(News)
    query = query.order_by(desc(News.created))
    query = query.options(undefer('created'))
    query = query.options(undefer('content'))
    query = query.filter(News.id.in_(news_ids))

    return request.exclude_invisible(query.all())


def occurrences_by_newsletter(newsletter, request):
    occurrence_ids = newsletter.content.get('occurrences')

    if not occurrence_ids:
        return None

    query = request.session.query(Occurrence)
    query = query.order_by(Occurrence.start, Occurrence.title)
    query = query.filter(Occurrence.id.in_(occurrence_ids))

    return query


def publications_by_newsletter(newsletter, request):
    publication_ids = newsletter.content.get('publications')

    if not publication_ids:
        return None

    query = PublicationCollection(request.session).query()
    query = query.filter(File.id.in_(publication_ids))
    query = query.order_by(File.created)

    return query


@OrgApp.form(model=NewsletterCollection, template='newsletter_collection.pt',
             permission=Public, form=SignupForm)
def handle_newsletters(self, request, form, layout=None, mail_layout=None):

    if form.submitted(request):
        recipients = RecipientCollection(request.session)
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
                'layout': mail_layout or DefaultMailLayout(self, request),
                'newsletters': self,
                'subscription': recipient.subscription,
                'title': title
            })

            # TODO: Make this an opt-out instead so we can move it back
            #       to the marketing stream?
            request.app.send_transactional_email(
                subject=title,
                receivers=(recipient.address, ),
                content=confirm_mail,
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
        'layout': layout or NewsletterLayout(self, request),
        'newsletters': query.all(),
        'title': _("Newsletter"),
        'recipients_count': recipients_count
    }


@OrgApp.html(model=Newsletter, template='newsletter.pt', permission=Public)
def view_newsletter(self, request, layout=None):

    # link to file and thumbnail by id
    def link(f, name=None):
        return request.class_link(File, {'id': f.id}, name=name)

    layout = layout or NewsletterLayout(self, request)

    return {
        'layout': layout,
        'newsletter': self,
        'news': news_by_newsletter(self, request),
        'occurrences': occurrences_by_newsletter(self, request),
        'publications': publications_by_newsletter(self, request),
        'title': self.title,
        'lead': layout.linkify(self.lead),
        'link': link,
        'name_without_extension': name_without_extension,
        'get_lead': get_lead
    }


@OrgApp.html(model=RecipientCollection, template='recipients.pt',
             permission=Private)
def view_subscribers(self, request, layout=None):

    # i18n:attributes translations do not support variables, so we need
    # to do this ourselves
    warning = request.translate(_("Do you really want to unsubscribe \"{}\"?"))

    recipients = self.query().order_by(Recipient.address).all()
    by_letter = OrderedDict()

    for key, values in groupby(recipients, key=lambda r: r.address[0].upper()):
        by_letter[key] = list(values)

    return {
        'layout': layout or RecipientLayout(self, request),
        'title': _("Subscribers"),
        'by_letter': by_letter,
        'warning': warning,
    }


@OrgApp.form(model=NewsletterCollection, name='new', template='form.pt',
             permission=Public, form=get_newsletter_form)
def handle_new_newsletter(self, request, form, layout=None):

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
        'layout': layout or NewsletterLayout(self, request),
        'title': _("New Newsletter"),
        'size': 'large'
    }


@OrgApp.form(model=Newsletter, template='form.pt', name='edit',
             permission=Private, form=get_newsletter_form)
def edit_newsletter(self, request, form, layout=None):

    if form.submitted(request):
        form.update_model(self, request)

        request.success(_("Your changes were saved"))
        return morepath.redirect(request.link(self))

    elif request.method == 'GET':
        form.apply_model(self)

    return {
        'layout': layout or NewsletterLayout(self, request),
        'form': form,
        'title': _("Edit Newsletter"),
        'size': 'large'
    }


@OrgApp.view(model=Newsletter, request_method='DELETE', permission=Private)
def delete_page(self, request):
    request.assert_valid_csrf_token()

    NewsletterCollection(request.session).delete(self)
    request.success(_("The newsletter was deleted"))


def send_newsletter(request, newsletter, recipients, is_test=False,
                    layout=None):
    layout = layout or DefaultMailLayout(newsletter, request)
    _html = render_template(
        'mail_newsletter.pt', request, {
            'layout': layout,
            'lead': layout.linkify(newsletter.lead or ''),
            'newsletter': newsletter,
            'title': newsletter.title,
            'unsubscribe': '$unsubscribe',
            'news': news_by_newsletter(newsletter, request),
            'occurrences': occurrences_by_newsletter(newsletter, request),
            'publications': publications_by_newsletter(newsletter, request),
            'name_without_extension': name_without_extension
        }
    )
    html = Template(_html)
    plaintext = Template(html_to_text(_html))

    count = 0

    # We use a generator function to submit the email batch since that is
    # significantly more memory efficient for large batches.
    def email_iter():
        nonlocal count
        for count, recipient in enumerate(recipients, start=1):
            unsubscribe = request.link(recipient.subscription, 'unsubscribe')

            yield request.app.prepare_email(
                subject=newsletter.title,
                receivers=(recipient.address, ),
                content=html.substitute(unsubscribe=unsubscribe),
                plaintext=plaintext.substitute(unsubscribe=unsubscribe),
                headers={'List-Unsubscribe': f'<{unsubscribe}>'}
            )

            if not is_test and recipient not in newsletter.recipients:
                newsletter.recipients.append(recipient)

    request.app.send_marketing_email_batch(email_iter())

    if not is_test:
        newsletter.sent = newsletter.sent or utcnow()

    return count


@OrgApp.form(model=Newsletter, template='send_newsletter.pt', name='send',
             permission=Private, form=NewsletterSendForm)
def handle_send_newsletter(self, request, form, layout=None):
    layout = layout or NewsletterLayout(self, request)

    open_recipients = self.open_recipients

    if form.submitted(request):
        if form.send.data == 'now':
            sent = send_newsletter(request, self, open_recipients)

            request.success(_('Sent "${title}" to ${n} recipients', mapping={
                'title': self.title,
                'n': sent
            }))
        elif form.send.data == 'specify':
            self.scheduled = form.time.data

            request.success(
                _('Scheduled "${title}" to be sent on ${date}', mapping={
                    'title': self.title,
                    'date': layout.format_date(self.scheduled, 'datetime_long')
                })
            )
        else:
            raise NotImplementedError()

        return morepath.redirect(request.link(self))

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'newsletter': self,
        'previous_recipients': self.recipients,
        'open_recipients': open_recipients,
    }


@OrgApp.form(model=Newsletter, template='form.pt', name='test',
             permission=Private, form=NewsletterTestForm.build)
def handle_test_newsletter(self, request, form, layout=None):
    layout = layout or NewsletterLayout(self, request)

    if form.submitted(request):
        send_newsletter(request, self, (form.recipient, ), is_test=True)

        request.success(_('Sent "${title}" to ${recipient}', mapping={
            'title': self.title,
            'recipient': form.recipient.address
        }))

        return morepath.redirect(request.link(self))

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'helptext': _(
            "Sends a test newsletter to the given address"
        )
    }


@OrgApp.html(model=Newsletter,
             template='mail_newsletter.pt', name='preview', permission=Private)
def handle_preview_newsletter(self, request, layout=None):
    layout = layout or DefaultMailLayout(self, request)

    return {
        'layout': layout,
        'lead': layout.linkify(self.lead or ''),
        'newsletter': self,
        'title': self.title,
        'unsubscribe': '#',
        'news': news_by_newsletter(self, request),
        'occurrences': occurrences_by_newsletter(self, request),
        'publications': publications_by_newsletter(self, request),
        'name_without_extension': name_without_extension
    }
