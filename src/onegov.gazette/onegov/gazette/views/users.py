from morepath import redirect
from onegov.core.crypto import random_password
from onegov.core.security import Secret
from onegov.core.templates import render_template
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.forms import EmptyForm
from onegov.gazette.forms import UserForm
from onegov.gazette.layout import Layout
from onegov.gazette.layout import MailLayout
from onegov.user import User
from onegov.user import UserCollection
from onegov.user.utils import password_reset_url


@GazetteApp.html(
    model=UserCollection,
    template='users.pt',
    permission=Secret
)
def view_users(self, request):
    """ View all the publishers and editors (but not the admins).

    This view is only visible by an admin.

    """

    layout = Layout(self, request)
    roles = [
        (_("Publishers"), self.for_filter(role='editor').query().all()),
        (_("Editors"), self.for_filter(role='member').query().all())
    ]
    return {
        'layout': layout,
        'roles': roles,
        'title': _('Users'),
        'new_user': request.link(self, name='new-user')
    }


@GazetteApp.form(
    model=UserCollection,
    name='new-user',
    template='form.pt',
    permission=Secret,
    form=UserForm
)
def create_user(self, request, form):
    """ Create a new publisher or editor.

    This view is only visible by an admin.

    """

    layout = Layout(self, request)

    if form.submitted(request):
        user = self.add(
            form.email.data,
            random_password(16),
            form.role.data,
            realname=form.name.data
        )
        form.update_model(user)
        user.modified = user.timestamp()
        url = password_reset_url(
            user,
            request,
            request.link(request.app.principal, name='reset-password')
        )
        request.app.send_email(
            subject=request.translate(_("User account created")),
            receivers=(user.username, ),
            reply_to=request.app.mail_sender,
            content=render_template(
                'mail_user_created.pt',
                request,
                {
                    'title': request.translate(_("User account created")),
                    'model': None,
                    'url': url,
                    'layout': MailLayout(self, request)
                }
            )
        )

        request.message(_("User added."), 'success')
        return redirect(layout.manage_users_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New User"),
        'cancel': layout.manage_users_link
    }


@GazetteApp.form(
    model=User,
    name='edit',
    template='form.pt',
    permission=Secret,
    form=UserForm
)
def edit_user(self, request, form):
    """ Edit the role, name and email of an editor or publisher.

    This view is only visible by an admin.

    """

    layout = Layout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_("User modified."), 'success')
        return redirect(layout.manage_users_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Edit User"),
        'cancel': layout.manage_users_link
    }


@GazetteApp.form(
    model=User,
    name='delete',
    template='form.pt',
    permission=Secret,
    form=EmptyForm
)
def delete_user(self, request, form):
    """ Delete an editor or publisher (but not admins).

    This view is only visible by an admin.

    """

    layout = Layout(self, request)

    callout = None
    if self.official_notices or self.changes:
        callout = _("There are official notices linked to this user!")

    if form.submitted(request):
        collection = UserCollection(request.app.session())
        user = collection.by_username(self.username)
        if user.role != 'admin':
            collection.delete(self.username)
            request.message(_("User deleted."), 'success')
        return redirect(layout.manage_users_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Delete User"),
        'callout': callout,
        'button_text': _("Delete User"),
        'button_class': 'alert',
        'cancel': layout.manage_users_link
    }
