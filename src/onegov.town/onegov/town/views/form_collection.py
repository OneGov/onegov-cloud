""" Lists the builtin and custom forms. """

from onegov.core.security import Public
from onegov.form import FormCollection, FormDefinition, FormSubmission
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.layout import FormCollectionLayout

from sqlalchemy import func


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
def view_get_form_collection(self, request):

    if request.is_logged_in:
        forms = get_definitions_with_submission_count(request.app.session())
    else:
        forms = self.definitions.query().order_by(FormDefinition.name).all()

    return {
        'layout': FormCollectionLayout(self, request),
        'title': _("Forms"),
        'forms': forms,
    }
