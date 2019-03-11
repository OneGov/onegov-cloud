from datetime import date
from onegov.core.orm.func import unaccent
from onegov.form import Form
from onegov.wtfs import _
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import ReportBoxes
from onegov.wtfs.models import ReportBoxesAndForms
from onegov.wtfs.models import ReportBoxesAndFormsByDelivery
from onegov.wtfs.models import ReportFormsByMunicipality
from wtforms import RadioField
from wtforms import SelectField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired


class ReportSelectionForm(Form):

    start = DateField(
        label=_("Start date"),
        validators=[InputRequired()],
        default=date.today
    )

    end = DateField(
        label=_("End date"),
        validators=[InputRequired()],
        default=date.today
    )

    report_type = RadioField(
        label=_("Report"),
        choices=[
            ('boxes', _("Report boxes")),
            ('boxes_and_forms', _("Report boxes and forms")),
            ('forms', _("Report forms")),
            ('delivery', _("Report boxes and forms by delivery")),
        ],
        validators=[InputRequired()],
        default='boxes'
    )

    scan_job_type = RadioField(
        label=_("Type"),
        choices=[
            ('normal', _("Regular shipment")),
            ('express', _("Express shipment")),
            ('all', _("Regular and express shipment"))
        ],
        depends_on=('report_type', '!boxes'),
        validators=[InputRequired()],
        default='all'
    )

    municipality_id = SelectField(
        label=_("Municipality"),
        choices=[],
        validators=[InputRequired()],
        depends_on=(
            'report_type', '!boxes',
            'report_type', '!boxes_and_forms'
        ),
    )

    def on_request(self):
        query = self.request.session.query(
            Municipality.id.label('id'),
            Municipality.name.label('name'),
            Municipality.meta['bfs_number'].label('bfs_number')
        )
        query = query.order_by(unaccent(Municipality.name))
        self.municipality_id.choices = [
            (r.id.hex, f"{r.name} ({r.bfs_number})") for r in query
        ]

    def get_model(self):
        if self.report_type.data == 'boxes':
            return ReportBoxes(
                self.request.session,
                start=self.start.data,
                end=self.end.data
            )
        if self.report_type.data == 'boxes_and_forms':
            return ReportBoxesAndForms(
                self.request.session,
                start=self.start.data,
                end=self.end.data,
                type=self.scan_job_type.data
            )
        if self.report_type.data == 'forms':
            return ReportFormsByMunicipality(
                self.request.session,
                start=self.start.data,
                end=self.end.data,
                type=self.scan_job_type.data,
                municipality_id=self.municipality_id.data
            )
        if self.report_type.data == 'delivery':
            return ReportBoxesAndFormsByDelivery(
                self.request.session,
                start=self.start.data,
                end=self.end.data,
                type=self.scan_job_type.data,
                municipality_id=self.municipality_id.data
            )
