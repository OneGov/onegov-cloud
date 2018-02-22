from morepath import redirect
from onegov.core.security import Private
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import CategoryCollection
from onegov.gazette.forms import CategoryForm
from onegov.gazette.forms import EmptyForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import Category


@GazetteApp.html(
    model=CategoryCollection,
    template='categories.pt',
    permission=Private
)
def view_categories(self, request):
    """ View the list of categories.

    This view is only visible by an admin.

    """
    layout = Layout(self, request)

    return {
        'title': _("Categories"),
        'layout': layout,
        'categories': self.query().all(),
        'new_category': request.link(self, name='new-category')
    }


@GazetteApp.form(
    model=CategoryCollection,
    name='new-category',
    template='form.pt',
    permission=Private,
    form=CategoryForm
)
def create_category(self, request, form):
    """ Create a new category.

    This view is only visible by an admin.

    """
    layout = Layout(self, request)

    if form.submitted(request):
        self.add_root(
            title=form.title.data,
            active=form.active.data,
            name=form.name.data
        )
        request.message(_("Category added."), 'success')
        return redirect(layout.manage_categories_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New Category"),
        'button_text': _("Save"),
        'cancel': layout.manage_categories_link
    }


@GazetteApp.form(
    model=Category,
    name='edit',
    template='form.pt',
    permission=Private,
    form=CategoryForm
)
def edit_category(self, request, form):
    """ Edit a category.

    This view is only visible by an admin.

    """

    layout = Layout(self, request)
    if form.submitted(request):
        form.update_model(self)
        request.message(_("Category modified."), 'success')
        return redirect(layout.manage_categories_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Edit Category"),
        'button_text': _("Save"),
        'cancel': layout.manage_categories_link,
    }


@GazetteApp.form(
    model=Category,
    name='delete',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def delete_category(self, request, form):
    """ Delete a category.

    Only unused categorys may be deleted.

    """
    layout = Layout(self, request)
    session = request.session

    if self.in_use:
        request.message(
            _("Only unused categorys may be deleted."),
            'alert'
        )
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Delete Category"),
            'show_form': False
        }

    if form.submitted(request):
        collection = CategoryCollection(session)
        collection.delete(self)
        request.message(_("Category deleted."), 'success')
        return redirect(layout.manage_categories_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Delete Category"),
        'button_text': _("Delete Category"),
        'button_class': 'alert',
        'cancel': layout.manage_categories_link
    }
