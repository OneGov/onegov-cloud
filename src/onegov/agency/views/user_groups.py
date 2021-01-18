from morepath import redirect
from onegov.agency import _
from onegov.agency import AgencyApp
from onegov.agency.forms import UserGroupForm
from onegov.agency.layout import UserGroupCollectionLayout
from onegov.agency.layout import UserGroupLayout
from onegov.agency.models import ExtendedAgency
from onegov.core.elements import Link
from onegov.core.security import Secret
from onegov.user import UserGroup
from onegov.user import UserGroupCollection


@AgencyApp.html(
    model=UserGroupCollection,
    template='user_groups.pt',
    permission=Secret
)
def view_user_groups(self, request):
    layout = UserGroupCollectionLayout(self, request)

    # todo: Add organization filter
    # todo: Add user filter

    return {
        'layout': layout,
        'title': _('User Groups'),
        'groups': self.query().all()
    }


@AgencyApp.form(
    model=UserGroupCollection,
    name='new',
    template='form.pt',
    permission=Secret,
    form=UserGroupForm
)
def add_user_group(self, request, form):
    if form.submitted(request):
        user_group = self.add(name=form.name.data)
        request.success(_('Added a new user group'))
        return redirect(request.link(user_group))

    layout = UserGroupCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New user group'), '#'))

    return {
        'layout': layout,
        'title': _('New user group'),
        'form': form
    }


@AgencyApp.html(
    model=UserGroup,
    template='user_group.pt',
    permission=Secret
)
def view_user_group(self, request):
    layout = UserGroupLayout(self, request)
    agencies = [
        agency.title for agency in request.session.query(
            ExtendedAgency.title
        ).filter(
            ExtendedAgency.id.in_([m.content_id for m in self.role_mappings])
        )
    ]

    return {
        'layout': layout,
        'title': self.name,
        'agencies': agencies
    }


@AgencyApp.form(
    model=UserGroup,
    name='edit',
    template='form.pt',
    permission=Secret,
    form=UserGroupForm
)
def edit_user_group(self, request, form):
    if form.submitted(request):
        form.update_model(self)
        request.success(_('Your changes were saved'))
        return redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    layout = UserGroupLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit user group'), '#'))

    return {
        'layout': layout,
        'title': _('Edit user group'),
        'form': form
    }


@AgencyApp.view(
    model=UserGroup,
    request_method='DELETE',
    permission=Secret
)
def delete_user_group(self, request):
    request.assert_valid_csrf_token()
    UserGroupCollection(request.session).delete(self)
