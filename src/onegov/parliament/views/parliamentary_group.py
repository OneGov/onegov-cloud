from __future__ import annotations

from onegov.core.elements import Link
from onegov.parliament import _
from onegov.parliament.collections.parliamentary_group import (
    ParliamentaryGroupCollection
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webob.response import Response

    from onegov.core.types import RenderData
    from onegov.parliament.forms.parliamentary_group import (
        ParliamentaryGroupForm
    )
    from onegov.parliament.models import ParliamentaryGroup
    from onegov.pas.layouts import (
        PASParliamentaryGroupCollectionLayout,
        PASParliamentaryGroupLayout
    )
    from onegov.town6.layout import (
        RISParliamentaryGroupCollectionLayout,
        RISParliamentaryGroupLayout
    )
    from onegov.town6.request import TownRequest


def view_parliamentary_groups(
    self: ParliamentaryGroupCollection,
    request: TownRequest,
    layout: RISParliamentaryGroupCollectionLayout |
            PASParliamentaryGroupCollectionLayout
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
    layout: RISParliamentaryGroupCollectionLayout |
            PASParliamentaryGroupCollectionLayout
) -> RenderData | Response:

    if form.submitted(request):
        parliamentary_group = self.add(**form.get_useful_data())
        request.success(_('Added a new parliamentary group'))

        return request.redirect(request.link(parliamentary_group))

    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.include_editor()

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

    return {
        'layout': layout,
        'parliamentary_group': self,
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
