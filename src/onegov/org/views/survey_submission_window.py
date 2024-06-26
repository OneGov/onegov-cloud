from onegov.core.security import Private
from onegov.form.models.definition import SurveyDefinition
from onegov.form.models.submission import SurveySubmission
from onegov.form.models.survey_window import SurveySubmissionWindow
from onegov.org import OrgApp, _
from onegov.org.forms.survey_submission import SurveySubmissionWindowForm
from onegov.org.layout import SurveySubmissionLayout
from onegov.core.elements import Link, Confirm, Intercooler


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from webob import Response


@OrgApp.form(
    model=SurveyDefinition,
    name='new-submission-window',
    permission=Private,
    form=SurveySubmissionWindowForm,
    template='form.pt'
)
def handle_new_submision_form(
    self: SurveyDefinition,
    request: 'OrgRequest',
    form: SurveySubmissionWindowForm,
    layout: SurveySubmissionLayout | None = None
) -> 'RenderData | Response':
    title = _("New Submission Window")

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

        request.success(_("The registration window was added successfully"))
        return request.redirect(request.link(self))

    return {
        'layout': layout,
        'title': title,
        'form': form,
        'helptext': _(
            "Submissions windows limit survey submissions to a specific "
            "time-range."
        )
    }


@OrgApp.html(
    model=SurveySubmissionWindow,
    permission=Private,
    template='submission_window.pt'
)
def view_submission_window(
    self: SurveySubmissionWindow,
    request: 'OrgRequest',
    layout: SurveySubmissionLayout | None = None
) -> 'RenderData':

    layout = layout or SurveySubmissionLayout(self.survey, request)
    title = layout.format_date_range(self.start, self.end)
    layout.breadcrumbs.append(Link(title, '#'))
    layout.editbar_links = [
        Link(
            text=_("Edit"),
            url=request.link(self, 'edit'),
            attrs={'class': 'edit-link'}
        ),
        Link(
            text=_("Delete"),
            url=layout.csrf_protected_url(request.link(self)),
            attrs={'class': 'delete-link'},
            traits=(
                Confirm(
                    _(
                        "Do you really want to delete "
                        "this submission window?"
                    ),
                    _("Existing submissions will be disassociated."),
                    _("Delete submission window"),
                    _("Cancel")
                ),
                Intercooler(
                    request_method='DELETE',
                    redirect_after=request.link(self.survey)
                )
            )
        )
    ]

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
        'title': title,
        'model': self,
        'results': results,
        'fields': fields,
        'aggregated': aggregated,
        'submission_count': len(submissions)
    }


@OrgApp.form(
    model=SurveySubmissionWindow,
    permission=Private,
    form=SurveySubmissionWindowForm,
    template='form.pt',
    name='edit'
)
def handle_edit_registration_form(
    self: SurveySubmissionWindow,
    request: 'OrgRequest',
    form: SurveySubmissionWindowForm,
    layout: SurveySubmissionLayout | None = None
) -> 'RenderData | Response':

    title = _("Edit Submission Window")

    layout = layout or SurveySubmissionLayout(self.survey, request)
    layout.breadcrumbs.append(Link(title, '#'))
    layout.edit_mode = True

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))
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
def delete_registration_window(
    self: SurveySubmissionWindow,
    request: 'OrgRequest'
) -> None:

    request.assert_valid_csrf_token()

    self.disassociate()
    request.session.delete(self)

    request.success(_("The submission window was deleted"))
