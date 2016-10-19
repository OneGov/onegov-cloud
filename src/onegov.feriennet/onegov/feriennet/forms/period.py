from datetime import datetime
from onegov.feriennet import _
from onegov.form import Form
from wtforms.fields import StringField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired


class PeriodForm(Form):

    title = StringField(
        label=_("Title"),
        description=_("Ferienpass Summer ${year}", mapping={
            'year': datetime.now().year
        }),
        validators=[InputRequired()]
    )

    prebooking_start = DateField(
        label=_("Prebooking Start"),
        validators=[InputRequired()]
    )

    prebooking_end = DateField(
        label=_("Prebooking End"),
        validators=[InputRequired()]
    )

    execution_start = DateField(
        label=_("Execution Start"),
        validators=[InputRequired()]
    )

    execution_end = DateField(
        label=_("Execution End"),
        validators=[InputRequired()]
    )

    @property
    def prebooking(self):
        return (self.prebooking_start.data, self.prebooking_end.data)

    @property
    def execution(self):
        return (self.execution_start.data, self.execution_end.data)

    def ensure_valid_daterange_periods(self):
        fields = (
            self.prebooking_start,
            self.prebooking_end,
            self.execution_start,
            self.execution_end
        )

        stack = [fields[0]]

        for field in fields:
            if field.data is None:
                continue

            if stack.pop().data > field.data:
                field.errors.append(_(
                    "The prebooking period must start before the exeuction "
                    "period and each period must start before it ends."
                ))
                return False

            stack.append(field)

        return True

    def validate(self):
        result = super().validate()

        ensurances = (
            self.ensure_valid_daterange_periods,
        )

        for ensurance in ensurances:
            if not ensurance():
                return False

        return result
