from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Public, Private
from onegov.org.models import (
    RISParliamentaryGroup,
    RISParliamentaryGroupCollection
)
from onegov.org.forms.parliamentary_group import ParliamentaryGroupForm
from onegov.parliament.collections import ParliamentaryGroupCollection
from onegov.town6 import _
from onegov.town6 import TownApp
from onegov.town6.layout import (
    RISParliamentaryGroupCollectionLayout,
    RISParliamentaryGroupLayout
)
from webob.exc import HTTPNotFound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.parliament.models import ParliamentaryGroup
    from onegov.pas.layouts import PASParliamentaryGroupLayout
    from onegov.pas.layouts import PASParliamentaryGroupCollectionLayout
    from onegov.town6.request import TownRequest
    from webob.response import Response


def view_parliamentary_groups(
    self: ParliamentaryGroupCollection,
    request: TownRequest,
    layout: RISParliamentaryGroupCollectionLayout
            | PASParliamentaryGroupCollectionLayout
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
        'parliamentary_groups': self.query().all(),
        'title': layout.title,
    }


def add_parliamentary_group(
    self: ParliamentaryGroupCollection,
    request: TownRequest,
    form: ParliamentaryGroupForm,
    layout: RISParliamentaryGroupCollectionLayout
            | PASParliamentaryGroupCollectionLayout
) -> RenderData | Response:

    if form.submitted(request):
        parliamentary_group = self.add(**form.get_useful_data())
        request.success(_('Added a new parliamentary group'))

        return request.redirect(request.link(parliamentary_group))

    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.include_editor()
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('New parliamentary group'),
        'form': form,
        'form_width': 'large'
    }


def view_parliamentary_group(
    self: ParliamentaryGroup,
    request: TownRequest,
    layout: RISParliamentaryGroupLayout | PASParliamentaryGroupLayout
) -> RenderData | Response:

    active_roles = [
        role for role in self.roles if not role.end
    ]

    return {
        'layout': layout,
        'parliamentary_group': self,
        'active_roles': active_roles,
        'title': layout.title,
    }


def edit_parliamentary_group(
    self: ParliamentaryGroup,
    request: TownRequest,
    form: ParliamentaryGroupForm,
    layout: RISParliamentaryGroupLayout | PASParliamentaryGroupLayout
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []
    layout.include_editor()
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


def delete_parliamentary_group(
    self: ParliamentaryGroup,
    request: TownRequest
) -> None:

    request.assert_valid_csrf_token()

    collection = ParliamentaryGroupCollection(request.session)
    collection.delete(self)

    request.success(_('The parliamentary group has been deleted.'))


@TownApp.html(
    model=RISParliamentaryGroupCollection,
    template='parliamentary_groups.pt',
    permission=Public
)
def ris_view_parliamentary_groups(
    self: RISParliamentaryGroupCollection,
    request: TownRequest
) -> RenderData | Response:

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return view_parliamentary_groups(
        self, request, RISParliamentaryGroupCollectionLayout(self, request)
    )


@TownApp.form(
    model=RISParliamentaryGroupCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=ParliamentaryGroupForm
)
def ris_add_parliamentary_group(
    self: RISParliamentaryGroupCollection,
    request: TownRequest,
    form: ParliamentaryGroupForm
) -> RenderData | Response:

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return add_parliamentary_group(
        self,
        request,
        form,
        RISParliamentaryGroupCollectionLayout(self, request)
    )


@TownApp.html(
    model=RISParliamentaryGroup,
    template='parliamentary_group.pt',
    permission=Public
)
def ris_view_parliamentary_group(
    self: RISParliamentaryGroup,
    request: TownRequest
) -> RenderData | Response:

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return view_parliamentary_group(
        self, request, RISParliamentaryGroupLayout(self, request)
    )


@TownApp.form(
    model=RISParliamentaryGroup,
    name='edit',
    template='form.pt',
    permission=Private,
    form=ParliamentaryGroupForm
)
def ris_edit_parliamentary_group(
    self: RISParliamentaryGroup,
    request: TownRequest,
    form: ParliamentaryGroupForm
) -> RenderData | Response:

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return edit_parliamentary_group(
        self, request, form, RISParliamentaryGroupLayout(self, request)
    )


@TownApp.view(
    model=RISParliamentaryGroup,
    request_method='DELETE',
    permission=Private
)
def ris_delete_parliamentary_group(
    self: RISParliamentaryGroup,
    request: TownRequest
) -> None:

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return delete_parliamentary_group(self, request)
