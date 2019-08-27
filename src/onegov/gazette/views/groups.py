from morepath import redirect
from onegov.core.security import Private
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.forms import EmptyForm
from onegov.gazette.layout import Layout
from onegov.user import UserGroup
from onegov.user import UserGroupCollection
from onegov.user.forms import UserGroupForm


@GazetteApp.html(
    model=UserGroupCollection,
    template='groups.pt',
    permission=Private
)
def view_groups(self, request):
    """ View all the user groups.

    This view is only visible by an admin.

    """

    layout = Layout(self, request)
    return {
        'layout': layout,
        'groups': self.query().all(),
        'title': _('Groups'),
        'new_group': request.link(self, name='new-group')
    }


@GazetteApp.form(
    model=UserGroupCollection,
    name='new-group',
    template='form.pt',
    permission=Private,
    form=UserGroupForm
)
def create_group(self, request, form):
    """ Create a new user group.

    This view is only visible by an admin.

    """

    layout = Layout(self, request)

    if form.submitted(request):
        self.add(name=form.name.data)
        request.message(_("Group added."), 'success')
        return redirect(layout.manage_groups_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New Group"),
        'cancel': layout.manage_groups_link
    }


@GazetteApp.form(
    model=UserGroup,
    name='edit',
    template='form.pt',
    permission=Private,
    form=UserGroupForm
)
def edit_group(self, request, form):
    """ Edit a user group.

    This view is only visible by an admin.

    """

    layout = Layout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_("Group modified."), 'success')
        return redirect(layout.manage_groups_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.name,
        'subtitle': _("Edit Group"),
        'cancel': layout.manage_groups_link
    }


@GazetteApp.form(
    model=UserGroup,
    name='delete',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def delete_group(self, request, form):
    """ Delete a user group.

    This view is only visible by an admin.

    """

    layout = Layout(self, request)

    if self.official_notices:
        request.message(
            _("There are official notices linked to this group!"),
            'warning'
        )

    if self.users.count():
        request.message(
            _('Only groups without users may be deleted.'),
            'alert'
        )
        return {
            'layout': layout,
            'title': self.name,
            'subtitle': _("Delete Group"),
            'show_form': False
        }

    if form.submitted(request):
        UserGroupCollection(request.session).delete(self)
        request.message(_("Group deleted."), 'success')
        return redirect(layout.manage_groups_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.name}
        ),
        'layout': layout,
        'form': form,
        'title': self.name,
        'subtitle': _("Delete Group"),
        'button_text': _("Delete Group"),
        'button_class': 'alert',
        'cancel': layout.manage_groups_link
    }
