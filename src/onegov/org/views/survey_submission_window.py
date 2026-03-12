from __future__ import annotations

import morepath

from onegov.core.security import Private
from onegov.core.security.permissions import Public
from onegov.core.utils import append_query_param
from onegov.form.collection import SurveyCollection
from onegov.form.models.definition import SurveyDefinition
from onegov.form.models.submission import SurveySubmission
from onegov.form.models.survey_window import SurveySubmissionWindow
from onegov.gis.models.coordinates import Coordinates
from onegov.org import OrgApp, _
from onegov.org.forms.survey_submission import SurveySubmissionWindowForm
from onegov.org.layout import (SurveySubmissionLayout,
                               SurveySubmissionWindowLayout)
from onegov.core.elements import Link


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form import Form
    from collections.abc import Iterator
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from webob import Response
    from onegov.core.layout import Layout


def get_hints(
    layout: Layout,
    window: SurveySubmissionWindow | None
) -> Iterator[tuple[str, str]]:

    if not window:
        return

    if window.in_the_past:
        yield 'stop', _('The survey timeframe has ended')

    if window.in_the_future:
        yield 'date', _(
            'The survey timeframe opens on ${day}, ${date}', mapping={
                'day': layout.format_date(window.start, 'weekday_long'),
                'date': layout.format_date(window.start, 'date_long')
            })

    if window.in_the_present:
        yield 'date', _(
            'The survey timeframe closes on ${day}, ${date}', mapping={
                'day': layout.format_date(window.end, 'weekday_long'),
                'date': layout.format_date(window.end, 'date_long')
            })


@OrgApp.form(
    model=SurveyDefinition,
    name='new-submission-window',
    permission=Private,
    form=SurveySubmissionWindowForm,
    template='form.pt'
)
def handle_new_submission_form(
    self: SurveyDefinition,
    request: OrgRequest,
    form: SurveySubmissionWindowForm,
    layout: SurveySubmissionLayout | None = None
) -> RenderData | Response:
    title = _('New Submission Window')

    layout = layout or SurveySubmissionLayout(self, request)
    layout.edit_mode = True
    layout.breadcrumbs.append(Link(title, '#'))

    if form.submitted(request):
        assert form.start.data is not None
        assert form.end.data is not None
        form.populate_obj(self.add_submission_window(
            form.start.data,
            form.end.data
        ))

        request.success(_('The registration window was added successfully'))
        return request.redirect(request.link(self))

    return {
        'layout': layout,
        'title': title,
        'form': form,
        'helptext': _(
            'Submissions windows limit survey submissions to a specific '
            'time-range.'
        )
    }


@OrgApp.html(
    model=SurveySubmissionWindow,
    permission=Private,
    template='submission_window.pt',
    name='results'
)
def view_submission_window_results(
    self: SurveySubmissionWindow,
    request: OrgRequest,
    layout: SurveySubmissionLayout | None = None
) -> RenderData:

    layout = layout or SurveySubmissionLayout(self.survey, request)
    window_name = self.title if self.title else layout.format_date_range(
        self.start, self.end)
    date_range = layout.format_date_range(self.start, self.end)
    layout.breadcrumbs.append(Link(window_name, request.link(self)))
    layout.breadcrumbs.append(Link(_('Results'), '#'))

    layout.editbar_links = [
        Link(
            text=_('Export'),
            url=append_query_param(
                request.link(self.survey, name='export'),
                'submission_window_id', self.id.hex),
            attrs={'class': 'export-link'}
        )]

    q = request.session.query(SurveySubmission)
    submissions = q.filter_by(submission_window_id=self.id).all()

    results = self.survey.get_results(request, self.id)
    aggregated = ['MultiCheckboxField', 'CheckboxField', 'RadioField']

    form = request.get_form(self.survey.form_class)
    all_fields = form._fields
    all_fields.pop('csrf_token', None)
    fields = all_fields.values()

    return {
        'layout': layout,
        'title': _('Results'),
        'window_name': window_name,
        'date_range': date_range,
        'model': self,
        'results': results,
        'fields': fields,
        'aggregated': aggregated,
        'submission_count': len(submissions)
    }


@OrgApp.form(
    model=SurveySubmissionWindow,
    permission=Public,
    template='form.pt',
    form=lambda self, request: self.survey.form_class
)
def view_submission_window_survey(
    self: SurveySubmissionWindow,
    request: OrgRequest,
    form: Form,
    layout: SurveySubmissionWindowLayout | None = None
) -> RenderData | Response:

    collection = SurveyCollection(request.session)
    definition = self.survey

    enabled = self.accepts_submissions()
    layout = layout or SurveySubmissionWindowLayout(self, request)

    window_title = self.title if self.title else layout.format_date_range(
        self.start, self.end)
    date_range = layout.format_date_range(self.start, self.end)
    subtitle = window_title if window_title else date_range

    if enabled and request.POST:
        submission = collection.submissions.add(
            self.name, form,
            submission_window=self)

        return morepath.redirect(request.link(submission))

    return {
        'layout': layout,
        'title': definition.title,
        'subtitle': subtitle,
        'date_range': date_range,
        'form': enabled and form,
        'definition': definition,
        'form_width': 'small',
        'lead': layout.linkify(definition.meta.get('lead')),
        'text': definition.content.get('text'),
        'people': getattr(definition, 'people', None),
        'files': getattr(definition, 'files', None),
        'contact': getattr(definition, 'contact_html', None),
        'coordinates': getattr(definition, 'coordinates', Coordinates()),
        'hints': tuple(get_hints(layout, self)),
        'hints_callout': not enabled,
    }


@OrgApp.form(
    model=SurveySubmissionWindow,
    permission=Private,
    form=SurveySubmissionWindowForm,
    template='form.pt',
    name='edit'
)
def handle_edit_submission_window(
    self: SurveySubmissionWindow,
    request: OrgRequest,
    form: SurveySubmissionWindowForm,
    layout: SurveySubmissionLayout | None = None
) -> RenderData | Response:

    title = _('Edit Submission Window')

    layout = layout or SurveySubmissionLayout(self.survey, request)
    layout.breadcrumbs.append(Link(title, '#'))
    layout.edit_mode = True

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self.survey))

    elif not request.POST:
        form.process(obj=self)

    return {
        'layout': layout,
        'title': title,
        'form': form
    }


@OrgApp.view(
    model=SurveySubmissionWindow,
    permission=Private,
    request_method='DELETE'
)
def delete_submission_window(
    self: SurveySubmissionWindow,
    request: OrgRequest
) -> None:

    request.assert_valid_csrf_token()

    submissions = request.session.query(SurveySubmission)
    submissions = submissions.filter(
        SurveySubmission.submission_window_id == self.id)
    submissions.delete()
    request.session.delete(self)

    request.success(_('The submission window and all associated submissions '
                        'were deleted'))
