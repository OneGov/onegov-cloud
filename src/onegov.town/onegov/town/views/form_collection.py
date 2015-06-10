""" Lists the builtin and custom forms. """

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
from sqlalchemy import desc


@TownApp.html(model=FormCollection, template='forms.pt', permission=Public)
def view_form_collection(self, request):

    if request.is_logged_in:
        forms = self.get_definitions_with_submission_count()
    else:
        forms = self.definitions.query().order_by(FormDefinition.name).all()

    return {
        'layout': FormCollectionLayout(self, request),
        'title': _("Forms"),
        'forms': forms
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
