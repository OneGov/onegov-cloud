from onegov.activity import Period, PeriodCollection
from onegov.feriennet import _
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import WhitelistedMimeType, FileSizeLimit
from sqlalchemy import desc
from wtforms import SelectField, ValidationError
from wtforms.validators import InputRequired, DataRequired


class BankStatementImportForm(Form):

    period = SelectField(
        label=_("Period"),
        validators=[
            InputRequired()
        ],
        default='0xdeadbeef')

    xml = UploadField(
        label=_("ISO 20022 XML"),
        validators=[
            DataRequired(),
            WhitelistedMimeType({'text/plain', 'text/xml', 'application/xml'}),
            FileSizeLimit(10 * 1024 * 1024)
        ],
        render_kw=dict(force_simple=True)
    )

    @property
    def period_choices(self):
        periods = PeriodCollection(self.request.session)

        q = periods.query()
        q = q.with_entities(Period.id, Period.title)
        q = q.order_by(desc(Period.active), desc(Period.prebooking_start))

        def choice(row):
            return row.id.hex, row.title

        return [choice(p) for p in q]

    def load_periods(self):
        self.period.choices = self.period_choices

        if self.period.data == '0xdeadbeef':
            self.period.data = self.period.choices[0][0]

    def on_request(self):
        self.load_periods()

    def validate_period(self, field):
        periods = PeriodCollection(self.request.session)
        period = periods.by_id(field.data)

        if not period.finalized:
            raise ValidationError(
                "The billing of this period has not been finalized yet"
            )
