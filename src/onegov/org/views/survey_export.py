from __future__ import annotations

from collections import OrderedDict
from onegov.core.security import Private
from onegov.form.collection import SurveySubmissionCollection
from onegov.form.models.definition import SurveyDefinition
from onegov.form.models.submission import SurveySubmission
from onegov.form.models.survey_window import SurveySubmissionWindow
from onegov.org import _
from onegov.org import OrgApp
from onegov.org.forms.survey_export import SurveySubmissionsExport
from onegov.org.layout import SurveySubmissionLayout
from onegov.core.elements import Link
from onegov.org.utils import keywords_first


from typing import Any, NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Sequence
    from datetime import date
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from sqlalchemy.orm import Query
    from uuid import UUID
    from webob import Response

    class SurveySubmissionRow(NamedTuple):
        data: dict[str, Any]
        submission_window_start: date
        submission_window_end: date


@OrgApp.form(
    model=SurveyDefinition,
    name='export',
    permission=Private,
    form=SurveySubmissionsExport,
    template='export.pt'
)
def handle_form_submissions_export(
    self: SurveyDefinition,
    request: OrgRequest,
    form: SurveySubmissionsExport,
    layout: SurveySubmissionLayout | None = None
) -> RenderData | Response:

    layout = layout or SurveySubmissionLayout(self, request)
    layout.breadcrumbs.append(Link(_('Export'), '#'))
    layout.editbar_links = None

    if form.submitted(request):
        submissions = SurveySubmissionCollection(
            request.session, name=self.name)

        if form.data['submission_window']:
            query = subset_by_window(
                submissions=submissions,
                window_ids=form.data['submission_window'])
        else:
            query = submissions.query()

        subset = configure_subset(query)

        field_order, results = run_export(
            subset=subset,
            nested=form.format == 'json',
            formatter=layout.export_formatter(form.format))

        return form.as_export_response(results, self.title, key=field_order)

    return {
        'title': _('Export'),
        'layout': layout,
        'form': form,
        'explanation': _('Exports the submissions of the survey.')
    }


def subset_by_window(
    submissions: SurveySubmissionCollection,
    window_ids: Collection[UUID]
) -> Query[SurveySubmission]:
    return (
        submissions.query()
        .filter(SurveySubmission.submission_window_id.in_(window_ids))
    )


def configure_subset(
    subset: Query[SurveySubmission],
) -> Query[SurveySubmissionRow]:

    subset = subset.join(
        SurveySubmissionWindow,
        SurveySubmission.submission_window_id == SurveySubmissionWindow.id,
        isouter=True
    )

    return subset.with_entities(
        SurveySubmission.data,
        SurveySubmissionWindow.start.label('submission_window_start'),
        SurveySubmissionWindow.end.label('submission_window_end'),
    )


def run_export(
    subset: Query[SurveySubmissionRow],
    nested: bool,
    formatter: Callable[[object], Any]
) -> tuple[Callable[[str], tuple[int, str]], Sequence[dict[str, Any]]]:

    keywords = (
        'submission_window_start',
        'submission_window_end'
    )

    def transform(submission: SurveySubmissionRow) -> dict[str, Any]:
        r = OrderedDict()

        for keyword in keywords:
            r[keyword] = formatter(getattr(submission, keyword))

        if nested:
            r['survey'] = {
                k: formatter(v)
                for k, v in submission.data.items()
            }
        else:
            for k, v in submission.data.items():
                r[f'{k}'] = formatter(v)

        return r

    return keywords_first(keywords), tuple(transform(s) for s in subset)
