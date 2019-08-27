from datetime import datetime
from io import BytesIO
from morepath import redirect
from morepath.request import Response
from onegov.core.security import Private
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import OrganizationCollection
from onegov.gazette.forms import EmptyForm
from onegov.gazette.forms import OrganizationForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import Organization
from onegov.gazette.models import OrganizationMove
from xlsxwriter import Workbook


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
        'export': request.link(self, name='export'),
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
    session = request.session

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


@GazetteApp.view(
    model=OrganizationCollection,
    name='export',
    permission=Private
)
def export_organizations(self, request):
    """ Export all organizations as XLSX. The exported file can be re-imported
    using the import-organizations command line command.

    """

    output = BytesIO()
    workbook = Workbook(output)

    worksheet = workbook.add_worksheet()
    worksheet.name = request.translate(_("Organizations"))
    worksheet.write_row(0, 0, (
        request.translate(_("ID")),
        request.translate(_("Name")),
        request.translate(_("Title")),
        request.translate(_("Active")),
        request.translate(_("External ID")),
        request.translate(_("Parent Organization"))
    ))

    index = 0
    for root in self.roots:
        index += 1
        worksheet.write_row(index, 0, (
            root.id or '',
            root.name or '',
            root.title or '',
            root.active,
            root.external_name or '',
            root.parent_id or ''
        ))
        for organization in root.children:
            index += 1
            worksheet.write_row(index, 0, (
                organization.id or '',
                organization.name or '',
                organization.title or '',
                organization.active,
                organization.external_name or '',
                organization.parent_id or ''
            ))

    workbook.close()
    output.seek(0)

    response = Response()
    response.content_type = (
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response.content_disposition = 'inline; filename={}-{}.xlsx'.format(
        request.translate(_("Organizations")).lower(),
        datetime.utcnow().strftime('%Y%m%d%H%M')
    )
    response.body = output.read()

    return response
