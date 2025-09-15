from __future__ import annotations

from io import BytesIO
from morepath import redirect
from morepath.request import Response
from onegov.core.crypto import random_password
from onegov.core.security import Private
from onegov.core.security import Secret
from onegov.core.templates import render_template
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.forms import EmptyForm
from onegov.gazette.forms import UserForm
from onegov.gazette.forms.user import ExportUsersForm
from onegov.gazette.layout import Layout
from onegov.gazette.layout import MailLayout
from onegov.user import User
from onegov.user import UserCollection
from onegov.user import UserGroup
from onegov.user.utils import password_reset_url
from sedate import utcnow
from sqlalchemy.orm import contains_eager
from webob.exc import HTTPForbidden
from xlsxwriter import Workbook


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.gazette.request import GazetteRequest
    from webob import Response as BaseResponse


@GazetteApp.html(
    model=UserCollection,
    template='users.pt',
    permission=Private
)
def view_users(
    self: UserCollection,
    request: GazetteRequest
) -> RenderData:
    """ View the users.

    Publishers can see editors, admins can see editors and publishers. Admins
    are never shown.

    """

    layout = Layout(self, request)
    roles = [
        (
            _('Editors'),
            self.for_filter(role='member').query().order_by(
                User.username
            ).all()
        )
    ]
    if request.is_secret(self):
        roles.append(
            (
                _('Publishers'),
                self.for_filter(role='editor').query().order_by(
                    User.username
                ).all()
            )
        )
    return {
        'layout': layout,
        'roles': roles,
        'title': _('Users'),
        'export': request.link(self, name='export'),
        'new_user': request.link(self, name='new-user')
    }


@GazetteApp.form(
    model=UserCollection,
    name='new-user',
    template='form.pt',
    permission=Private,
    form=UserForm
)
def create_user(
    self: UserCollection,
    request: GazetteRequest,
    form: UserForm
) -> RenderData | BaseResponse:
    """ Create a new publisher or editor.

    This view is visible for admins and publishers.

    """

    layout = Layout(self, request)

    if form.submitted(request):
        assert form.username.data is not None
        user = self.add(
            form.username.data,
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
        assert request.app.mail is not None
        request.app.send_transactional_email(
            subject=request.translate(_('User account created')),
            receivers=(user.username, ),
            reply_to=request.app.mail['transactional']['sender'],
            content=render_template(
                'mail_user_created.pt',
                request,
                {
                    'title': request.translate(_('User account created')),
                    'model': None,
                    'url': url,
                    'layout': MailLayout(self, request)
                }
            )
        )

        request.message(_('User added.'), 'success')
        return redirect(layout.manage_users_link)

    return {
        'layout': layout,
        'form': form,
        'title': _('New User'),
        'cancel': layout.manage_users_link
    }


@GazetteApp.form(
    model=User,
    name='edit',
    template='form.pt',
    permission=Private,
    form=UserForm
)
def edit_user(
    self: User,
    request: GazetteRequest,
    form: UserForm
) -> RenderData | BaseResponse:
    """ Edit the role, name and email of a user.

    Publishers may only edit members. Admins can not be edited.

    """

    layout = Layout(self, request)

    if self.role != 'member' and not request.is_secret(self):
        raise HTTPForbidden()

    if form.submitted(request):
        form.update_model(self)
        self.logout_all_sessions(request.app)
        request.message(_('User modified.'), 'success')
        return redirect(layout.manage_users_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _('Edit User'),
        'cancel': layout.manage_users_link
    }


@GazetteApp.form(
    model=User,
    name='delete',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def delete_user(
    self: User,
    request: GazetteRequest,
    form: EmptyForm
) -> RenderData | BaseResponse:
    """ Delete a user.

    Publishers may only edit members. Admins can not be deleted.

    """

    layout = Layout(self, request)

    if self.role != 'member' and not request.is_secret(self):
        raise HTTPForbidden()

    # FIXME: backrefs created across module boundaries
    if self.official_notices or self.changes:  # type:ignore[attr-defined]
        request.message(
            _('There are official notices linked to this user!'),
            'warning'
        )

    if form.submitted(request):
        collection = UserCollection(request.session)
        # FIXME: Why are we re-fetching the user to check its role?
        user = collection.by_username(self.username)
        assert user is not None
        if user.role != 'admin':
            self.logout_all_sessions(request.app)
            collection.delete(self.username)
            request.message(_('User deleted.'), 'success')
        return redirect(layout.manage_users_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _('Delete User'),
        'button_text': _('Delete User'),
        'button_class': 'alert',
        'cancel': layout.manage_users_link
    }


@GazetteApp.html(
    model=UserCollection,
    name='sessions',
    template='sessions.pt',
    permission=Secret
)
def view_user_sessions(
    self: UserCollection,
    request: GazetteRequest
) -> RenderData:
    """ View all open browser sessions.

    This view is only visible by an admin.

    """

    layout = Layout(self, request)
    return {
        'layout': layout,
        'title': _('Sessions'),
        'users': self.query().all()
    }


@GazetteApp.form(
    model=User,
    name='clear-sessions',
    template='form.pt',
    permission=Secret,
    form=EmptyForm
)
def clear_user_sessions(
    self: User,
    request: GazetteRequest,
    form: EmptyForm
) -> RenderData | BaseResponse:
    """ Closes all open browser sessions.

    This view is only visible by an admin.

    """

    layout = Layout(self, request)
    cancel = request.link(
        UserCollection(request.session), name='sessions'
    )

    if form.submitted(request):
        self.logout_all_sessions(request.app)
        return redirect(cancel)

    return {
        'message': _('Do you really clear all active sessions?'),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _('Clear Sessions'),
        'button_text': _('Clear Sessions'),
        'button_class': 'alert',
        'cancel': cancel
    }


@GazetteApp.form(
    model=UserCollection,
    name='export',
    permission=Private,
    form=ExportUsersForm,
    template='export.pt'
)
def export_users(
    self: UserCollection,
    request: GazetteRequest,
    form: ExportUsersForm
) -> RenderData | Response:
    """ Export all users as XLSX. The exported file can be re-imported
    using the import-editors command line command.

    """
    if form.submitted(request):
        output = BytesIO()
        workbook = Workbook(output)

        for role, name in (
            ('member', request.translate(_('Editors'))),
            ('editor', request.translate(_('Publishers')))
        ):
            worksheet = workbook.add_worksheet(name)
            worksheet.write_row(0, 0, (
                request.translate(_('Group')),
                request.translate(_('Name')),
                request.translate(_('E-Mail'))
            ))

            users = self.query().filter(User.role == role)
            group_ids = form.group_names.data
            if group_ids:
                users = users.join(User.groups)
                users = users.filter(UserGroup.id.in_(group_ids))
            else:
                users = users.outerjoin(User.groups)

            users = users.order_by(
                UserGroup.name,
                User.realname,
                User.username
            )
            users = users.options(contains_eager(User.groups))
            for index, user in enumerate(users):
                worksheet.write_row(index + 1, 0, (
                    '|'.join(g.name for g in user.groups if g.name),
                    user.realname or '',
                    user.username or ''
                ))

        workbook.close()
        output.seek(0)

        response = Response()
        response.content_type = (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response.content_disposition = 'inline; filename={}-{}.xlsx'.format(
            request.translate(_('Users')).lower(),
            utcnow().strftime('%Y%m%d%H%M')
        )
        response.body = output.read()
        return response

    return {
        'form': form,
        'layout': Layout(self, request),
        'title': _('Export Users'),
        'button_text': _('Export'),
        'callout': _('Export users by groups or leave empty '
                     'for un unfiltered export.')
    }
