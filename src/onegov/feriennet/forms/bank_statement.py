from __future__ import annotations

from onegov.activity import BookingPeriod, BookingPeriodCollection
from onegov.feriennet import _
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from wtforms.fields import SelectField
from wtforms.validators import InputRequired, DataRequired, ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from wtforms.fields.choices import _Choice


class BankStatementImportForm(Form):

    period = SelectField(
        label=_('Period'),
        validators=[
            InputRequired()
        ],
        default='0xdeadbeef')

    xml = UploadField(
        label=_('ISO 20022 XML'),
        validators=[
            DataRequired(),
            FileSizeLimit(10 * 1024 * 1024)
        ],
        allowed_mimetypes={
            'text/plain',
            'text/xml',
            'application/xml'
        },
        render_kw={'force_simple': True}
    )

    @property
    def period_choices(self) -> list[_Choice]:
        periods = BookingPeriodCollection(self.request.session)

        q = periods.query()
        q = q.with_entities(BookingPeriod.id, BookingPeriod.title)
        q = q.order_by(
            BookingPeriod.active.desc(),
            BookingPeriod.prebooking_start.desc()
        )

        return [(period_id.hex, title) for period_id, title in q]

    def load_periods(self) -> None:
        self.period.choices = self.period_choices

        if self.period.data == '0xdeadbeef':
            self.period.data = self.period.choices[0][0]

    def on_request(self) -> None:
        self.load_periods()

    def validate_period(self, field: SelectField) -> None:
        periods = BookingPeriodCollection(self.request.session)
        period = periods.by_id(field.data)
        assert period is not None

        if not period.finalized:
            raise ValidationError(
                'The billing of this period has not been finalized yet'
            )
