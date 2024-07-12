from datetime import date
from onegov.form import Form
from onegov.org.forms.fields import HtmlField
from onegov.pas import _
from onegov.pas.layouts import DefaultLayout
from onegov.pas.models import SettlementRun
from wtforms.fields import DateField
from wtforms.fields import StringField
from wtforms.validators import InputRequired


class SettlementRunForm(Form):

    name = StringField(
        label=_('Name'),
        validators=[InputRequired()],
    )

    start = DateField(
        label=_('Start'),
        validators=[InputRequired()],
        default=date.today
    )

    end = DateField(
        label=_('End'),
        validators=[InputRequired()],
        default=date.today
    )

    description = HtmlField(
        label=_('Description'),
    )

    def ensure_valid_dates(self) -> bool:
        start = self.start.data
        end = self.end.data
        if start and end:
            # Check valid range
            if end <= start:
                assert isinstance(self.end.errors, list)
                self.end.errors.append(_('End must be after start'))
                return False

            # Check overlapping runs
            query = self.request.session.query(SettlementRun)
            if isinstance(self.model, SettlementRun):
                query = query.filter(SettlementRun.id != self.model.id)
            for run in query:
                if max(start, run.start) <= min(end, run.end):
                    layout = DefaultLayout(
                        self.model,
                        self.request  # type:ignore[arg-type]
                    )
                    message = _(
                        'Dates overlap with existing settlement run: '
                        '${start} - ${end}',
                        mapping={
                            'start': layout.format_date(run.start, 'date'),
                            'end': layout.format_date(run.end, 'date')
                        }
                    )
                    assert isinstance(self.start.errors, list)
                    assert isinstance(self.end.errors, list)
                    self.start.errors.append(message)
                    self.end.errors.append(message)
                    return False

        return True
