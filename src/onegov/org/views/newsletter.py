""" The newsletter view. """

import morepath

from collections import OrderedDict
from itertools import groupby

from onegov.core.elements import Link
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
from onegov.org.forms import NewsletterForm, ExportForm
from onegov.org.forms import NewsletterSendForm
from onegov.org.forms import NewsletterTestForm
from onegov.org.forms import SignupForm
from onegov.org.forms.newsletter import NewsletterSubscriberImportExportForm
from onegov.org.homepage_widgets import get_lead
from onegov.org.layout import DefaultMailLayout
from onegov.org.layout import NewsletterLayout
from onegov.org.layout import RecipientLayout
from onegov.org.models import News
from onegov.org.models import PublicationCollection
from onegov.org.utils import ORDERED_ACCESS
from sedate import utcnow
from sqlalchemy import desc
from sqlalchemy.orm import undefer
from string import Template
from webob.exc import HTTPNotFound

from onegov.org.views.utils import show_tags, show_filters

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from onegov.core.types import EmailJsonDict, RenderData
    from onegov.org.request import OrgRequest
    from sqlalchemy.orm import Query
    from webob import Response


def get_newsletter_form(
    model: Newsletter,
    request: 'OrgRequest'
) -> type[NewsletterForm]:
    form = NewsletterForm

    news = request.session.query(News)
    news = news.filter(News.parent != None)
    news = news.order_by(desc(News.created))
    news = news.options(undefer('created'))
    form = form.with_news(request, news)

    publications = PublicationCollection(request.session).query()
    publications = publications.order_by(desc(File.created))
    form = form.with_publications(request, publications)

    occurrences = OccurrenceCollection(request.session).query()
    s = occurrences.with_entities(Occurrence.id)
    # FIXME: Why are we ordering the subquery? As far as I can tell
    #        that doesn't actually do anything
    s = s.order_by(None)
    s = s.order_by(
        Occurrence.event_id,
        Occurrence.start
    )
    s = s.distinct(Occurrence.event_id).subquery()
    occurrences = occurrences.filter(Occurrence.id.in_(s))
    form = form.with_occurrences(request, occurrences)

    return form


def newsletter_news_by_access(
    newsletter: Newsletter,
    request: 'OrgRequest',
    access: str = 'public',
    include_wider_access: bool = True,
) -> list[News] | None:
    """
    Retrieves a list of news items associated with a specific newsletter
    based on the given access level or higher. This function is used for the
    newsletter preview as well as for sending newsletters.

    The function filters the news items based on their access level ('public',
    'secret', 'private') and whether they are published.
    It then orders the news items in descending order by their creation date.

    Returns:
    - list[News] | None: A list of news items that match the provided access
    level. If no news items are found, None is returned.

    Raises:
    - ValueError: If an invalid access level is provided.
    """

    news_ids = newsletter.content.get('news')
    if not news_ids:
        return None

    if access not in ('public', 'secret', 'private'):
        raise ValueError(f"Invalid access level: {access}")

    if include_wider_access:
        access_levels = ORDERED_ACCESS[ORDERED_ACCESS.index(access):]
    else:
        access_levels = access,  # used??

    query = request.session.query(News)
    query = query.filter(News.access.in_(access_levels))  # type: ignore
    query = query.filter(News.published == True)
    query = query.order_by(desc(News.created))
    query = query.options(undefer('created'))
    query = query.options(undefer('content'))
    query = query.filter(News.id.in_(news_ids))

    return query.all()


def visible_news_by_newsletter(
    newsletter: Newsletter,
    request: 'OrgRequest',
) -> list[News] | None:
    """
    Retrieves a list of news items associated with a specific newsletter
    visible to the current user.

    """
    news_ids = newsletter.content.get('news')
    if not news_ids:
        return None

    query = request.session.query(News)
    query = query.order_by(desc(News.created))
    query = query.options(undefer('created'))
    query = query.options(undefer('content'))
    query = query.filter(News.id.in_(news_ids))

    return request.exclude_invisible(query.all())


def occurrences_by_newsletter(
    newsletter: Newsletter,
    request: 'OrgRequest'
) -> 'Query[Occurrence] | None':
    occurrence_ids = newsletter.content.get('occurrences')

    if not occurrence_ids:
        return None

    query = request.session.query(Occurrence)
    query = query.order_by(Occurrence.start, Occurrence.title)
    query = query.filter(Occurrence.id.in_(occurrence_ids))

    return query


def publications_by_newsletter(
    newsletter: Newsletter,
    request: 'OrgRequest'
) -> 'Query[File] | None':
    publication_ids = newsletter.content.get('publications')

    if not publication_ids:
        return None

    query = PublicationCollection(request.session).query()
    query = query.filter(File.id.in_(publication_ids))
    query = query.order_by(File.created)

    # FIXME: why not exclude invisible files?
    return query


@OrgApp.form(model=NewsletterCollection, template='newsletter_collection.pt',
             permission=Public, form=SignupForm)
def handle_newsletters(
    self: NewsletterCollection,
    request: 'OrgRequest',
    form: SignupForm,
    layout: NewsletterLayout | None = None,
    mail_layout: DefaultMailLayout | None = None
) -> 'RenderData':
    if not (request.is_manager or request.app.org.show_newsletter):
        raise HTTPNotFound()

    if form.submitted(request):
        assert form.address.data is not None
        recipients = RecipientCollection(request.session)
        recipient = recipients.by_address(form.address.data)

        # do not show a specific error message if the user already signed up,
        # just pretend like everything worked correctly - if someone signed up
        # or not is private

        if not recipient:
            recipient = recipients.add(address=form.address.data)
            unsubscribe = request.link(recipient.subscription, 'unsubscribe')

            title = request.translate(
                _("Welcome to the ${org} Newsletter", mapping={
                    'org': request.app.org.title
                })
            )

            confirm_mail = render_template('mail_confirm.pt', request, {
                'layout': mail_layout or DefaultMailLayout(self, request),
                'newsletters': self,
                'subscription': recipient.subscription,
                'title': title,
                'unsubscribe': unsubscribe
            })

            request.app.send_marketing_email(
                subject=title,
                receivers=(recipient.address,),
                content=confirm_mail,
                headers={
                    'List-Unsubscribe': f'<{unsubscribe}>',
                    'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click'
                },
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
        recipients_count = (
            RecipientCollection(self.session).query()
            .filter(Recipient.confirmed == True)
            .count()
        )
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
def view_newsletter(
    self: Newsletter,
    request: 'OrgRequest',
    layout: NewsletterLayout | None = None
) -> 'RenderData':
    # link to file and thumbnail by id
    def link(f: File, name: str = '') -> str:
        return request.class_link(File, {'id': f.id}, name=name)

    layout = layout or NewsletterLayout(self, request)
    news = visible_news_by_newsletter(self, request)

    return {
        'layout': layout,
        'newsletter': self,
        'news': news,
        'secret_news':
            any(n.access == 'secret' for n in news) if news else False,
        'private_news':
            any(n.access == 'private' for n in news) if news else False,
        'secret_content_allowed': request.app.org.secret_content_allowed,
        'link_newsletter_settings':
            request.link(request.app.org, 'newsletter-settings'),
        'occurrences': occurrences_by_newsletter(self, request),
        'publications': publications_by_newsletter(self, request),
        'title': self.title,
        'lead': layout.linkify(self.lead),
        'link': link,
        'name_without_extension': name_without_extension,
        'get_lead': get_lead,
        'show_tags': show_tags(request),
        'show_filters': show_filters(request),
    }


@OrgApp.html(model=RecipientCollection, template='recipients.pt',
             permission=Private)
def view_subscribers(
    self: RecipientCollection,
    request: 'OrgRequest',
    layout: RecipientLayout | None = None
) -> 'RenderData':
    # i18n:attributes translations do not support variables, so we need
    # to do this ourselves
    warning = request.translate(_("Do you really want to unsubscribe \"{}\"?"))

    recipients = self.query().order_by(Recipient.address).filter_by(
        confirmed=True
    )
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
def handle_new_newsletter(
    self: NewsletterCollection,
    request: 'OrgRequest',
    form: NewsletterForm,
    layout: NewsletterLayout | None = None
) -> 'RenderData | Response':
    if form.submitted(request):
        assert form.title.data is not None
        try:
            newsletter = self.add(title=form.title.data, html='')
        except AlreadyExistsError:
            request.alert(_("A newsletter with this name already exists"))
        else:
            form.update_model(newsletter, request)

            request.success(_("Added a new newsletter"))
            return morepath.redirect(request.link(newsletter))

    layout = layout or NewsletterLayout(self, request)
    layout.edit_mode = True

    return {
        'form': form,
        'layout': layout,
        'title': _("New Newsletter"),
        'size': 'large'
    }


@OrgApp.form(model=Newsletter, template='form.pt', name='edit',
             permission=Private, form=get_newsletter_form)
def edit_newsletter(
    self: Newsletter,
    request: 'OrgRequest',
    form: NewsletterForm,
    layout: NewsletterLayout | None = None
) -> 'RenderData | Response':
    if form.submitted(request):
        form.update_model(self, request)

        request.success(_("Your changes were saved"))
        return morepath.redirect(request.link(self))

    elif request.method == 'GET':
        form.apply_model(self)

    layout = layout or NewsletterLayout(self, request)
    layout.edit_mode = True

    return {
        'layout': layout,
        'form': form,
        'title': _("Edit Newsletter"),
        'size': 'large'
    }


@OrgApp.view(model=Newsletter, request_method='DELETE', permission=Private)
def delete_newsletter(self: Newsletter, request: 'OrgRequest') -> None:
    request.assert_valid_csrf_token()

    NewsletterCollection(request.session).delete(self)
    request.success(_("The newsletter was deleted"))


def send_newsletter(
    request: 'OrgRequest',
    newsletter: Newsletter,
    recipients: 'Iterable[Recipient]',
    is_test: bool = False,
    layout: DefaultMailLayout | None = None
) -> int:
    layout = layout or DefaultMailLayout(newsletter, request)
    if request.app.org.secret_content_allowed:
        news = newsletter_news_by_access(newsletter, request, access='secret')
    else:
        news = newsletter_news_by_access(newsletter, request, access='public')

    _html = render_template(
        'mail_newsletter.pt', request, {
            'layout': layout,
            'lead': layout.linkify(newsletter.lead or ''),
            'newsletter': newsletter,
            'title': newsletter.title,
            'unsubscribe': '$unsubscribe',
            'news': news,
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
    def email_iter() -> 'Iterator[EmailJsonDict]':
        nonlocal count
        for count, recipient in enumerate(recipients, start=1):
            unsubscribe = request.link(recipient.subscription, 'unsubscribe')

            yield request.app.prepare_email(
                subject=newsletter.title,
                receivers=(recipient.address,),
                content=html.substitute(unsubscribe=unsubscribe),
                plaintext=plaintext.substitute(unsubscribe=unsubscribe),
                headers={
                    'List-Unsubscribe': f'<{unsubscribe}>',
                    'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click'
                },
            )

            if not is_test and recipient not in newsletter.recipients:
                newsletter.recipients.append(recipient)

    request.app.send_marketing_email_batch(email_iter())

    if not is_test:
        newsletter.sent = newsletter.sent or utcnow()

    return count


@OrgApp.form(model=Newsletter, template='send_newsletter.pt', name='send',
             permission=Private, form=NewsletterSendForm)
def handle_send_newsletter(
    self: Newsletter,
    request: 'OrgRequest',
    form: NewsletterSendForm,
    layout: NewsletterLayout | None = None
) -> 'RenderData | Response':
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
             permission=Private, form=NewsletterTestForm)
def handle_test_newsletter(
    self: Newsletter,
    request: 'OrgRequest',
    form: NewsletterTestForm,
    layout: NewsletterLayout | None = None
) -> 'RenderData | Response':
    layout = layout or NewsletterLayout(self, request)

    if form.submitted(request):
        send_newsletter(request, self, (form.recipient,), is_test=True)

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
def handle_preview_newsletter(
    self: Newsletter,
    request: 'OrgRequest',
    layout: DefaultMailLayout | None = None
) -> 'RenderData':
    layout = layout or DefaultMailLayout(self, request)
    if request.app.org.secret_content_allowed:
        news = newsletter_news_by_access(self, request, access='secret')
    else:
        news = newsletter_news_by_access(self, request, access='public')

    return {
        'layout': layout,
        'lead': layout.linkify(self.lead or ''),
        'newsletter': self,
        'title': self.title,
        'unsubscribe': '#',
        'news': news,
        'occurrences': occurrences_by_newsletter(self, request),
        'publications': publications_by_newsletter(self, request),
        'name_without_extension': name_without_extension
    }


@OrgApp.form(
    model=RecipientCollection,
    name='export-newsletter-recipients',
    permission=Private,
    form=ExportForm,
    template='export.pt',
)
def export_newsletter_recipients(
    self: RecipientCollection,
    request: 'OrgRequest',
    form: ExportForm,
    layout: RecipientLayout | None = None
) -> 'RenderData | Response':
    layout = layout or RecipientLayout(self, request)
    layout.breadcrumbs.append(Link(_("Export"), '#'))
    layout.editbar_links = None

    if form.submitted(request):
        import_form = NewsletterSubscriberImportExportForm()
        import_form.request = request
        results = import_form.run_export()

        return form.as_export_response(
            results, title=request.translate(_("Newsletter Recipients"))
        )

    return {
        'layout': layout,
        'title': _("Newsletter recipient Export"),
        'form': form,
        'explanation': _("Exports all newsletter recipients."),
    }


@OrgApp.form(
    model=RecipientCollection,
    name='import-newsletter-recipients',
    permission=Private,
    form=NewsletterSubscriberImportExportForm,
    template='form.pt',
)
def import_newsletter_recipients(
    self: RecipientCollection,
    request: 'OrgRequest',
    form: NewsletterSubscriberImportExportForm,
    layout: RecipientLayout | None = None
) -> 'RenderData | Response':
    layout = layout or RecipientLayout(self, request)
    layout.breadcrumbs.append(Link(_("Import"), '#'))
    layout.editbar_links = None

    if form.submitted(request):
        count, errors = form.run_import()
        if errors:
            request.alert(
                _(
                    'The following line(s) contain invalid data: ${lines}',
                    mapping={'lines': ', '.join(errors)},
                )
            )
        elif form.dry_run.data:
            request.success(
                _(
                    '${count} newsletter subscribers will be imported',
                    mapping={'count': count},
                )
            )
        else:
            request.success(
                _(
                    '${count} newsletter subscribers imported',
                    mapping={'count': count},
                )
            )
            return morepath.redirect(request.link(self))

    return {
        'layout': layout,
        'callout': _(
            'The same format as the export (XLSX) can be used for the '
            'import.'
        ),
        'title': _('Import'),
        'form': form,
        'form_width': 'large',
    }
