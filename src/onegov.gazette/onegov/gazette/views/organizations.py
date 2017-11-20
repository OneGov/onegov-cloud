from morepath import redirect
from onegov.core.security import Private
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import OrganizationCollection
from onegov.gazette.forms import OrganizationForm
from onegov.gazette.forms import EmptyForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import Organization
from onegov.gazette.models import OrganizationMove


@GazetteApp.html(
    model=OrganizationCollection,
    template='organizations.pt',
    permission=Private
)
def view_organizations(self, request):
    """ View the list of organizations.

    This view is only visible by a publisher.

    """
    layout = Layout(self, request)
    roots = self.query().filter(Organization.parent_id.is_(None))

    return {
        'title': _("Organizations"),
        'layout': layout,
        'roots': roots,
        'new_organization': request.link(self, name='new-organization'),
        'order': request.link(self, name='order')
    }


@GazetteApp.html(
    model=OrganizationCollection,
    name='order',
    template='organizations_order.pt',
    permission=Private
)
def view_organizations_order(self, request):
    """ Reorder the list of organizations.

    This view is only visible by a publisher.

    """
    layout = Layout(self, request)
    roots = self.query().filter(Organization.parent_id.is_(None))

    return {
        'title': _("Organizations"),
        'layout': layout,
        'roots': roots
    }


@GazetteApp.view(
    model=OrganizationMove,
    permission=Private,
    request_method='PUT'
)
def move_organization(self, request):
    request.assert_valid_csrf_token()
    self.execute()


@GazetteApp.form(
    model=OrganizationCollection,
    name='new-organization',
    template='form.pt',
    permission=Private,
    form=OrganizationForm
)
def create_organization(self, request, form):
    """ Create a new organization.

    This view is only visible by a publisher.

    """
    layout = Layout(self, request)

    if form.submitted(request):
        organization = self.add_root(
            title=form.title.data,
            active=form.active.data,
            name=form.name.data,
            external_name=form.external_name.data
        )
        organization.parent_id = form.parent.data or None
        request.message(_("Organization added."), 'success')
        return redirect(layout.manage_organizations_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New Organization"),
        'button_text': _("Save"),
        'cancel': layout.manage_organizations_link
    }


@GazetteApp.form(
    model=Organization,
    name='edit',
    template='form.pt',
    permission=Private,
    form=OrganizationForm
)
def edit_organization(self, request, form):
    """ Edit a organization.

    This view is only visible by a publisher.

    """

    layout = Layout(self, request)
    if form.submitted(request):
        form.update_model(self)
        request.message(_("Organization modified."), 'success')
        return redirect(layout.manage_organizations_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Edit Organization"),
        'button_text': _("Save"),
        'cancel': layout.manage_organizations_link,
    }


@GazetteApp.form(
    model=Organization,
    name='delete',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def delete_organization(self, request, form):
    """ Delete a organization.

    Only unused organizations may be deleted.

    """
    layout = Layout(self, request)
    session = request.app.session()

    if self.children or self.in_use:
        request.message(
            _(
                "Only unused organizations with no sub-organisations may be "
                "deleted."
            ),
            'alert'
        )
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Delete Organization"),
            'show_form': False
        }

    if form.submitted(request):
        collection = OrganizationCollection(session)
        collection.delete(self)
        request.message(_("Organization deleted."), 'success')
        return redirect(layout.manage_organizations_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Delete Organization"),
        'button_text': _("Delete Organization"),
        'button_class': 'alert',
        'cancel': layout.manage_organizations_link
    }
