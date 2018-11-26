from datetime import date
from datetime import datetime
from io import BytesIO
from morepath import redirect
from morepath.request import Response
from onegov.core.security import Private
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import IssueCollection
from onegov.gazette.forms import EmptyForm
from onegov.gazette.forms import IssueForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import Issue
from onegov.gazette.pdf import IssuePrintOnlyPdf
from sedate import to_timezone
from xlsxwriter import Workbook


@GazetteApp.html(
    model=IssueCollection,
    template='issues.pt',
    permission=Private
)
def view_issues(self, request):
    """ View the list of issues.

    This view is only visible by a publisher.

    """
    layout = Layout(self, request)

    today = date.today()
    past_issues = self.query().filter(Issue.date < today)
    past_issues = past_issues.order_by(None).order_by(Issue.date.desc())
    next_issues = self.query().filter(Issue.date >= today)

    return {
        'title': _("Issues"),
        'layout': layout,
        'past_issues': past_issues,
        'next_issues': next_issues,
        'new_issue': request.link(self, name='new-issue'),
        'export': request.link(self, name='export'),
    }


@GazetteApp.form(
    model=IssueCollection,
    name='new-issue',
    template='form.pt',
    permission=Private,
    form=IssueForm
)
def create_issue(self, request, form):
    """ Create a new issue.

    This view is only visible by a publisher.

    """
    layout = Layout(self, request)

    if form.submitted(request):
        issue = Issue()
        form.update_model(issue)
        request.session.add(issue)
        request.message(_("Issue added."), 'success')
        return redirect(layout.manage_issues_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New Issue"),
        'button_text': _("Save"),
        'cancel': layout.manage_issues_link
    }


@GazetteApp.form(
    model=Issue,
    name='edit',
    template='form.pt',
    permission=Private,
    form=IssueForm
)
def edit_issue(self, request, form):
    """ Edit a issue.

    This view is only visible by a publisher.

    """

    layout = Layout(self, request)
    if form.submitted(request):
        form.update_model(self)
        request.message(_("Issue modified."), 'success')
        return redirect(layout.manage_issues_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.name,
        'subtitle': _("Edit Issue"),
        'button_text': _("Save"),
        'cancel': layout.manage_issues_link,
    }


@GazetteApp.form(
    model=Issue,
    name='delete',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def delete_issue(self, request, form):
    """ Delete a issue.

    Only unused issues may be deleted.

    This view is only visible by a publisher.

    """
    layout = Layout(self, request)
    session = request.session

    if self.in_use:
        request.message(
            _("Only unused issues may be deleted."),
            'alert'
        )
        return {
            'layout': layout,
            'title': self.name,
            'subtitle': _("Delete Issue"),
            'show_form': False
        }

    if form.submitted(request):
        collection = IssueCollection(session)
        collection.delete(self)
        request.message(_("Issue deleted."), 'success')
        return redirect(layout.manage_issues_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.name}
        ),
        'layout': layout,
        'form': form,
        'title': self.name,
        'subtitle': _("Delete Issue"),
        'button_text': _("Delete Issue"),
        'button_class': 'alert',
        'cancel': layout.manage_issues_link
    }


@GazetteApp.form(
    model=Issue,
    name='publish',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def publish_issue(self, request, form):
    """ Publish an issue.

    This moves all accepted notices related to this issue to the published
    state (if not already) and generates the PDF. The publication numbers are
    assigned during PDF creation.

    This view is only visible by a publisher.

    """

    layout = Layout(self, request)
    if not layout.publishing:
        return {
            'layout': layout,
            'title': self.name,
            'subtitle': _("Publish"),
            'callout': _("Publishing is disabled."),
            'show_form': False
        }

    if self.notices('submitted').first():
        request.message(
            _("There are submitted notices for this issue!"), 'warning'
        )
    if self.pdf:
        request.message(
            _("A PDF already exists for this issue!"), 'warning'
        )

    old_numbers = self.publication_numbers()
    if any(old_numbers.values()):
        request.message(
            _("There are already official notices with publication numbers!"),
            'warning'
        )

    if form.submitted(request):
        self.publish(request)
        request.message(_("Issue published."), 'success')

        new_numbers = self.publication_numbers()
        if any(old_numbers.values()) and old_numbers != new_numbers:
            request.message(
                _(
                    "The already assigned publication numbers have been "
                    "changed. Recreating the following issues might be needed."
                ), 'warning'
            )

        return redirect(layout.manage_issues_link)

    return {
        'layout': layout,
        'form': form,
        'title': self.name,
        'subtitle': _("Publish"),
        'button_text': _("Publish"),
        'cancel': layout.manage_issues_link,
        'message': _(
            (
                'Do you really want to publish "${item}"? This will assign '
                'the publication numbers to the official notices and create '
                'the PDF.'
            ),
            mapping={
                'item': self.name,
                'number': len(self.notices('accepted').all())
            }
        ),
    }


@GazetteApp.view(
    model=Issue,
    name='print-only-pdf',
    permission=Private
)
def print_only_pdf(self, request):
    """ Creates the PDF with all the print only notices of an issue. """

    response = Response()
    response.content_type = 'application/pdf'
    response.content_disposition = 'inline; filename={}-{}.pdf'.format(
        self.name,
        request.translate(_("Print only")).lower().replace(' ', '-')
    )
    response.body = IssuePrintOnlyPdf.from_issue(self, request).read()
    return response


@GazetteApp.view(
    model=IssueCollection,
    name='export',
    permission=Private
)
def export_issue(self, request):
    """ Export all issues as XLSX. The exported file can be re-imported
    using the import-issues command line command.

    """

    output = BytesIO()
    workbook = Workbook(output, {
        'default_date_format': 'dd.mm.yy'
    })
    datetime_format = workbook.add_format({'num_format': 'dd.mm.yy hh:mm'})

    worksheet = workbook.add_worksheet()
    worksheet.name = request.translate(_("Issues"))
    worksheet.write_row(0, 0, (
        request.translate(_("Year")),
        request.translate(_("Number")),
        request.translate(_("Date")),
        request.translate(_("Deadline"))
    ))

    timezone = request.app.principal.time_zone
    for index, issue in enumerate(self.query()):
        worksheet.write(index + 1, 0, issue.date.year)
        worksheet.write(index + 1, 1, issue.number)
        worksheet.write(index + 1, 2, issue.date)
        worksheet.write_datetime(
            index + 1, 3,
            to_timezone(issue.deadline, timezone).replace(tzinfo=None),
            datetime_format
        )

    workbook.close()
    output.seek(0)

    response = Response()
    response.content_type = (
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response.content_disposition = 'inline; filename={}-{}.xlsx'.format(
        request.translate(_("Issues")).lower(),
        datetime.utcnow().strftime('%Y%m%d%H%M')
    )
    response.body = output.read()

    return response
