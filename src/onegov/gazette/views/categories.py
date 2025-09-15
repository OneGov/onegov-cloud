from __future__ import annotations

from io import BytesIO
from morepath import redirect
from morepath.request import Response
from onegov.core.security import Private
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import CategoryCollection
from onegov.gazette.forms import CategoryForm
from onegov.gazette.forms import EmptyForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import Category
from sedate import utcnow
from xlsxwriter import Workbook


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.gazette.request import GazetteRequest
    from webob import Response as BaseResponse


@GazetteApp.html(
    model=CategoryCollection,
    template='categories.pt',
    permission=Private
)
def view_categories(
    self: CategoryCollection,
    request: GazetteRequest
) -> RenderData:
    """ View the list of categories.

    This view is only visible by an admin.

    """
    layout = Layout(self, request)

    return {
        'title': _('Categories'),
        'layout': layout,
        'categories': self.query().all(),
        'export': request.link(self, name='export'),
        'new_category': request.link(self, name='new-category')
    }


@GazetteApp.form(
    model=CategoryCollection,
    name='new-category',
    template='form.pt',
    permission=Private,
    form=CategoryForm
)
def create_category(
    self: CategoryCollection,
    request: GazetteRequest,
    form: CategoryForm
) -> RenderData | BaseResponse:
    """ Create a new category.

    This view is only visible by an admin.

    """
    layout = Layout(self, request)

    if form.submitted(request):
        assert form.title.data is not None
        self.add_root(
            title=form.title.data,
            active=form.active.data,
            name=form.name.data
        )
        request.message(_('Category added.'), 'success')
        return redirect(layout.manage_categories_link)

    return {
        'layout': layout,
        'form': form,
        'title': _('New Category'),
        'button_text': _('Save'),
        'cancel': layout.manage_categories_link
    }


@GazetteApp.form(
    model=Category,
    name='edit',
    template='form.pt',
    permission=Private,
    form=CategoryForm
)
def edit_category(
    self: Category,
    request: GazetteRequest,
    form: CategoryForm
) -> RenderData | BaseResponse:
    """ Edit a category.

    This view is only visible by an admin.

    """

    layout = Layout(self, request)
    if form.submitted(request):
        form.update_model(self)
        request.message(_('Category modified.'), 'success')
        return redirect(layout.manage_categories_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _('Edit Category'),
        'button_text': _('Save'),
        'cancel': layout.manage_categories_link,
    }


@GazetteApp.form(
    model=Category,
    name='delete',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def delete_category(
    self: Category,
    request: GazetteRequest,
    form: EmptyForm
) -> RenderData | BaseResponse:
    """ Delete a category.

    Only unused categorys may be deleted.

    """
    layout = Layout(self, request)
    session = request.session

    if self.in_use:
        request.message(
            _('Only unused categorys may be deleted.'),
            'alert'
        )
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _('Delete Category'),
            'show_form': False
        }

    if form.submitted(request):
        collection = CategoryCollection(session)
        collection.delete(self)
        request.message(_('Category deleted.'), 'success')
        return redirect(layout.manage_categories_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _('Delete Category'),
        'button_text': _('Delete Category'),
        'button_class': 'alert',
        'cancel': layout.manage_categories_link
    }


@GazetteApp.view(
    model=CategoryCollection,
    name='export',
    permission=Private
)
def export_categories(
    self: CategoryCollection,
    request: GazetteRequest
) -> Response:
    """ Export all categories as XLSX. The exported file can be re-imported
    using the import-categories command line command.

    """

    output = BytesIO()
    workbook = Workbook(output)

    worksheet = workbook.add_worksheet(request.translate(_('Categories')))
    worksheet.write_row(0, 0, (
        request.translate(_('ID')),
        request.translate(_('Name')),
        request.translate(_('Title')),
        request.translate(_('Active'))
    ))

    for index, category in enumerate(self.query()):
        worksheet.write_row(index + 1, 0, (
            category.id or '',
            category.name or '',
            category.title or '',
            category.active,
        ))

    workbook.close()
    output.seek(0)

    response = Response()
    response.content_type = (
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response.content_disposition = 'inline; filename={}-{}.xlsx'.format(
        request.translate(_('Categories')).lower(),
        utcnow().strftime('%Y%m%d%H%M')
    )
    response.body = output.read()

    return response
