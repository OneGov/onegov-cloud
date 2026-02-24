from __future__ import annotations

import csv

from datetime import date
from io import StringIO
from onegov.core.elements import Link
from onegov.core.security import Public, Private
from onegov.form import FieldDependency, WTFormsClassBuilder, move_fields
from onegov.org.views.files import view_get_image_collection
from onegov.winterthur import WinterthurApp, _
from onegov.winterthur.collections import MissionReportCollection
from onegov.winterthur.collections import MissionReportFileCollection
from onegov.winterthur.collections import MissionReportVehicleCollection
from onegov.winterthur.forms import MissionReportForm
from onegov.winterthur.forms import MissionReportVehicleForm
from onegov.winterthur.layout import MissionReportLayout
from onegov.winterthur.models import MissionReport
from onegov.winterthur.models import MissionReportVehicle
from onegov.winterthur.models import MissionReportVehicleUse
from uuid import UUID
from webob import Response
from wtforms.fields import BooleanField
from wtforms.fields import IntegerField
from wtforms.validators import NumberRange


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webob import Response

    from onegov.core.types import JSON_ro, RenderData
    from onegov.winterthur.request import WinterthurRequest


def mission_report_form(
    model: MissionReport | MissionReportCollection,
    request: WinterthurRequest
) -> type[MissionReportForm]:
    if isinstance(model, MissionReportCollection):
        report = MissionReport()
    else:
        report = model

    form_class = report.with_content_extensions(MissionReportForm, request)

    class MissionReportVehicleUseForm(form_class):  # type:ignore

        def populate_obj(self, obj: MissionReport) -> None:
            super().populate_obj(obj)

            for used in obj.used_vehicles:
                request.session.delete(used)

            request.session.flush()

            fids = (
                fid for fid in self._fields

                if fid.startswith('vehicles_')
                and not fid.endswith('_count')
                and self.data[fid]
            )

            for fid in fids:

                obj.used_vehicles.append(
                    MissionReportVehicleUse(
                        vehicle_id=UUID(fid.replace('vehicles_', '')),
                        count=self[f'{fid}_count'].data
                    )
                )

        def process_obj(self, obj: MissionReport) -> None:
            super().process_obj(obj)

            for used in obj.used_vehicles:
                field_id = f'vehicles_{used.vehicle_id.hex}'

                self[field_id].data = True
                self[f'{field_id}_count'].data = used.count

    builder = WTFormsClassBuilder(MissionReportVehicleUseForm)
    builder.set_current_fieldset(_('Vehicles'))

    vehicles_q = MissionReportVehicleCollection(request.session).query()
    vehicles = {v.id: v for v in vehicles_q if v.access == 'public'}

    # include hidden vehicles that were picked before being hidden
    for used in report.used_vehicles:
        if used.vehicle_id not in vehicles:
            vehicles[used.vehicle_id] = used.vehicle

    vehicle_field_id = None

    for vehicle in sorted(vehicles.values(), key=lambda v: v.name):
        field_id = f'vehicles_{vehicle.id.hex}'
        vehicle_field_id = f'{field_id}_count'

        builder.add_field(
            field_class=BooleanField,
            field_id=field_id,
            label=vehicle.title,
            required=False,
            id=vehicle.id
        )

        builder.add_field(
            validators=[NumberRange(0, 10000)],
            field_class=IntegerField,
            field_id=vehicle_field_id,
            label=request.translate(_('Count')),
            required=True,
            dependency=FieldDependency(field_id, 'y'),
            default=1
        )

    form_class = builder.form_class

    if vehicle_field_id:
        form_class = move_fields(
            form_class, ('access', ), vehicle_field_id)

    return form_class


def mission_report_vehicle_form(
    model: MissionReportVehicle | MissionReportVehicleCollection,
    request: WinterthurRequest
) -> type[MissionReportVehicleForm]:

    if isinstance(model, MissionReportVehicleCollection):
        report = MissionReportVehicle()
    else:
        report = model

    return report.with_content_extensions(MissionReportVehicleForm, request)


@WinterthurApp.html(
    model=MissionReportCollection,
    permission=Public,
    template='mission_reports.pt'
)
def view_mission_reports(
    self: MissionReportCollection,
    request: WinterthurRequest
) -> RenderData:
    return {
        'layout': MissionReportLayout(self, request),
        'title': _('Mission Reports'),
        'reports': self.batch,
        'count': self.mission_count(),
        'year': self.year,
    }


@WinterthurApp.html(
    model=MissionReport,
    permission=Public,
    template='mission_report.pt'
)
def view_mission(
    self: MissionReport,
    request: WinterthurRequest
) -> RenderData:
    return {
        'title': self.title,
        'layout': MissionReportLayout(
            self, request,
            Link(self.title, '#')
        ),
        'model': self
    }


@WinterthurApp.json(
    model=MissionReportCollection,
    name='json',
    permission=Public
)
def view_mission_reports_as_json(
    self: MissionReportCollection,
    request: WinterthurRequest
) -> JSON_ro:

    query = self.query()
    if request.params.get('all', False):
        query = self.query_all()
    elif request.params.get('year'):
        year_param = str(request.params['year'])
        if year_param.isdigit():
            self.year = int(year_param)
            query = self.filter_by_year(self.query())

    return {
        'name': 'Mission Reports',
        'report_count': query.count(),
        'reports': [
            {
                'date': mission.local_date.strftime('%d-%m-%Y'),
                'alarm': mission.local_date.strftime('%H:%M'),
                'duration': mission.readable_duration,
                'nature': mission.nature,
                'mission_type': mission.mission_type,
                'mission_count': mission.mission_count,
                'vehicles': [
                    use.vehicle.name for use in mission.used_vehicles
                    for _ in range(use.count)
                ],
                'vehicles_icons': [
                    request.link(use.vehicle.symbol)
                    if use.vehicle.symbol else ''
                    for use in mission.used_vehicles
                    for _ in range(use.count)
                ],
                'location': mission.location,
                'personnel_active': mission.personnel,
                'personnel_backup': mission.backup,
                'civil_defence_involved': mission.civil_defence,
            } for mission in query
        ]
    }


@WinterthurApp.view(
    model=MissionReportCollection,
    name='csv',
    permission=Public
)
def view_mission_reports_as_csv(
    self: MissionReportCollection,
    request: WinterthurRequest
) -> Response:

    query = self.query()
    if request.params.get('all', False):
        query = self.query_all()
    elif request.params.get('year'):
        year_param = str(request.params['year'])
        if year_param.isdigit():
            self.year = int(year_param)
            query = self.filter_by_year(self.query())

    output = StringIO()
    writer = csv.writer(output)

    # Write CSV header
    writer.writerow([
        'date', 'alarm', 'duration', 'nature', 'mission_type', 'mission_count',
        'vehicles', 'vehicles_icons', 'location', 'personnel_active',
        'personnel_backup', 'civil_defence_involved'
    ])

    # Write CSV rows
    for mission in query:
        writer.writerow([
            mission.local_date.strftime('%d-%m-%Y'),
            mission.local_date.strftime('%H:%M'),
            mission.readable_duration,
            mission.nature,
            mission.mission_type,
            mission.mission_count,
            ', '.join([
                use.vehicle.name for use in mission.used_vehicles for _ in
                range(use.count)
            ]),
            ', '.join([
                request.link(use.vehicle.symbol)
                if use.vehicle.symbol else ''
                for use in mission.used_vehicles for _ in range(use.count)
            ]),
            mission.location,
            mission.personnel,
            mission.backup,
            mission.civil_defence
        ])

    response = Response(content_type='text/csv')
    response.text = output.getvalue()
    response.content_disposition = 'attachment; filename="mission_reports.csv"'
    return response


@WinterthurApp.html(
    model=MissionReportVehicleCollection,
    permission=Private,
    template='mission_report_vehicles.pt'
)
def view_mission_report_vehicles(
    self: MissionReportVehicleCollection,
    request: WinterthurRequest
) -> RenderData:

    return {
        'layout': MissionReportLayout(
            self, request,
            Link(_('Vehicles'), request.link(self))
        ),
        'title': _('Vehicles'),
        'vehicles': tuple(self.query()),
    }


@WinterthurApp.html(
    model=MissionReportFileCollection,
    template='images.pt',
    permission=Private
)
def view_mission_report_files(
    self: MissionReportFileCollection,
    request: WinterthurRequest
) -> RenderData:

    data = view_get_image_collection(self, request)
    data['layout'] = MissionReportLayout(
        self, request,
        Link(self.report.title, request.link(self.report)),
        Link(_('Images'), '#', editbar=False)
    )

    return data


@WinterthurApp.form(
    model=MissionReportCollection,
    permission=Private,
    form=mission_report_form,
    name='new',
    template='form.pt'
)
def handle_new_mission_report(
    self: MissionReportCollection,
    request: WinterthurRequest,
    form: MissionReportForm
) -> RenderData | Response:

    if form.submitted(request):
        mission = self.add(date=form.date, **{
            k: v for k, v in form.data.items()
            if k not in ('csrf_token', 'day', 'time')
            and not k.startswith('vehicles_')
        })

        form.populate_obj(mission)

        if mission.date.year != date.today().year:
            request.warning(
                _(
                    'The report was entered in the current year, '
                    'please verify the date'
                ))
        else:
            request.success(_('Successfully added a mission report'))

        return request.redirect(request.link(mission))

    return {
        'title': _('Mission Reports'),
        'form': form,
        'layout': MissionReportLayout(
            self, request,
            Link(_('New'), '#', editbar=False)
        ),
    }


@WinterthurApp.form(
    model=MissionReport,
    permission=Private,
    form=mission_report_form,
    name='edit',
    template='form.pt'
)
def handle_edit_mission_report(
    self: MissionReport,
    request: WinterthurRequest,
    form: MissionReportForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        self.date = form.date

        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    elif not request.POST:
        form.process(obj=self)
        form.date = self.date

    return {
        'title': _('Mission Reports'),
        'form': form,
        'layout': MissionReportLayout(
            self, request,
            Link(self.title, request.link(self)),
            Link(_('Edit'), '#', editbar=False),
        )
    }


@WinterthurApp.view(
    model=MissionReport,
    permission=Private,
    request_method='DELETE'
)
def delete_mission_report(
    self: MissionReport,
    request: WinterthurRequest
) -> None:

    request.assert_valid_csrf_token()
    request.session.delete(self)
    request.success(_('Successfully deleted mission report'))


@WinterthurApp.form(
    model=MissionReportVehicleCollection,
    permission=Private,
    form=mission_report_vehicle_form,
    name='new',
    template='form.pt'
)
def handle_new_vehicle(
    self: MissionReportVehicleCollection,
    request: WinterthurRequest,
    form: MissionReportVehicleForm
) -> RenderData | Response:

    if form.submitted(request):
        vehicle = self.add(
            **{k: v for k, v in form.data.items() if k not in (
                'csrf_token', 'symbol'
            )})

        # required for the symbol image
        form.populate_obj(vehicle)

        request.success(_('Successfully added a vehicle'))

        return request.redirect(
            request.class_link(MissionReportVehicleCollection))

    return {
        'title': _('Vehicle'),
        'form': form,
        'layout': MissionReportLayout(
            self, request,
            Link(_('Vehicles'), request.link(self)),
            Link(_('New'), '#', editbar=False)
        ),
    }


@WinterthurApp.form(
    model=MissionReportVehicle,
    permission=Private,
    form=mission_report_vehicle_form,
    name='edit',
    template='form.pt'
)
def handle_edit_vehicle(
    self: MissionReportVehicle,
    request: WinterthurRequest,
    form: MissionReportVehicleForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_('Your changes were saved'))

        return request.redirect(
            request.class_link(MissionReportVehicleCollection))

    elif not request.POST:
        form.process(obj=self)

    return {
        'title': self.title,
        'form': form,
        'layout': MissionReportLayout(
            self, request,
            Link(_('Vehicles'), request.class_link(
                MissionReportVehicleCollection)),
            Link(self.title, '#')
        )
    }


@WinterthurApp.view(
    model=MissionReportVehicle,
    permission=Private,
    request_method='DELETE'
)
def delete_mission_report_vehicle(
    self: MissionReportVehicle,
    request: WinterthurRequest
) -> None:

    request.assert_valid_csrf_token()
    request.session.delete(self)
    request.success(_('Successfully deleted vehicle'))
