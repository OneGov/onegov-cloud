from __future__ import annotations

from onegov.core.security import Public, Private
from onegov.newsletter import Newsletter
from onegov.newsletter import NewsletterCollection
from onegov.newsletter import RecipientCollection
from onegov.org.forms.newsletter import NewsletterSubscriberImportExportForm
from onegov.org.views.newsletter import (
    handle_newsletters, view_newsletter, view_subscribers,
    handle_new_newsletter, get_newsletter_form, edit_newsletter,
    handle_send_newsletter, handle_test_newsletter, handle_preview_newsletter,
    export_newsletter_recipients, import_newsletter_recipients,
    handle_update_newsletters_subscription)
from onegov.town6 import TownApp
from onegov.org.forms import NewsletterSendForm, ExportForm
from onegov.org.forms import NewsletterTestForm
from onegov.org.forms import SignupForm
from onegov.town6.layout import (
    NewsletterLayout, RecipientLayout, DefaultMailLayout)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.forms import NewsletterForm
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=NewsletterCollection,
    template='newsletter_collection.pt',
    permission=Public,
    form=SignupForm
)
def town_handle_newsletters(
    self: NewsletterCollection,
    request: TownRequest,
    form: SignupForm
) -> RenderData | Response:
    return handle_newsletters(
        self, request, form, NewsletterLayout(self, request),
        DefaultMailLayout(self, request)
    )


@TownApp.form(
    model=NewsletterCollection,
    template='newsletter_collection.pt',
    permission=Public,
    name='update',
    form=SignupForm
)
def town_handle_update_newsletters_subscription(
    self: NewsletterCollection,
    request: TownRequest,
    form: SignupForm
) -> RenderData | Response:

    return handle_update_newsletters_subscription(
        self, request, form, NewsletterLayout(self, request),
        DefaultMailLayout(self, request)
    )


@TownApp.html(model=Newsletter, template='newsletter.pt', permission=Public)
def town_view_newsletter(
    self: Newsletter,
    request: TownRequest
) -> RenderData:
    return view_newsletter(self, request, NewsletterLayout(self, request))


@TownApp.html(
    model=RecipientCollection,
    template='recipients.pt',
    permission=Private
)
def town_view_subscribers(
    self: RecipientCollection,
    request: TownRequest
) -> RenderData:
    return view_subscribers(self, request, RecipientLayout(self, request))


@TownApp.form(
    model=NewsletterCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=get_newsletter_form
)
def town_handle_new_newsletter(
    self: NewsletterCollection,
    request: TownRequest,
    form: NewsletterForm
) -> RenderData | Response:
    return handle_new_newsletter(
        self, request, form, NewsletterLayout(self, request))


@TownApp.form(
    model=Newsletter,
    template='form.pt',
    name='edit',
    permission=Private,
    form=get_newsletter_form
)
def town_edit_newsletter(
    self: Newsletter,
    request: TownRequest,
    form: NewsletterForm
) -> RenderData | Response:
    return edit_newsletter(
        self, request, form, NewsletterLayout(self, request))


@TownApp.form(
    model=Newsletter,
    template='send_newsletter.pt',
    name='send',
    permission=Private,
    form=NewsletterSendForm
)
def town_handle_send_newsletter(
    self: Newsletter,
    request: TownRequest,
    form: NewsletterSendForm
) -> RenderData | Response:
    return handle_send_newsletter(
        self, request, form, NewsletterLayout(self, request))


@TownApp.form(
    model=Newsletter,
    template='form.pt',
    name='test',
    permission=Private,
    form=NewsletterTestForm
)
def town_handle_test_newsletter(
    self: Newsletter,
    request: TownRequest,
    form: NewsletterTestForm
) -> RenderData | Response:
    return handle_test_newsletter(
        self, request, form, NewsletterLayout(self, request))


@TownApp.html(
    model=Newsletter,
    template='mail_newsletter.pt',
    name='preview',
    permission=Private
)
def town_handle_preview_newsletter(
    self: Newsletter,
    request: TownRequest
) -> RenderData:
    return handle_preview_newsletter(
        self, request, DefaultMailLayout(self, request))


@TownApp.form(
    model=RecipientCollection,
    name='export-newsletter-recipients',
    permission=Private,
    form=ExportForm,
    template='export.pt'
)
def town_export_newsletter_recipients(
    self: RecipientCollection,
    request: TownRequest,
    form: ExportForm,
) -> RenderData | Response:
    return export_newsletter_recipients(
        self, request, form, RecipientLayout(self, request))


@TownApp.form(
    model=RecipientCollection,
    name='import-newsletter-recipients',
    permission=Private,
    form=NewsletterSubscriberImportExportForm,
    template='form.pt'
)
def town_import_newsletter_recipients(
    self: RecipientCollection,
    request: TownRequest,
    form: NewsletterSubscriberImportExportForm
) -> RenderData | Response:
    return import_newsletter_recipients(
        self, request, form, RecipientLayout(self, request))
