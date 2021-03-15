from onegov.core.security import Private
from onegov.org.views.resource_recipient import view_resource_recipients, \
    handle_new_resource_recipient, handle_edit_resource_recipient
from onegov.town6 import TownApp
from onegov.org.forms import ResourceRecipientForm
from onegov.org.models import ResourceRecipient, ResourceRecipientCollection
from onegov.town6.layout import ResourceRecipientsLayout, \
    ResourceRecipientsFormLayout
from onegov.town6 import _


@TownApp.html(
    model=ResourceRecipientCollection,
    template='resource_recipients.pt',
    permission=Private)
def town_view_resource_recipients(self, request):
    return view_resource_recipients(
        self, request, ResourceRecipientsLayout(self, request))


@TownApp.form(
    model=ResourceRecipientCollection,
    name='new-recipient',
    template='form.pt',
    permission=Private,
    form=ResourceRecipientForm)
def town_handle_new_resource_recipient(self, request, form):
    title = _("New Recipient")
    return handle_new_resource_recipient(
        self, request, form,
        ResourceRecipientsFormLayout(self, request, title)
    )


@TownApp.form(
    model=ResourceRecipient,
    name='edit',
    template='form.pt',
    permission=Private,
    form=ResourceRecipientForm)
def town_handle_edit_resource_recipient(self, request, form):
    title = _("Edit Recipient")
    return handle_edit_resource_recipient(
        self, request, form,
        ResourceRecipientsFormLayout(self, request, title)
    )
