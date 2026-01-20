from __future__ import annotations

from collections import OrderedDict
from onegov.core.orm.types import UUID
from onegov.core.security import Private
from onegov.form import FormDefinition
from onegov.form import FormRegistrationWindow
from onegov.form import FormSubmission
from onegov.form import FormSubmissionCollection
from onegov.org import _
from onegov.org import OrgApp
from onegov.org.forms import FormSubmissionsExport
from onegov.org.layout import FormSubmissionLayout
from onegov.core.elements import Link
from onegov.org.utils import keywords_first
from onegov.ticket import Ticket
from sedate import align_range_to_day, as_datetime, standardize_date
from sqlalchemy import and_


from typing import Any, NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Sequence
    from datetime import date, datetime
    from onegov.core.types import RenderData
    from onegov.form.types import RegistrationState
    from onegov.org.request import OrgRequest
    from onegov.pay.types import PaymentMethod
    from sedate.types import DateLike, TzInfoOrName
    from sqlalchemy.orm import Query
    from webob import Response

    class FormSubmissionRow(NamedTuple):
        title: str
        email: str | None
        received: datetime
        payment_method: PaymentMethod | None
        data: dict[str, Any]
        ticket_number: str
        registration_state: RegistrationState | None
        registration_window_start: date
        registration_window_end: date


@OrgApp.form(
    model=FormDefinition,
    name='export',
    permission=Private,
    form=FormSubmissionsExport,
    template='export.pt'
)
def handle_form_submissions_export(
    self: FormDefinition,
    request: OrgRequest,
    form: FormSubmissionsExport,
    layout: FormSubmissionLayout | None = None
) -> RenderData | Response:

    layout = layout or FormSubmissionLayout(self, request)
    layout.breadcrumbs.append(Link(_('Export'), '#'))
    layout.editbar_links = None

    if form.submitted(request):
        submissions = FormSubmissionCollection(request.session, name=self.name)

        if form.data['selection'] == 'date':
            query = subset_by_date(
                submissions=submissions,
                start=form.data['start'],
                end=form.data['end'],
                timezone=layout.timezone)

        elif form.data['selection'] == 'window':
            query = subset_by_window(
                submissions=submissions,
                window_ids=form.data['registration_window'])
        else:
            raise NotImplementedError

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
        'explanation': _('Exports the submissions of the given date range.')
    }


def subset_by_date(
    submissions: FormSubmissionCollection,
    start: DateLike,
    end: DateLike,
    timezone: TzInfoOrName
) -> Query[FormSubmission]:

    start, end = align_range_to_day(
        standardize_date(as_datetime(start), timezone),
        standardize_date(as_datetime(end), timezone),
        timezone)

    return (
        submissions.query()
        .filter_by(state='complete')
        .filter(and_(
            FormSubmission.received >= start,
            FormSubmission.received <= end)
        )
    )


def subset_by_window(
    submissions: FormSubmissionCollection,
    window_ids: Collection[UUID]
) -> Query[FormSubmission]:
    return (
        submissions.query()
        .filter_by(state='complete')
        .filter(FormSubmission.registration_window_id.in_(window_ids))
    )


def configure_subset(
    subset: Query[FormSubmission]
) -> Query[FormSubmissionRow]:
    subset = subset.join(
        Ticket,
        FormSubmission.id == Ticket.handler_id.cast(UUID)
    )

    subset = subset.join(
        FormRegistrationWindow,
        FormSubmission.registration_window_id == FormRegistrationWindow.id,
        isouter=True
    )

    return subset.with_entities(
        FormSubmission.title,
        FormSubmission.email,
        FormSubmission.received,
        FormSubmission.payment_method,
        FormSubmission.data,
        Ticket.number.label('ticket_number'),
        FormSubmission.registration_state,
        FormRegistrationWindow.start.label('registration_window_start'),
        FormRegistrationWindow.end.label('registration_window_end'),
    )


def run_export(
    subset: Query[FormSubmissionRow],
    nested: bool,
    formatter: Callable[[object], Any]
) -> tuple[Callable[[str], tuple[int, str]], Sequence[dict[str, Any]]]:

    keywords = (
        'ticket_number',
        'title',
        'email',
        'received',
        'payment_method',
        'registration_state',
        'registration_window_start',
        'registration_window_end'
    )

    def transform(submission: FormSubmissionRow) -> dict[str, Any]:
        r = OrderedDict()

        for keyword in keywords:
            r[keyword] = formatter(getattr(submission, keyword))

        if nested:
            r['form'] = {
                k: formatter(v)
                for k, v in submission.data.items()
            }
        else:
            for k, v in submission.data.items():
                r[f'form_{k}'] = formatter(v)

        return r

    return keywords_first(keywords), tuple(transform(s) for s in subset)
