from __future__ import annotations

from itertools import groupby
from operator import attrgetter
import uuid

from more_itertools import flatten

from onegov.core.elements import BackLink, Confirm, Intercooler, Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import (AttendenceCollection,
                                    PASParliamentarianCollection)
from onegov.pas.custom import check_attendance_in_closed_settlement_run
from onegov.pas.forms import AttendenceAddCommissionBulkForm, AttendenceAddForm
from onegov.pas.forms import AttendenceAddPlenaryForm
from onegov.pas.forms import AttendenceForm
from onegov.pas.forms.attendence import (AttendenceCommissionBulkEditForm,
                                         AttendencePlenaryBulkEditForm)
from onegov.pas.layouts import AttendenceCollectionLayout
from onegov.pas.layouts import AttendenceLayout
from onegov.pas.models import Attendence
from onegov.pas.models import Change
from onegov.pas.models import SettlementRun
from onegov.pas.models.commission_membership import PASCommissionMembership


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from onegov.pas.request import PasRequest
    from webob import Response


@PasApp.html(
    model=AttendenceCollection,
    template='attendences.pt',
    permission=Private
)
def view_attendences(
    self: AttendenceCollection,
    request: PasRequest
) -> RenderData:

    layout = AttendenceCollectionLayout(self, request)

    # Apply role-based filtering, then re-sort for bulk edit grouping
    filtered_attendences = self.view_for_parliamentarian(request)
    bulk_edit_attendences = sorted(
        filtered_attendences,
        key=lambda x: (str(x.bulk_edit_id) if x.bulk_edit_id else '',
                      x.created or x.modified),
        reverse=True
    )

    bulk_edit_groups = [
        sorted(group, key=attrgetter('created', 'modified'), reverse=True)
        for bulk_edit_id, group in groupby(
            bulk_edit_attendences, key=attrgetter('bulk_edit_id'))
    ]

    non_null_groups = [g for g in bulk_edit_groups if getattr(
        g[0], 'bulk_edit_id', None) is not None]
    null_groups = [g for g in bulk_edit_groups if getattr(
        g[0], 'bulk_edit_id', None) is None]

    non_null_groups.sort(
        key=lambda group: max(  # type: ignore
            (attendence.modified or attendence.created
             for attendence in group),
            default=None
        ),
        reverse=True
    )

    bulk_edit_groups = non_null_groups + null_groups

    return {
        'add_link': request.link(self, name='new'),
        'layout': layout,
        'attendences': list(flatten(bulk_edit_groups)),
        'title': layout.title,
        'bulk_edit_groups': bulk_edit_groups
    }


@PasApp.form(
    model=AttendenceCollection,
    name='new',
    template='form.pt',
    form=AttendenceAddForm
)
def add_attendence(
    self: AttendenceCollection,
    request: PasRequest,
    form: AttendenceAddForm
) -> RenderData | Response:
    request.include('custom')

    if form.submitted(request):
        # Check if attendance date is in a closed settlement run
        if form.date.data:
            if check_attendance_in_closed_settlement_run(
                request.session, form.date.data
            ):
                request.alert(
                    _('Cannot create attendance in closed settlement run.')
                )
                return {
                    'layout': AttendenceCollectionLayout(self, request),
                    'title': _('New attendence'),
                    'form': form,
                    'form_width': 'large'
                }

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
        # Check if attendance date is in a closed settlement run
        if form.date.data:
            if check_attendance_in_closed_settlement_run(
                request.session, form.date.data
            ):
                request.alert(
                    _('Cannot create attendance in closed settlement run.')
                )
                return {
                    'layout': AttendenceCollectionLayout(self, request),
                    'title': _('New commission session'),
                    'form': form,
                    'form_width': 'large'
                }

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
    name='edit-plenary-bulk-attendences',
    template='form.pt',
    permission=Private,
    form=AttendencePlenaryBulkEditForm
)
def edit_plenary_bulk_attendence(
    self: Attendence,
    request: TownRequest,
    form: AttendencePlenaryBulkEditForm
) -> RenderData | Response:
    request.include('custom')

    if not request.is_admin:
        request.alert(
            _('You do not have permission to edit plenary sessions.')
        )
        return request.redirect(request.class_link(AttendenceCollection))

    all_parliamentarians = [
        str(parliamentarian.id)
        for parliamentarian
        in PASParliamentarianCollection(
            request.app, active=[True]).query()
    ]

    if form.submitted(request):
        # Check if attendance date is in a closed settlement run
        if form.date.data:
            if check_attendance_in_closed_settlement_run(
                request.session, form.date.data
            ):
                request.alert(
                    _('Cannot edit attendance in closed settlement run.')
                )
                return {
                    'layout': AttendenceCollectionLayout(self, request),
                    'title': _('Edit plenary session'),
                    'form': form,
                    'form_width': 'large'
                }

        data = form.get_useful_data()
        raw_parl_ids = request.POST.getall('parliamentarian_id')
        data.pop('parliamentarian_id', None)
        collection = AttendenceCollection(request.session)

        unselected_parliamentarians = [
            pid for pid in all_parliamentarians
            if pid not in raw_parl_ids
        ]
        for parliamentarian in unselected_parliamentarians:
            if attendence := collection.query().filter(
                    Attendence.parliamentarian_id == parliamentarian,
                    Attendence.bulk_edit_id == form.bulk_edit_id.data,
                ).first():
                Change.add(request, 'delete', attendence)
                collection.delete(attendence)

        for parliamentarian_id in raw_parl_ids:
            attendence = collection.query().filter(
                    Attendence.parliamentarian_id == parliamentarian_id,
                    Attendence.bulk_edit_id == form.bulk_edit_id.data,
                ).first()
            if attendence:
                form.populate_obj(attendence)
                Change.add(request, 'edit', attendence)
            else:
                attendence = collection.add(
                    parliamentarian_id=parliamentarian_id, **data
                )
                Change.add(request, 'add', attendence)

        request.success(_('Edited attendences'))
        return request.redirect(request.class_link(AttendenceCollection))

    elif not request.POST:
        form.process(obj=self)

    layout = AttendenceCollectionLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Attendences'), request.class_link(AttendenceCollection)),
        Link(_('Edit session'), '#')
    ]
    layout.edit_mode = True
    layout.editmode_links[1] = BackLink(
        attrs={'class': 'cancel-link'},
    )
    layout.editmode_links.append(
        Link(
            text=_('Delete'),
            url=layout.csrf_protected_url(
                request.link(self, name='delete-attendences')),
            traits=(
                Confirm(
                    _(
                        'Do you really want to delete this bulk edit?'
                    ),
                    _('This cannot be undone.'),
                    _('Delete Attendencess'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='DELETE',
                    redirect_after=request.class_link(AttendenceCollection)
                )),
            attrs={'class': 'delete-link'},
        )
    )

    return {
        'layout': layout,
        'title': _('Edit plenary session'),
        'form': form,
        'form_width': 'large'
    }


@PasApp.form(
    model=Attendence,
    name='edit-commission-bulk-attendences',
    template='form.pt',
    permission=Private,
    form=AttendenceCommissionBulkEditForm
)
def edit_commission_bulk_attendence(
    self: Attendence,
    request: TownRequest,
    form: AttendenceCommissionBulkEditForm
) -> RenderData | Response:
    request.include('custom')

    if form.submitted(request):
        # Check if attendance date is in a closed settlement run
        if form.date.data:
            if check_attendance_in_closed_settlement_run(
                request.session, form.date.data
            ):
                request.alert(
                    _('Cannot edit attendance in closed settlement run.')
                )
                return {
                    'layout': AttendenceCollectionLayout(self, request),
                    'title': _('Edit commission session'),
                    'form': form,
                    'form_width': 'large'
                }

        data = form.get_useful_data()
        if raw_parl_ids := request.POST.getall('parliamentarian_id'):
            data.pop('parliamentarian_id', None)
            collection = AttendenceCollection(request.session)
            memberships = request.session.query(
                PASCommissionMembership
            ).filter(
                PASCommissionMembership.commission_id
                == form.commission_id.data
            ).all()
            commission_parliamentarians = [
                str(membership.parliamentarian_id)
                for membership in memberships
            ]
            unselected_parliamentarians = [
                pid for pid in commission_parliamentarians
                if pid not in raw_parl_ids
            ]
            for parliamentarian in unselected_parliamentarians:
                if attendence := collection.query().filter(
                        Attendence.parliamentarian_id == parliamentarian,
                        Attendence.bulk_edit_id == form.bulk_edit_id.data,
                    ).first():
                    Change.add(request, 'delete', attendence)
                    collection.delete(attendence)

            for parliamentarian_id in raw_parl_ids:
                attendence = collection.query().filter(
                        Attendence.parliamentarian_id == parliamentarian_id,
                        Attendence.bulk_edit_id == form.bulk_edit_id.data,
                    ).first()
                if attendence:
                    form.populate_obj(attendence)
                    Change.add(request, 'edit', attendence)
                else:
                    attendence = collection.add(
                        parliamentarian_id=parliamentarian_id, **data
                    )
                    Change.add(request, 'add', attendence)

        request.success(_('Edited attendences'))

        return request.redirect(request.class_link(AttendenceCollection))

    elif not request.POST:
        form.process(obj=self)

    layout = AttendenceCollectionLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Attendences'), request.class_link(AttendenceCollection)),
        Link(_('Edit session'), '#')
    ]
    layout.edit_mode = True
    layout.editmode_links[1] = BackLink(
        attrs={'class': 'cancel-link'},
    )
    layout.editmode_links.append(
        Link(
            text=_('Delete'),
            url=layout.csrf_protected_url(
                request.link(self, name='delete-attendences')),
            traits=(
                Confirm(
                    _(
                        'Do you really want to delete this bulk edit?'
                    ),
                    _('This cannot be undone.'),
                    _('Delete Attendencess'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='DELETE',
                    redirect_after=request.class_link(AttendenceCollection)
                )),
            attrs={'class': 'delete-link'},
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
    form=AttendenceAddPlenaryForm
)
def add_plenary_attendence(self: AttendenceCollection,
    request: PasRequest,
    form: AttendenceAddPlenaryForm
) -> RenderData | Response:

    if not request.is_admin:
        request.alert(_('You do not have permission to add plenary sessions.'))
        return request.redirect(request.link(self))

    if form.submitted(request):
        # Check if attendance date is in a closed settlement run
        if form.date.data:
            if check_attendance_in_closed_settlement_run(
                request.session, form.date.data
            ):
                request.alert(
                    _('Cannot create attendance in closed settlement run.')
                )
                return {
                    'layout': AttendenceCollectionLayout(self, request),
                    'title': _('New plenary session'),
                    'form': form,
                    'form_width': 'large'
                }

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
    request: PasRequest
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
    form=AttendenceForm,
    permission=Private
)
def edit_attendence(
    self: Attendence,
    request: PasRequest,
    form: AttendenceForm
) -> RenderData | Response:

    if form.submitted(request):
        # Check if attendance date is in a closed settlement run
        if form.date.data:
            if check_attendance_in_closed_settlement_run(
                request.session, form.date.data
            ):
                request.alert(
                    _('Cannot edit attendance in closed settlement run.')
                )
                return {
                    'layout': AttendenceLayout(self, request),
                    'title': AttendenceLayout(self, request).title,
                    'form': form,
                    'form_width': 'large'
                }

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
)
def delete_attendence(
    self: Attendence,
    request: PasRequest
) -> None:

    request.assert_valid_csrf_token()

    # Check if attendance is in a closed settlement run
    settlement_run = request.session.query(SettlementRun).filter(
        SettlementRun.start <= self.date,
        SettlementRun.end >= self.date,
        SettlementRun.closed == True
    ).first()

    if settlement_run:
        request.alert(
            _('Cannot delete attendance in closed settlement run.')
        )
        return

    Change.add(request, 'delete', self)
    collection = AttendenceCollection(request.session)
    collection.delete(self)


@PasApp.view(
    model=Attendence,
    name='delete-attendences',
    request_method='DELETE',
    permission=Private
)
def delete_attendences(
    self: Attendence,
    request: TownRequest
) -> None:

    request.assert_valid_csrf_token()

    attendences = request.session.query(Attendence).filter(
        Attendence.bulk_edit_id == self.bulk_edit_id
    ).all()

    # Check if any attendance is in a closed settlement run
    for attendence in attendences:
        settlement_run = request.session.query(SettlementRun).filter(
            SettlementRun.start <= attendence.date,
            SettlementRun.end >= attendence.date,
            SettlementRun.closed == True
        ).first()

        if settlement_run:
            request.alert(
                _('Cannot delete attendance in closed settlement run.')
            )
            return

    for attendence in attendences:
        Change.add(request, 'delete', attendence)
        collection = AttendenceCollection(request.session)
        collection.delete(attendence)
    request.success(_('Deleted ${count} attendeces', mapping={
            'count': len(attendences)
        }))
