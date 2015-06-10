import morepath

from onegov.core.security import Private
from onegov.form import Form, FormCollection, FormDefinition, with_options
from onegov.form.validators import ValidFormDefinition
from onegov.town import _, TownApp
from onegov.town.elements import Link
from onegov.town.layout import FormEditorLayout
from onegov.town.utils import sanitize_html, mark_images
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

    def get_meta(self):
        return {
            'lead': self.lead.data,
        }

    def set_meta(self, meta):
        self.lead.data = meta.get('lead', '')

    def get_content(self):
        return {
            'text': self.text.data
        }

    def set_content(self, content):
        self.text.data = content.get('text', '')


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


form_classes = {
    'builtin': BuiltinDefinitionForm,
    'custom': CustomDefinitionForm
}


@TownApp.form(model=FormCollection, name='neu', template='form.pt',
              permission=Private, form=CustomDefinitionForm)
def handle_new_definition(self, request, form):

    if form.submitted(request):

        # forms added online are always custom forms
        new_form = self.definitions.add(
            title=form.title.data,
            definition=form.definition.data,
            type='custom',
            meta=form.get_meta(),
            content=form.get_content()
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
              form=lambda m: form_classes[m.type], name='bearbeiten')
def handle_edit_definition(self, request, form):

    if form.submitted(request):
        self.title = form.title.data

        if self.type == 'custom':
            self.definition = form.definition.data

        self.meta = form.get_meta()
        self.content = form.get_content()

        request.success(_("Your changes were saved"))
        return morepath.redirect(request.link(self))
    else:
        form.title.data = self.title
        form.definition.data = self.definition
        form.set_meta(self.meta)
        form.set_content(self.content)

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
    assert self.type == 'custom'
    assert not self.has_submissions(with_state='complete')
    request.assert_valid_csrf_token()

    FormCollection(request.app.session()).definitions.delete(
        self.name, with_submissions=False)
