import morepath

from onegov.core.security import Private, Public
from onegov.core.utils import normalize_for_url
from onegov.form import FormCollection, FormDefinition
from onegov.form.collection import SurveyCollection
from onegov.form.models.definition import SurveyDefinition
from onegov.gis import Coordinates
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.forms import FormDefinitionForm
from onegov.org.forms.form_definition import SurveyDefinitionForm
from onegov.org.layout import FormEditorLayout, SurveySubmissionLayout
from onegov.org.models import BuiltinFormDefinition, CustomFormDefinition


from typing import TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.layout import Layout
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.form import SurveySubmissionWindow
    from onegov.org.request import OrgRequest
    from webob import Response

    FormDefinitionT = TypeVar('FormDefinitionT', bound=FormDefinition)


def get_hints(
    layout: 'Layout',
    window: 'SurveySubmissionWindow | None'
) -> 'Iterator[tuple[str, str]]':

    if not window:
        return

    if window.in_the_past:
        yield 'stop', _("The survey timeframe has ended")

    if window.in_the_future:
        yield 'date', _(
            "The survey timeframe opens on ${day}, ${date}", mapping={
                'day': layout.format_date(window.start, 'weekday_long'),
                'date': layout.format_date(window.start, 'date_long')
            })

    if window.in_the_present:
        yield 'date', _(
            "The survey timeframe closes on ${day}, ${date}", mapping={
                'day': layout.format_date(window.end, 'weekday_long'),
                'date': layout.format_date(window.end, 'date_long')
            })


@OrgApp.form(
    model=SurveyCollection,
    name='new', template='form.pt',
    permission=Private, form=SurveyDefinitionForm
)
def handle_new_survey_definition(
    self: SurveyCollection,
    request: 'OrgRequest',
    form: SurveyDefinitionForm,
    layout: FormEditorLayout | None = None
) -> 'RenderData | Response':

    if form.submitted(request):
        assert form.title.data is not None
        assert form.definition.data is not None

        if self.definitions.by_name(normalize_for_url(form.title.data)):
            request.alert(_("A survey with this name already exists"))
        else:
            definition = self.definitions.add(
                title=form.title.data,
                definition=form.definition.data,
            )
            form.populate_obj(definition)

            request.success(_("Added a new survey"))
            return morepath.redirect(request.link(definition))

    layout = layout or FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Forms"), request.class_link(FormCollection)),
        Link(_("New Survey"), request.link(self, name='new'))
    ]
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _("New Survey"),
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
    request: 'OrgRequest',
    form: 'Form',
    layout: SurveySubmissionLayout | None = None
) -> 'RenderData | Response':
    """ Renders the empty survey and takes input, even if it's not valid,
    stores it as a pending submission and redirects the user to the view that
    handles pending submissions.

    """

    collection = SurveyCollection(request.session)

    if not self.current_submission_window:
        enabled = True
    else:
        enabled = self.current_submission_window.accepts_submissions()

    if enabled and request.POST:
        submission = collection.submissions.add(
            self.name, form, state='pending')

        return morepath.redirect(request.link(submission))

    layout = layout or SurveySubmissionLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'form': enabled and form,
        'definition': self,
        'form_width': 'small',
        'lead': layout.linkify(self.meta.get('lead')),
        'text': self.content.get('text'),
        'people': getattr(self, 'people', None),
        'files': getattr(self, 'files', None),
        'contact': getattr(self, 'contact_html', None),
        'coordinates': getattr(self, 'coordinates', Coordinates()),
        'hints': tuple(get_hints(layout, self.current_submission_window)),
        'hints_callout': not enabled,
        'button_text': _('Continue')
    }


@OrgApp.form(
    model=SurveyDefinition,
    template='form.pt', permission=Private,
    form=SurveyDefinitionForm, name='edit'
)
def handle_edit_survey_definition(
    self: SurveyDefinition,
    request: 'OrgRequest',
    form: SurveyDefinitionForm,
    layout: FormEditorLayout | None = None
) -> 'RenderData | Response':

    if form.submitted(request):
        assert form.definition.data is not None
        # why do we exclude definition here? we set it normally right after
        # which is also what populate_obj should be doing
        form.populate_obj(self, exclude={'definition'})
        self.definition = form.definition.data

        request.success(_("Your changes were saved"))
        return morepath.redirect(request.link(self))
    elif not request.POST:
        form.process(obj=self)

    collection = SurveyCollection(request.session)

    layout = layout or FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Surveys"), request.link(collection)),
        Link(self.title, request.link(self)),
        Link(_("Edit"), request.link(self, name='edit'))
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
    request: 'OrgRequest',
    layout: SurveySubmissionLayout | None = None
) -> 'RenderData':

    submissions = self.submissions
    results = self.get_results(request)
    aggregated = ['MultiCheckboxField', 'CheckboxField', 'RadioField']

    form = request.get_form(self.form_class)
    all_fields = form._fields
    all_fields.pop('csrf_token', None)
    fields = all_fields.values()

    layout = layout or SurveySubmissionLayout(self, request)
    layout.breadcrumbs.append(
        Link(_("Results"), request.link(self, name='results'))
    )
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': _("Results"),
        'results': results,
        'fields': fields,
        'aggregated': aggregated,
        'submission_count': len(submissions),
        'submission_windows': self.submission_windows
    }
