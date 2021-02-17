from onegov.core.security import Public, Private
from onegov.newsletter import Newsletter
from onegov.newsletter import NewsletterCollection
from onegov.newsletter import RecipientCollection
from onegov.org.views.newsletter import handle_newsletters, view_newsletter, \
    view_subscribers, handle_new_newsletter, get_newsletter_form, \
    edit_newsletter, handle_send_newsletter, \
    handle_test_newsletter, handle_preview_newsletter
from onegov.town6 import TownApp
from onegov.org.forms import NewsletterSendForm
from onegov.org.forms import NewsletterTestForm
from onegov.org.forms import SignupForm
from onegov.town6.layout import NewsletterLayout, RecipientLayout, \
    DefaultMailLayout


@TownApp.form(model=NewsletterCollection, template='newsletter_collection.pt',
              permission=Public, form=SignupForm)
def town_handle_newsletters(self, request, form):
    return handle_newsletters(
        self, request, form, NewsletterLayout(self, request),
        DefaultMailLayout(self, request)
    )


@TownApp.html(model=Newsletter, template='newsletter.pt', permission=Public)
def town_view_newsletter(self, request):
    return view_newsletter(self, request, NewsletterLayout(self, request))


@TownApp.html(model=RecipientCollection, template='recipients.pt',
              permission=Private)
def town_view_subscribers(self, request):
    return view_subscribers(self, request, RecipientLayout(self, request))


@TownApp.form(model=NewsletterCollection, name='new', template='form.pt',
              permission=Public, form=get_newsletter_form)
def town_handle_new_newsletter(self, request, form):
    return handle_new_newsletter(
        self, request, form, NewsletterLayout(self, request))


@TownApp.form(model=Newsletter, template='form.pt', name='edit',
              permission=Private, form=get_newsletter_form)
def town_edit_newsletter(self, request, form):
    return edit_newsletter(
        self, request, form, NewsletterLayout(self, request))


@TownApp.form(model=Newsletter, template='send_newsletter.pt', name='send',
              permission=Private, form=NewsletterSendForm)
def town_handle_send_newsletter(self, request, form):
    return handle_send_newsletter(
        self, request, form, NewsletterLayout(self, request))


@TownApp.form(model=Newsletter, template='form.pt', name='test',
              permission=Private, form=NewsletterTestForm.build)
def town_handle_test_newsletter(self, request, form):
    return handle_test_newsletter(
        self, request, form, NewsletterLayout(self, request))


@TownApp.html(
    model=Newsletter,
    template='mail_newsletter.pt',
    name='preview',
    permission=Private
)
def town_handle_preview_newsletter(self, request):
    return handle_preview_newsletter(
        self, request, DefaultMailLayout(self, request))
