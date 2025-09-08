from __future__ import annotations
from itertools import groupby
from operator import attrgetter
import uuid

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import AttendenceCollection
from onegov.pas.forms import AttendenceAddCommissionBulkForm, AttendenceAddForm
from onegov.pas.forms import AttendenceAddPlenaryForm
from onegov.pas.forms import AttendenceForm
from onegov.pas.forms.attendence import AttendenceEditBulkForm
from onegov.pas.layouts import AttendenceCollectionLayout
from onegov.pas.layouts import AttendenceLayout
from onegov.pas.models import Attendence
from onegov.pas.models import Change

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=AttendenceCollection,
    template='attendences.pt',
    permission=Private
)
def view_attendences(
    self: AttendenceCollection,
    request: TownRequest
) -> RenderData:

    layout = AttendenceCollectionLayout(self, request)

    all_attendances = self.query().order_by(Attendence.created.desc()).all()
    bulk_edit_groups = [
        list(group) 
        for bulk_edit_id, group in groupby(all_attendances, key=attrgetter(
            'bulk_edit_id'))
    ]

    return {
        'add_link': request.link(self, name='new'),
        'layout': layout,
        'attendences': all_attendances,
        'title': layout.title,
        'bulk_edit_groups': bulk_edit_groups
    }


@PasApp.form(
    model=AttendenceCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=AttendenceAddForm
)
def add_attendence(
    self: AttendenceCollection,
    request: TownRequest,
    form: AttendenceAddForm
) -> RenderData | Response:

    if form.submitted(request):
        attendence = self.add(**form.get_useful_data())
        Change.add(request, 'add', attendence)
        request.success(_('Added a new attendence'))

        return request.redirect(request.link(attendence))

    layout = AttendenceCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('New attendence'),
        'form': form,
        'form_width': 'large'
    }


@PasApp.form(
    model=AttendenceCollection,
    name='new-commission-bulk',
    template='form.pt',
    permission=Private,
    form=AttendenceAddCommissionBulkForm
)
def add_bulk_attendence(
    self: AttendenceCollection,
    request: TownRequest,
    form: AttendenceAddCommissionBulkForm
) -> RenderData | Response:
    request.include('custom')

    if form.submitted(request):

        data = form.get_useful_data()
        if raw_parl_ids := request.POST.getall('parliamentarian_id'):
            # Remove static field; choices are set dynamically via JS
            data.pop('parliamentarian_id', None)
            bulk_edit_id = uuid.uuid4()
            for parliamentarian_id in raw_parl_ids:
                attendence = self.add(
                    parliamentarian_id=parliamentarian_id, **data
                )
                attendence.bulk_edit_id = bulk_edit_id
                Change.add(request, 'add', attendence)
        else:
            request.warning(_('No parliamentarians selected'))
            return request.redirect(request.class_link(AttendenceCollection))

        request.success(_('Added commission session'))

        return request.redirect(request.link(self))

    layout = AttendenceCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New commission session'), '#'))
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('New commission session'),
        'form': form,
        'form_width': 'large'
    }


@PasApp.form(
    model=Attendence,
    name='edit-bulk-attendences',
    template='form.pt',
    permission=Private,
    form=AttendenceEditBulkForm 
)
def edit_bulk_attendence(
    self: Attendence,
    request: TownRequest,
    form: AttendenceEditBulkForm
) -> RenderData | Response:
    request.include('custom')

    if form.submitted(request):

        data = form.get_useful_data()
        if raw_parl_ids := request.POST.getall('parliamentarian_id'):
            # Remove static field; choices are set dynamically via JS
            all_parliamentarians = data.pop('parliamentarian_id', None)
            if self.type == 'plenary':
                unselected_parliamentarians = [
                    pid for pid in all_parliamentarians
                    if pid not in raw_parl_ids
                ]
                for parliamentarian in unselected_parliamentarians:
                    attendences = AttendenceCollection(request.session
                                                       ).query().filter(
                        Attendence.parliamentarian_id == parliamentarian,
                        Attendence.bulk_edit_id == form.bulk_edit_id.data,
                    ).first()
                    for attendence in attendences:
                        Change.add(request, 'delete', attendence)
                        request.delete(attendence)
            return request.redirect(request.class_link(AttendenceCollection))

        request.success(_('Added commission session'))

        return request.redirect(request.link(self))
    elif not request.POST:
        form.process(obj=self)

    layout = AttendenceCollectionLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Attendences'), request.class_link(AttendenceCollection)),
        Link(_('Edit commission session'), '#')
    ]
    layout.edit_mode = True
    layout.editmode_links.append(
        Link(
            _('Delete'),
            request.class_link(AttendenceCollection) # Needs to be created
        )
    )

    return {
        'layout': layout,
        'title': _('Edit commission session'),
        'form': form,
        'form_width': 'large'
    }


@PasApp.form(
    model=AttendenceCollection,
    name='new-bulk',
    template='form.pt',
    permission=Private,
    form=AttendenceAddPlenaryForm
)
def add_plenary_attendence(
    self: AttendenceCollection,
    request: TownRequest,
    form: AttendenceAddPlenaryForm
) -> RenderData | Response:

    if form.submitted(request):
        data = form.get_useful_data()
        if raw_parl_ids := request.POST.getall('parliamentarian_id'):
            # Remove static field; choices are set dynamically via JS
            data.pop('parliamentarian_id', None)
            bulk_edit_id = uuid.uuid4()
            for parliamentarian_id in raw_parl_ids:
                attendence = self.add(
                    parliamentarian_id=parliamentarian_id, **data
                )
                attendence.bulk_edit_id = bulk_edit_id
                Change.add(request, 'add', attendence)
            request.success(_('Added plenary session'))

        return request.redirect(request.link(self))

    layout = AttendenceCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New plenary session'), '#'))
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('New plenary session'),
        'form': form,
        'form_width': 'large'
    }


@PasApp.html(
    model=Attendence,
    template='attendence.pt',
    permission=Private
)
def view_attendence(
    self: Attendence,
    request: TownRequest
) -> RenderData:

    layout = AttendenceLayout(self, request)

    return {
        'layout': layout,
        'attendence': self,
        'title': layout.title,
    }


@PasApp.form(
    model=Attendence,
    name='edit',
    template='form.pt',
    permission=Private,
    form=AttendenceForm
)
def edit_attendence(
    self: Attendence,
    request: TownRequest,
    form: AttendenceForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        Change.add(request, 'edit', self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = AttendenceLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.edit_mode = True   

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@PasApp.view(
    model=Attendence,
    request_method='DELETE',
    permission=Private
)
def delete_attendence(
    self: Attendence,
    request: TownRequest
) -> None:

    request.assert_valid_csrf_token()

    Change.add(request, 'delete', self)
    collection = AttendenceCollection(request.session)
    collection.delete(self)
