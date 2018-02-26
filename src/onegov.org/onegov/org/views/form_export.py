from collections import OrderedDict
from onegov.core.orm.types import UUID
from onegov.core.security import Private
from onegov.form import FormDefinition
from onegov.form import FormSubmission
from onegov.form import FormSubmissionCollection
from onegov.form import merge_forms
from onegov.org import _
from onegov.org import OrgApp
from onegov.org.forms.generic import DateRangeForm, ExportForm
from onegov.org.layout import FormSubmissionLayout
from onegov.org.new_elements import Link
from onegov.org.utils import keywords_first
from onegov.ticket import Ticket
from sedate import align_range_to_day, as_datetime, standardize_date
from sqlalchemy import and_


@OrgApp.form(
    model=FormDefinition,
    name='export',
    permission=Private,
    form=merge_forms(DateRangeForm, ExportForm),
    template='export.pt')
def handle_form_submissions_export(self, request, form):

    layout = FormSubmissionLayout(self, request)
    layout.breadcrumbs.append(Link(_("Export"), '#'))
    layout.editbar_links = None

    if form.submitted(request):
        field_order, results = run_export(
            session=request.session,
            definition=self,
            start=form.data['start'],
            end=form.data['end'],
            nested=form.format == 'json',
            formatter=layout.export_formatter(form.format),
            timezone=layout.timezone)

        return form.as_export_response(results, self.title, key=field_order)

    return {
        'title': _("Export"),
        'layout': layout,
        'form': form,
        'explanation': _("Exports the submissions of the given date range.")
    }


def run_export(session, definition, start, end, timezone, nested, formatter):
    start, end = align_range_to_day(
        standardize_date(as_datetime(start), timezone),
        standardize_date(as_datetime(end), timezone),
        timezone
    )

    submissions = FormSubmissionCollection(session, name=definition.name)
    subset = submissions.query().filter_by(state='complete').filter(and_(
        FormSubmission.received >= start,
        FormSubmission.received <= end
    ))
    subset = subset.join(
        Ticket, FormSubmission.id == Ticket.handler_id.cast(UUID)
    )
    subset = subset.with_entities(
        FormSubmission.title,
        FormSubmission.email,
        FormSubmission.received,
        FormSubmission.payment_method,
        FormSubmission.data,
        Ticket.number.label('ticket_number')
    )

    keywords = (
        'ticket_number',
        'title',
        'email',
        'received',
        'payment_method'
    )

    def transform(submission):
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
