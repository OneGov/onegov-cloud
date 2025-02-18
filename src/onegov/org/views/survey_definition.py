from __future__ import annotations

import morepath

from webob.exc import HTTPForbidden

from onegov.core.security import Private, Public
from onegov.core.utils import normalize_for_url
from onegov.form.collection import SurveyCollection
from onegov.form.models.definition import SurveyDefinition
from onegov.form.models.submission import SurveySubmission
from onegov.gis import Coordinates
from onegov.org import _, OrgApp
from onegov.core.elements import Confirm, Intercooler, Link
from onegov.org.forms.form_definition import SurveyDefinitionForm
from onegov.org.layout import (FormEditorLayout,
                               SurveySubmissionLayout)


from typing import TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.org.request import OrgRequest
    from webob import Response

    SurveyDefinitionT = TypeVar('SurveyDefinitionT', bound=SurveyDefinition)


@OrgApp.form(
    model=SurveyCollection,
    name='new', template='form.pt',
    permission=Private, form=SurveyDefinitionForm
)
def handle_new_survey_definition(
    self: SurveyCollection,
    request: OrgRequest,
    form: SurveyDefinitionForm,
    layout: FormEditorLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        assert form.title.data is not None
        assert form.definition.data is not None

        if self.definitions.by_name(normalize_for_url(form.title.data)):
            request.alert(_('A survey with this name already exists'))
        else:
            definition = self.definitions.add(
                title=form.title.data,
                definition=form.definition.data,
            )
            form.populate_obj(definition)

            request.success(_('Added a new survey'))
            return morepath.redirect(request.link(definition))

    layout = layout or FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Surveys'), request.class_link(SurveyCollection)),
        Link(_('New Survey'), request.link(self, name='new'))
    ]
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('New Survey'),
        'form': form,
        'form_width': 'large',
    }


@OrgApp.form(
    model=SurveyDefinition,
    template='form.pt', permission=Public,
    form=lambda self, request: self.form_class
)
def handle_defined_survey(
    self: SurveyDefinition,
    request: OrgRequest,
    form: Form,
    layout: SurveySubmissionLayout | None = None
) -> RenderData | Response:
    """ Renders the empty survey and takes input, even if it's not valid,
    stores it as a pending submission and redirects the user to the view that
    handles pending submissions.

    """

    collection = SurveyCollection(request.session)

    enabled = False
    hint = [('stop', _('Please choose a submission window'))]

    if not self.current_submission_window:
        enabled = True
        hint = []
    elif not request.is_manager:
        raise HTTPForbidden()

    if enabled and request.POST:
        submission = collection.submissions.add(
            self.name, form)

        return morepath.redirect(request.link(submission))

    layout = layout or SurveySubmissionLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'form': enabled and form,
        'definition': self,
        'form_width': 'small',
        'lead': layout.linkify(self.meta.get('lead')),
        'text': self.text,
        'people': getattr(self, 'people', None),
        'files': getattr(self, 'files', None),
        'contact': getattr(self, 'contact_html', None),
        'coordinates': getattr(self, 'coordinates', Coordinates()),
        'hints': hint,
        'hints_callout': not enabled,
    }


@OrgApp.form(
    model=SurveyDefinition,
    template='form.pt', permission=Private,
    form=SurveyDefinitionForm, name='edit'
)
def handle_edit_survey_definition(
    self: SurveyDefinition,
    request: OrgRequest,
    form: SurveyDefinitionForm,
    layout: FormEditorLayout | None = None
) -> RenderData | Response:

    info = _('This field cannot be edited because there are submissions '
             'associated with this survey. If you want to edit the definition '
             'please delete all submissions.')

    if self.submissions:
        form.definition.description = info
        form.definition.render_kw = {
            'rows': 32, 'disabled': 'true', 'title': request.translate(info)
        }
        form.definition.validators = []

    if form.submitted(request):
        if self.submissions:
            form.definition.data = self.definition
        assert form.definition.data is not None
        form.populate_obj(self)

        request.success(_('Your changes were saved'))
        return morepath.redirect(request.link(self))
    elif not request.POST:
        form.process(obj=self)

    collection = SurveyCollection(request.session)

    layout = layout or FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Surveys'), request.link(collection)),
        Link(self.title, request.link(self)),
        Link(_('Edit'), request.link(self, name='edit'))
    ]
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
        'form_width': 'large',
    }


@OrgApp.html(model=SurveyDefinition, template='survey_results.pt',
             permission=Private, name='results')
def view_survey_results(
    self: SurveyDefinition,
    request: OrgRequest,
    layout: SurveySubmissionLayout | None = None
) -> RenderData:

    submissions = self.submissions
    results = self.get_results(request)
    aggregated = ['MultiCheckboxField', 'CheckboxField', 'RadioField']

    form = request.get_form(self.form_class)
    all_fields = form._fields
    all_fields.pop('csrf_token', None)
    fields = all_fields.values()

    layout = layout or SurveySubmissionLayout(self, request)
    layout.breadcrumbs.append(Link(_('Results'), '#'))

    layout.editbar_links = [
        Link(
            text=_('Export'),
            url=request.link(self, name='export'),
            attrs={'class': 'export-link'}
        ),
        Link(
            text=_('Delete Submissions'),
            url=layout.csrf_protected_url(
                request.link(self, name='delete-submissions')),
            attrs={'class': 'delete-link'},
            traits=(
                Confirm(
                    _(
                        'Do you really want to delete '
                        'all submissions?'
                    ),
                    _('All submissions associated with this survey will be '
                      'deleted.'),
                    _('Delete submissions'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='DELETE',
                    redirect_after=request.link(self)
                ))
            )]

    return {
        'layout': layout,
        'title': _('Results'),
        'results': results,
        'fields': fields,
        'aggregated': aggregated,
        'submission_count': len(submissions),
        'submission_windows': self.submission_windows
    }


@OrgApp.view(
    model=SurveyDefinition,
    request_method='DELETE',
    permission=Private
)
def delete_survey_definition(
    self: SurveyDefinition,
    request: OrgRequest
) -> None:
    """
    Deletes the survey along with all its submissions.
    """

    request.assert_valid_csrf_token()

    SurveyCollection(request.session).definitions.delete(
        self.name,
        with_submission_windows=True,
    )


@OrgApp.view(
    model=SurveyDefinition,
    request_method='DELETE',
    name='delete-submissions',
    permission=Private
)
def delete_survey_entries(
    self: SurveyDefinition,
    request: OrgRequest
) -> None:
    """
    Deletes all survey submissions.
    """

    request.assert_valid_csrf_token()

    submissions = request.session.query(SurveySubmission)
    submissions = submissions.filter(SurveySubmission.name == self.name)

    submissions.delete()
