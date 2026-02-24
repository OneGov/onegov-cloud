from __future__ import annotations

from wtforms import StringField
from onegov.form import Form
from onegov.org import _
from wtforms.fields import DateField
from wtforms.validators import InputRequired


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form import SurveySubmissionWindow, SurveyDefinition
    from onegov.org.request import OrgRequest


class SurveySubmissionWindowForm(Form):
    """ Form to edit submission windows. """

    if TYPE_CHECKING:
        model: SurveyDefinition | SurveySubmissionWindow
        request: OrgRequest

    title = StringField(
        label=_('Name'),
        validators=[]
    )

    start = DateField(
        label=_('Start'),
        validators=[InputRequired()]
    )

    end = DateField(
        label=_('End'),
        validators=[InputRequired()]
    )

    def process_obj(
        self,
        obj: SurveySubmissionWindow  # type:ignore[override]
    ) -> None:

        super().process_obj(obj)

    def populate_obj(  # type:ignore[override]
        self,
        obj: SurveySubmissionWindow,  # type:ignore[override]
        *args: Any,
        **kwargs: Any,
    ) -> None:

        super().populate_obj(obj, *args, **kwargs)

    def ensure_start_before_end(self) -> bool | None:
        """ Validate start and end for proper error message.
        def ensure_start_end(self) would also be run in side the validate
        function, but the error is not clear. """

        if not self.start.data or not self.end.data:
            return None
        if self.start.data >= self.end.data:
            assert isinstance(self.end.errors, list)
            self.end.errors.append(_('Please use a stop date after the start'))
            return False
        return None

    def ensure_unique_title(self) -> bool | None:
        """ Ensure that the title is unique within the survey. """

        if not self.title.data:
            return None

        survey: SurveyDefinition
        survey = getattr(self.model, 'survey', self.model)  # type:ignore

        for existing in survey.submission_windows:
            if existing == self.model:
                continue
            if existing.title == self.title.data:
                assert isinstance(self.title.errors, list)
                self.title.errors.append(
                    _('A submission window with this title already exists.')
                )
                return False
        return None

    def ensure_no_overlapping_windows(self) -> bool | None:
        """ Ensure that this registration window does not overlap with other
        already defined registration windows unless they have a title.

        """
        if not self.start.data or not self.end.data:
            return None

        # FIXME: An isinstance check would be nicer but we would need to
        #        stop using Bunch in the tests
        survey: SurveyDefinition
        survey = getattr(self.model, 'survey', self.model)  # type:ignore

        if self.title.data:
            return None

        for existing in survey.submission_windows:
            if existing == self.model:
                continue

            latest_start = max(self.start.data, existing.start)
            earliest_end = min(self.end.data, existing.end)
            delta = (earliest_end - latest_start).days + 1
            if delta > 0:
                # circular
                from onegov.org.layout import DefaultLayout
                layout = DefaultLayout(self.model, self.request)

                msg = _(
                    'The date range overlaps with an existing submission '
                    'window (${range}). Either choose a different date range '
                    'or give this window a title to differenciate it from '
                    'other windows.',
                    mapping={
                        'range': layout.format_date_range(
                            existing.start, existing.end
                        )
                    }
                )
                assert isinstance(self.start.errors, list)
                self.start.errors.append(msg)
                assert isinstance(self.end.errors, list)
                self.end.errors.append(msg)
                return False
        return None
