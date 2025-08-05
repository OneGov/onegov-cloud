from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Public, Private
from onegov.org.forms import ParliamentarianForm
from onegov.org.forms import ParliamentarianRoleForm
from onegov.org.forms.commission_role import ParliamentarianCommissionRoleForm
from onegov.org.models import RISParliamentarian
from onegov.org.models import RISParliamentarianCollection
from onegov.org.models import PoliticalBusinessParticipationCollection
from onegov.parliament.collections import ParliamentarianCollection
from onegov.parliament.models import ParliamentarianRole, CommissionMembership
from onegov.town6 import _
from onegov.town6 import TownApp
from onegov.town6.layout import (
    RISParliamentarianCollectionLayout,
    RISParliamentarianLayout
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webob.response import Response
    from onegov.core.types import RenderData
    from onegov.pas.forms.parliamentarian import PASParliamentarianForm
    from onegov.parliament.models import Parliamentarian
    from onegov.pas.layouts import PASParliamentarianCollectionLayout
    from onegov.pas.layouts import PASParliamentarianLayout
    from onegov.town6.request import TownRequest


def view_parliamentarians(
    self: ParliamentarianCollection,
    request: TownRequest,
    layout: RISParliamentarianCollectionLayout
            | PASParliamentarianCollectionLayout
) -> RenderData | Response:

    filters = {}
    filters['active'] = [
        Link(
            text=request.translate(title),
            active=self.active == value,
            url=request.link(self.for_filter(active=value))
        ) for title, value in (
            (_('Active'), True),
            (_('Inactive'), False)
        )
    ]

    return {
        'add_link': request.link(self, name='new'),
        'filters': filters,
        'layout': layout,
        'parliamentarians': self.query().all(),
        'title': layout.title,
    }


def add_parliamentarian(
    self: ParliamentarianCollection,
    request: TownRequest,
    form: ParliamentarianForm | PASParliamentarianForm,
    layout: RISParliamentarianCollectionLayout
            | PASParliamentarianCollectionLayout
) -> RenderData | Response:

    if form.submitted(request):
        parliamentarian = self.add(**form.get_useful_data())
        request.success(_('Added a new parliamentarian'))

        return request.redirect(request.link(parliamentarian))

    layout.breadcrumbs.append(Link(_('New'), '#'))

    return {
        'layout': layout,
        'title': _('New parliamentarian'),
        'form': form,
        'form_width': 'large'
    }


def view_parliamentarian(
    self: Parliamentarian,
    request: TownRequest,
    layout: RISParliamentarianLayout | PASParliamentarianLayout
) -> RenderData | Response:

    return {
        'layout': layout,
        'parliamentarian': self,
        'title': layout.title,
    }


def edit_parliamentarian(
    self: Parliamentarian,
    request: TownRequest,
    form: ParliamentarianForm | PASParliamentarianForm,
    layout: RISParliamentarianLayout | PASParliamentarianLayout
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


def delete_parliamentarian(
    self: Parliamentarian,
    request: TownRequest,
) -> None:

    request.assert_valid_csrf_token()

    businesses = PoliticalBusinessParticipationCollection(request.session)
    businesses.by_parliamentarian_id(self.id).delete()

    parliamentarians = ParliamentarianCollection(request.session)
    parliamentarians.delete(self)

    request.success(_('The parliamentarian has been deleted.'))


def add_parliamentarian_group_membership(
    self: Parliamentarian,
    request: TownRequest,
    form: ParliamentarianRoleForm,
    layout: RISParliamentarianLayout | PASParliamentarianLayout
) -> RenderData | Response:

    form.delete_field('parliamentarian_id')

    if form.submitted(request):
        self.roles.append(
            ParliamentarianRole.get_polymorphic_class(
                # FIXME: We should probably just use `ris` and `pas`
                #        as the polymorphic types on every model
                #        then we can directly use them
                f'{self.type}_role',
                ParliamentarianRole
            )(**form.get_useful_data())
        )
        request.success(_('Added a new role'))
        return request.redirect(request.link(self))

    layout.breadcrumbs.append(Link(_('New parliamentary group membership'), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _('New parliamentary group membership'),
        'form': form,
        'form_width': 'large'
    }


def add_commission_membership(
    self: Parliamentarian,
    request: TownRequest,
    form: ParliamentarianCommissionRoleForm,
    layout: RISParliamentarianLayout
) -> RenderData | Response:
    form.delete_field('parliamentarian_id')

    if form.submitted(request):
        self.commission_memberships.append(
            CommissionMembership.get_polymorphic_class(
                # FIXME: We should probably just use `ris` and `pas`
                #        as the polymorphic types on every model
                #        then we can directly use them
                'ris_commission_membership',
                CommissionMembership
            )(**form.get_useful_data())
        )
        request.success(_('Added a new role'))
        return request.redirect(request.link(self))

    layout.breadcrumbs.append(Link(_('New commission membership'), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _('New commission membership'),
        'form': form,
        'form_width': 'large'
    }


@TownApp.html(
    model=RISParliamentarianCollection,
    template='parliamentarians.pt',
    permission=Public
)
def ris_view_parliamentarians(
    self: RISParliamentarianCollection,
    request: TownRequest
) -> RenderData | Response:

    layout = RISParliamentarianCollectionLayout(self, request)
    return view_parliamentarians(self, request, layout)


@TownApp.form(
    model=RISParliamentarianCollection,
    name='new',
    template='form.pt',
    permission=Public,
    form=ParliamentarianForm
)
def ris_add_parliamentarian(
    self: RISParliamentarianCollection,
    request: TownRequest,
    form: ParliamentarianForm
) -> RenderData | Response:

    layout = RISParliamentarianCollectionLayout(self, request)
    return add_parliamentarian(self, request, form, layout)


@TownApp.html(
    model=RISParliamentarian,
    template='parliamentarian.pt',
    permission=Public
)
def ris_view_parliamentarian(
    self: RISParliamentarian,
    request: TownRequest
) -> RenderData | Response:

    layout = RISParliamentarianLayout(self, request)
    return view_parliamentarian(self, request, layout)


@TownApp.form(
    model=RISParliamentarian,
    name='edit',
    template='form.pt',
    permission=Private,
    form=ParliamentarianForm
)
def ris_edit_parliamentarian(
    self: RISParliamentarian,
    request: TownRequest,
    form: ParliamentarianForm
) -> RenderData | Response:

    layout = RISParliamentarianLayout(self, request)
    return edit_parliamentarian(self, request, form, layout)


@TownApp.view(
    model=RISParliamentarian,
    request_method='DELETE',
    permission=Private
)
def ris_delete_parliamentarian(
    self: RISParliamentarian,
    request: TownRequest
) -> None:

    return delete_parliamentarian(self, request)


@TownApp.form(
    model=RISParliamentarian,
    name='new-role',  # change to 'add-group-role'
    template='form.pt',
    permission=Private,
    form=ParliamentarianRoleForm
)
def ris_add_parliamentary_group_membership(
    self: RISParliamentarian,
    request: TownRequest,
    form: ParliamentarianRoleForm
) -> RenderData | Response:

    layout = RISParliamentarianLayout(self, request)
    return add_parliamentarian_group_membership(self, request, form, layout)


@TownApp.form(
    model=RISParliamentarian,
    name='new-commission-role',  # change to 'add-group-role'
    template='form.pt',
    permission=Private,
    form=ParliamentarianCommissionRoleForm
)
def ris_add_commission_membership(
    self: RISParliamentarian,
    request: TownRequest,
    form: ParliamentarianCommissionRoleForm
) -> RenderData | Response:

    layout = RISParliamentarianLayout(self, request)
    return add_commission_membership(self, request, form, layout)
