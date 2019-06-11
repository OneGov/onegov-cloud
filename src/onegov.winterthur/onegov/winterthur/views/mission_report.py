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
from wtforms.fields import BooleanField
from wtforms.fields.html5 import IntegerField


def mission_report_form(model, request):
    if isinstance(model, MissionReportCollection):
        report = MissionReport()
    else:
        report = model

    form_class = report.with_content_extensions(MissionReportForm, request)

    class MissionReportVehicleUseForm(form_class):

        def populate_obj(self, obj):
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
                        count=self.data[f'{fid}_count']))

        def process_obj(self, obj):
            super().process_obj(obj)

            for used in obj.used_vehicles:
                field_id = f'vehicles_{used.vehicle_id.hex}'

                getattr(self, field_id).data = True
                getattr(self, f'{field_id}_count').data = used.count

    builder = WTFormsClassBuilder(MissionReportVehicleUseForm)
    builder.set_current_fieldset(_("Vehicles"))

    vehicles = MissionReportVehicleCollection(request.session).query()
    vehicles = {v.id: v for v in vehicles if not v.is_hidden_from_public}

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
            field_class=IntegerField,
            field_id=vehicle_field_id,
            label=request.translate(_("Count")),
            required=True,
            dependency=FieldDependency(field_id, 'y'),
            default=1
        )

    form_class = builder.form_class

    if vehicle_field_id:
        form_class = move_fields(
            form_class, ('is_hidden_from_public', ), vehicle_field_id)

    return form_class


def mission_report_vehicle_form(model, request):
    if isinstance(model, MissionReportVehicleCollection):
        report = MissionReportVehicle()
    else:
        report = model

    return report.with_content_extensions(MissionReportVehicleForm, request)


@WinterthurApp.html(
    model=MissionReportCollection,
    permission=Public,
    template='mission_reports.pt')
def view_mission_reports(self, request):
    return {
        'layout': MissionReportLayout(self, request),
        'title': _("Mission Reports"),
        'reports': self.batch,
        'count': self.mission_count(),
        'year': self.year,
    }


@WinterthurApp.html(
    model=MissionReport,
    permission=Public,
    template='mission_report.pt')
def view_mission(self, request):
    return {
        'title': self.title,
        'layout': MissionReportLayout(
            self, request,
            Link(self.title, '#')
        ),
        'model': self
    }


@WinterthurApp.html(
    model=MissionReportVehicleCollection,
    permission=Private,
    template='mission_report_vehicles.pt')
def view_mission_report_vehicles(self, request):

    return {
        'layout': MissionReportLayout(
            self, request,
            Link(_("Vehicles"), request.link(self))
        ),
        'title': _("Vehicles"),
        'vehicles': tuple(self.query()),
    }


@WinterthurApp.html(model=MissionReportFileCollection, template='images.pt',
                    permission=Private)
def view_mission_report_files(self, request):
    data = view_get_image_collection(self, request)
    data['layout'] = MissionReportLayout(
        self, request,
        Link(self.report.title, request.link(self.report)),
        Link(_("Images"), '#', editbar=False)
    )

    return data


@WinterthurApp.form(
    model=MissionReportCollection,
    permission=Private,
    form=mission_report_form,
    name='new',
    template='form.pt')
def handle_new_mission_report(self, request, form):

    if form.submitted(request):
        mission = self.add(**{
            k: v for k, v in form.data.items()
            if k != 'csrf_token'
            and not k.startswith('vehicles_')
        })

        form.populate_obj(mission)

        request.success(_("Successfully added a mission report"))
        return request.redirect(request.link(mission))

    return {
        'title': _("Mission Reports"),
        'form': form,
        'layout': MissionReportLayout(
            self, request,
            Link(_("New"), '#', editbar=False)
        ),
    }


@WinterthurApp.form(
    model=MissionReport,
    permission=Private,
    form=mission_report_form,
    name='edit',
    template='form.pt')
def handle_edit_mission_report(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    elif not request.POST:
        form.process(obj=self)

    return {
        'title': _("Mission Reports"),
        'form': form,
        'layout': MissionReportLayout(
            self, request,
            Link(self.title, request.link(self)),
            Link(_("Edit"), '#', editbar=False),
        )
    }


@WinterthurApp.view(
    model=MissionReport,
    permission=Private,
    request_method='DELETE')
def delete_mission_report(self, request):
    request.assert_valid_csrf_token()
    request.session.delete(self)
    request.success(_("Successfully deleted mission report"))


@WinterthurApp.form(
    model=MissionReportVehicleCollection,
    permission=Private,
    form=mission_report_vehicle_form,
    name='new',
    template='form.pt')
def handle_new_vehicle(self, request, form):

    if form.submitted(request):
        vehicle = self.add(
            **{k: v for k, v in form.data.items() if k not in (
                'csrf_token', 'symbol'
            )})

        # required for the symbol image
        form.populate_obj(vehicle)

        request.success(_("Successfully added a vehicle"))

        return request.redirect(
            request.class_link(MissionReportVehicleCollection))

    return {
        'title': _("Vehicle"),
        'form': form,
        'layout': MissionReportLayout(
            self, request,
            Link(_("Vehicles"), request.link(self)),
            Link(_("New"), '#', editbar=False)
        ),
    }


@WinterthurApp.form(
    model=MissionReportVehicle,
    permission=Private,
    form=mission_report_vehicle_form,
    name='edit',
    template='form.pt')
def handle_edit_vehicle(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))

        return request.redirect(
            request.class_link(MissionReportVehicleCollection))

    elif not request.POST:
        form.process(obj=self)

    return {
        'title': self.title,
        'form': form,
        'layout': MissionReportLayout(
            self, request,
            Link(_("Vehicles"), request.class_link(
                MissionReportVehicleCollection)),
            Link(self.title, '#')
        )
    }


@WinterthurApp.view(
    model=MissionReportVehicle,
    permission=Private,
    request_method='DELETE')
def delete_mission_report_vehicle(self, request):
    request.assert_valid_csrf_token()
    request.session.delete(self)
    request.success(_("Successfully deleted vehicle"))
