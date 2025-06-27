from __future__ import annotations

from onegov.core.elements import Link
from onegov.parliament import _
from onegov.parliament.collections import ParliamentarianCollection
from onegov.parliament.models import RISParliamentarian
from onegov.parliament.models import RISParliamentarianRole
from onegov.pas.models import PASParliamentarian
from onegov.pas.models import PASParliamentarianRole

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from webob import Response

    from onegov.parliament.forms import ParliamentarianForm
    from onegov.parliament.forms import PASParliamentarianForm
    from onegov.parliament.forms import ParliamentarianRoleForm
    from onegov.pas.layouts import (
        PASParliamentarianCollectionLayout,
        PASParliamentarianLayout
    )
    from onegov.town6.layout import (
        RISParliamentarianCollectionLayout,
        RISParliamentarianLayout
    )
    from onegov.town6.request import TownRequest


def view_parliamentarians(
    self: ParliamentarianCollection,
    request: TownRequest,
    layout: RISParliamentarianCollectionLayout |
            PASParliamentarianCollectionLayout
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
    layout: RISParliamentarianCollectionLayout |
            PASParliamentarianCollectionLayout
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
    self: RISParliamentarian | PASParliamentarian,
    request: TownRequest,
    layout: RISParliamentarianLayout | PASParliamentarianLayout
) -> RenderData | Response:

    return {
        'layout': layout,
        'parliamentarian': self,
        'title': layout.title,
    }


def edit_parliamentarian(
    self: RISParliamentarian | PASParliamentarian,
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
    self: RISParliamentarian | PASParliamentarian,
    request: TownRequest,
) -> None:

    request.assert_valid_csrf_token()

    collection = ParliamentarianCollection(request.session)
    collection.delete(self)


def add_commission_membership(
    self: RISParliamentarian | PASParliamentarian,
    request: TownRequest,
    form: ParliamentarianRoleForm,
    layout: RISParliamentarianLayout | PASParliamentarianLayout

) -> RenderData | Response:

    form.delete_field('parliamentarian_id')

    if form.submitted(request):
        if isinstance(self, RISParliamentarian):
            self.roles.append(
                RISParliamentarianRole(**form.get_useful_data())
            )
        elif isinstance(self, PASParliamentarian):
            self.roles.append(
                PASParliamentarianRole(**form.get_useful_data())
            )
        else:
            raise NotImplementedError(
                'Unknown parliamentarian type: {}'.format(type(self))
            )
        request.success(_('Added a new role'))
        return request.redirect(request.link(self))

    layout.breadcrumbs.append(Link(_('New role'), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _('New role'),
        'form': form,
        'form_width': 'large'
    }
