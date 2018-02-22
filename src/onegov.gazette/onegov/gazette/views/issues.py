from datetime import date
from morepath import redirect
from onegov.core.security import Private
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import IssueCollection
from onegov.gazette.forms import EmptyForm
from onegov.gazette.forms import IssueForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import Issue


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
        'new_issue': request.link(self, name='new-issue')
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

    layout = Layout(self, request)
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
