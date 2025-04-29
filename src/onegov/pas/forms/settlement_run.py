from __future__ import annotations

from datetime import date
from onegov.form import Form
from onegov.org.forms.fields import HtmlField
from onegov.pas import _
from onegov.pas.layouts import DefaultLayout
from onegov.pas.models import SettlementRun
from wtforms.fields import BooleanField
from onegov.pas.custom import get_current_settlement_run
from wtforms.fields import DateField
from wtforms.fields import StringField
from wtforms.validators import InputRequired, ValidationError


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

    active = BooleanField(
        label=_('Active'),
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

    def validate_active(self, field: BooleanField) -> None:
        if not field.data:
            return

        session = self.request.session
        active_run = get_current_settlement_run(session)

        if active_run:
            # If we are editing the currently active run, it's okay
            if isinstance(self.model, SettlementRun) \
                    and self.model.id == active_run.id:
                return

            raise ValidationError(
                _('An active settlement run already exists.')
            )
