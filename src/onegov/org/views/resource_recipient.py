from onegov.core.security import Private
from onegov.org import OrgApp, _
from onegov.org.forms import ResourceRecipientForm
from onegov.org.layout import ResourceRecipientsLayout
from onegov.org.layout import ResourceRecipientsFormLayout
from onegov.org.models import ResourceRecipient, ResourceRecipientCollection
from onegov.reservation import Resource, ResourceCollection
from sqlalchemy.orm import undefer
from onegov.org.elements import DeleteLink, Link


@OrgApp.html(
    model=ResourceRecipientCollection,
    template='resource_recipients.pt',
    permission=Private)
def view_resource_recipients(self, request, layout=None):

    layout = layout or ResourceRecipientsLayout(self, request)

    def recipient_links(recipient):
        yield Link(
            text=_("Edit"),
            url=request.link(recipient, 'edit')
        )

        yield DeleteLink(
            text=_("Delete"),
            url=layout.csrf_protected_url(request.link(recipient)),
            confirm=_('Do you really want to delete "${name}"?', mapping={
                'name': recipient.name
            }),
            target='#{}'.format(recipient.id.hex),
            yes_button_text=_("Delete Recipient")
        )

    q = ResourceCollection(request.app.libres_context).query()
    q = q.order_by(Resource.group, Resource.name)
    q = q.with_entities(Resource.group, Resource.title, Resource.id)

    default_group = request.translate(_("General"))

    resources = dict(
        (r.id.hex, "{group} - {title}".format(
            group=r.group or default_group,
            title=r.title
        ))
        for r in q
    )

    return {
        'layout': layout,
        'title': _("Recipients"),
        'resources': resources,
        'recipients': self.query().options(undefer(ResourceRecipient.content)),
        'recipient_links': recipient_links
    }


@OrgApp.form(
    model=ResourceRecipientCollection,
    name='new-recipient',
    template='form.pt',
    permission=Private,
    form=ResourceRecipientForm)
def handle_new_resource_recipient(self, request, form, layout=None):

    if form.submitted(request):
        self.add(
            name=form.name.data,
            medium='email',
            address=form.address.data,
            daily_reservations=form.daily_reservations.data,
            new_reservations=form.new_reservations.data,
            send_on=form.send_on.data,
            resources=form.resources.data,
        )

        request.success(_("Added a new recipient"))
        return request.redirect(request.link(self))

    title = _("New Recipient")
    if layout:
        layout.title = title

    return {
        'title': title,
        'layout': layout or ResourceRecipientsFormLayout(self, request, title),
        'form': form
    }


@OrgApp.form(
    model=ResourceRecipient,
    name='edit',
    template='form.pt',
    permission=Private,
    form=ResourceRecipientForm)
def handle_edit_resource_recipient(self, request, form, layout=None):

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))

        return request.redirect(
            request.class_link(ResourceRecipientCollection)
        )
    elif not request.POST:
        form.process(obj=self)

    title = _("Edit Recipient")

    return {
        'title': title,
        'layout': layout or ResourceRecipientsFormLayout(self, request, title),
        'form': form
    }


@OrgApp.view(
    model=ResourceRecipient,
    permission=Private,
    request_method='DELETE')
def delete_notification(self, request):
    request.assert_valid_csrf_token()
    ResourceRecipientCollection(request.session).delete(self)

    @request.after
    def remove_target(response):
        response.headers.add('X-IC-Remove', 'true')
