from __future__ import annotations

from onegov.activity import Period, PeriodCollection
from onegov.feriennet import _
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import WhitelistedMimeType, FileSizeLimit
from sqlalchemy import desc
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
            WhitelistedMimeType({'text/plain', 'text/xml', 'application/xml'}),
            FileSizeLimit(10 * 1024 * 1024)
        ],
        render_kw={'force_simple': True}
    )

    @property
    def period_choices(self) -> list[_Choice]:
        periods = PeriodCollection(self.request.session)

        q = periods.query()
        q = q.with_entities(Period.id, Period.title)
        q = q.order_by(desc(Period.active), desc(Period.prebooking_start))

        # NOTE: Technically not quite correct, it's a Row with two named
        #       fields. But this is close enough for our purposes and is
        #       quicker than defining a matching NamedTuple.
        def choice(row: Period) -> _Choice:
            return row.id.hex, row.title

        return [choice(p) for p in q]

    def load_periods(self) -> None:
        self.period.choices = self.period_choices

        if self.period.data == '0xdeadbeef':
            self.period.data = self.period.choices[0][0]

    def on_request(self) -> None:
        self.load_periods()

    def validate_period(self, field: SelectField) -> None:
        periods = PeriodCollection(self.request.session)
        period = periods.by_id(field.data)
        assert period is not None

        if not period.finalized:
            raise ValidationError(
                'The billing of this period has not been finalized yet'
            )
