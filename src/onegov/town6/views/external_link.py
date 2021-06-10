from onegov.org.views.external_link import handle_new_external_link, \
    edit_external_link
from onegov.town6 import TownApp
from onegov.core.security import Private
from onegov.org.forms.external_link import ExternalLinkForm
from onegov.town6.layout import DefaultLayout
from onegov.org.models.external_link import (
    ExternalLinkCollection, ExternalLink
)


@TownApp.form(
    model=ExternalLinkCollection, name='new', template='form.pt',
    permission=Private, form=ExternalLinkForm)
def town_handle_new_external_link(self, request, form):
    return handle_new_external_link(
        self, request, form, layout=DefaultLayout(self, request)
    )


@TownApp.form(
    model=ExternalLink, name='edit', template='form.pt',
    permission=Private, form=ExternalLinkForm)
def town_edit_external_link(self, request, form):
    return edit_external_link(
        self, request, form, layout=DefaultLayout(self, request)
    )
