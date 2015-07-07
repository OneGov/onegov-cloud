import morepath

from onegov.core.security import Private
from onegov.core.utils import Bunch, sanitize_html
from onegov.form import Form, FormCollection, FormDefinition, with_options
from onegov.form.validators import ValidFormDefinition
from onegov.town import _, TownApp
from onegov.town.elements import Link
from onegov.town.layout import FormEditorLayout
from onegov.town.models import CustomFormDefinition
from onegov.town.models.mixins import extend_form
from onegov.town.utils import mark_images
from webob import exc
from wtforms import StringField, TextAreaField, validators
from wtforms.widgets import TextArea


class FormDefinitionBaseForm(Form):
    """ Form to edit defined forms. """

    title = StringField(_("Title"), [validators.InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this form is about"),
        widget=with_options(TextArea, rows=4))

    text = TextAreaField(
        label=_(u"Text"),
        widget=with_options(TextArea, class_='editor'),
        filters=[sanitize_html, mark_images])

    def get_page(self, page):
        page.title = self.title.data

        if page.type == 'custom':
            page.definition = self.definition.data

        page.meta['lead'] = self.lead.data
        page.content['text'] = self.text.data

    def set_page(self, page):
        self.title.data = page.title
        self.definition.data = page.definition
        self.lead.data = page.meta.get('lead', '')
        self.text.data = page.content.get('text', '')


class BuiltinDefinitionForm(FormDefinitionBaseForm):
    """ Form to edit builtin forms. """

    definition = TextAreaField(
        label=_(u"Definition"),
        validators=[validators.InputRequired(), ValidFormDefinition()],
        widget=with_options(
            TextArea, rows=24, readonly='readonly',
            **{'data-editor': 'form'}
        ),
    )


class CustomDefinitionForm(FormDefinitionBaseForm):
    """ Same as the default form definition form, but with the definition
    made read-only.

    """

    definition = TextAreaField(
        label=_(u"Definition"),
        validators=[validators.InputRequired(), ValidFormDefinition()],
        widget=with_options(TextArea, rows=32, **{'data-editor': 'form'}),
    )


def get_form_class(model, request):

    if isinstance(model, FormCollection):
        model = CustomFormDefinition()

    form_classes = {
        'builtin': BuiltinDefinitionForm,
        'custom': CustomDefinitionForm
    }

    return extend_form(form_classes[model.type], request, (
        model.extend_form_with_hidden_switch,
        model.extend_form_with_contact,
        model.extend_form_with_people,
    ))


@TownApp.form(model=FormCollection, name='neu', template='form.pt',
              permission=Private, form=get_form_class)
def handle_new_definition(self, request, form):

    if form.submitted(request):

        page = Bunch(
            title=None, definition=None, type='custom', meta={}, content={})
        form.get_page(page)

        # forms added online are always custom forms
        new_form = self.definitions.add(
            title=page.title,
            definition=page.definition,
            type='custom',
            meta=page.meta,
            content=page.content
        )

        request.success(_("Added a new form"))
        return morepath.redirect(request.link(new_form))

    layout = FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Forms"), request.link(self)),
        Link(_("New Form"), request.link(self, name='neu'))
    ]

    return {
        'layout': layout,
        'title': _("New Form"),
        'form': form,
        'form_width': 'large',
    }


@TownApp.form(model=FormDefinition, template='form.pt', permission=Private,
              form=get_form_class, name='bearbeiten')
def handle_edit_definition(self, request, form):

    if form.submitted(request):
        self.title = form.title.data

        if self.type == 'custom':
            self.definition = form.definition.data

        form.get_page(self)

        request.success(_("Your changes were saved"))
        return morepath.redirect(request.link(self))
    else:
        form.title.data = self.title
        form.definition.data = self.definition
        form.set_page(self)

    collection = FormCollection(request.app.session())

    layout = FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Forms"), request.link(collection)),
        Link(self.title, request.link(self)),
        Link(_("Edit"), request.link(self, name='bearbeiten'))
    ]

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
        'form_width': 'large',
    }


@TownApp.view(model=FormDefinition, request_method='DELETE',
              permission=Private)
def delete_form_definition(self, request):

    request.assert_valid_csrf_token()

    if self.type != 'custom':
        raise exc.HTTPMethodNotAllowed()

    if self.has_submissions(with_state='complete'):
        raise exc.HTTPMethodNotAllowed()

    FormCollection(request.app.session()).definitions.delete(
        self.name, with_submissions=False)
