from datetime import date
from onegov.core.orm.func import unaccent
from onegov.form import Form
from onegov.wtfs import _
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import ReportBoxes
from onegov.wtfs.models import ReportBoxesAndForms
from onegov.wtfs.models import ReportBoxesAndFormsByDelivery
from onegov.wtfs.models import ReportFormsAllMunicipalities
from onegov.wtfs.models import ReportFormsByMunicipality
from wtforms.fields import DateField
from wtforms.fields import RadioField
from wtforms.fields import SelectField
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
            ('all_forms', _("Report forms of all municipalities")),
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
            'report_type', '!boxes_and_forms',
            'report_type', '!all_forms'
        ),
    )

    def ensure_start_end_in_same_year(self) -> bool:
        if self.report_type.data == 'boxes':
            return True

        if self.start.data and self.end.data:
            if self.start.data.year != self.end.data.year:
                assert isinstance(self.end.errors, list)
                self.end.errors.append(
                    _('Start and end must be in the same year')
                )
                return False
        return True

    def on_request(self) -> None:
        query = self.request.session.query(
            Municipality.id.label('id'),
            Municipality.name.label('name'),
            Municipality.meta['bfs_number'].label('bfs_number')
        )
        query = query.order_by(unaccent(Municipality.name))
        self.municipality_id.choices = [
            (r.id.hex, f"{r.name} ({r.bfs_number})") for r in query
        ]

    def get_model(self) -> (
        ReportBoxes
        | ReportBoxesAndForms
        | ReportFormsByMunicipality
        | ReportFormsAllMunicipalities
        | ReportBoxesAndFormsByDelivery
        | None
    ):
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
        if self.report_type.data == 'all_forms':
            return ReportFormsAllMunicipalities(
                self.request.session,
                start=self.start.data,
                end=self.end.data,
                type=self.scan_job_type.data,
            )
        if self.report_type.data == 'delivery':
            assert self.start.data is not None
            assert self.end.data is not None
            return ReportBoxesAndFormsByDelivery(
                self.request.session,
                start=self.start.data,
                end=self.end.data,
                type=self.scan_job_type.data,
                municipality_id=self.municipality_id.data
            )
        return None
