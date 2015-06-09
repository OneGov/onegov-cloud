""" Lists the builtin and custom forms. """

from functools import partial

from onegov.core.security import Public, Private
from onegov.form import (
    FormCollection,
    FormSubmissionCollection,
    FormDefinition,
    FormSubmission
)
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout, FormCollectionLayout
from sqlalchemy import desc, func


def get_definitions_with_submission_count(session):
    """ Returns all form definitions and the number of submissions belonging
    to those definitions, in a single query.

    """
    submissions = session.query(
        FormSubmission.name,
        func.count(FormSubmission.id).label('count')
    )
    submissions = submissions.filter(FormSubmission.state == 'complete')
    submissions = submissions.group_by(FormSubmission.name).subquery()

    definitions = session.query(FormDefinition, submissions.c.count)
    definitions = definitions.outerjoin(
        submissions, submissions.c.name == FormDefinition.name
    )
    definitions = definitions.order_by(FormDefinition.name)

    for form, submissions_count in definitions.all():
        form.submissions_count = submissions_count or 0
        yield form


@TownApp.html(model=FormCollection, template='forms.pt', permission=Public)
def view_form_collection(self, request):

    if request.is_logged_in:
        forms = get_definitions_with_submission_count(request.app.session())
    else:
        forms = self.definitions.query().order_by(FormDefinition.name).all()

    return {
        'layout': FormCollectionLayout(self, request),
        'title': _("Forms"),
        'forms': forms,
        'get_submissions_collection': partial(
            self.scoped_submissions, ensure_existance=False)
    }


@TownApp.html(model=FormSubmissionCollection, template='submissions.pt',
              permission=Private)
def view_form_submission_collection(self, request):

    form_collection = FormCollection(request.app.session())
    form = form_collection.definitions.by_name(self.name)

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Forms"), request.link(form_collection)),
        Link(form.title, request.link(form)),
        Link(_("Submissions"), '#')
    ]

    submissions = self.query().order_by(desc(FormSubmission.received))

    return {
        'layout': layout,
        'title': _("Submissions for \"${form}\"", mapping={
            'form': form.title
        }),
        'submissions': submissions
    }
