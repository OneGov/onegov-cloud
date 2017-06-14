import morepath

from onegov.core.security import Private
from onegov.core.utils import normalize_for_url
from onegov.form import FormCollection, FormDefinition
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.forms import FormDefinitionForm
from onegov.org.layout import FormEditorLayout
from onegov.org.models import CustomFormDefinition
from webob import exc


def get_form_class(model, request):

    if isinstance(model, FormCollection):
        model = CustomFormDefinition()

    form_classes = {
        'builtin': FormDefinitionForm,
        'custom': FormDefinitionForm
    }

    return model.with_content_extensions(form_classes[model.type], request)


@OrgApp.form(model=FormCollection, name='neu', template='form.pt',
             permission=Private, form=get_form_class)
def handle_new_definition(self, request, form):

    if form.submitted(request):

        if self.definitions.by_name(normalize_for_url(form.title.data)):
            request.alert(_("A form with this name already exists"))
        else:
            definition = self.definitions.add(
                title=form.title.data,
                definition=form.definition.data,
                type='custom'
            )
            form.populate_obj(definition)

            request.success(_("Added a new form"))
            return morepath.redirect(request.link(definition))

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


@OrgApp.form(model=FormDefinition, template='form.pt', permission=Private,
             form=get_form_class, name='bearbeiten')
def handle_edit_definition(self, request, form):

    if form.submitted(request):
        form.populate_obj(self, exclude={'definition'})

        if self.type == 'custom':
            self.definition = form.definition.data

        request.success(_("Your changes were saved"))
        return morepath.redirect(request.link(self))
    elif not request.POST:
        form.process(obj=self)

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


@OrgApp.view(model=FormDefinition, request_method='DELETE',
             permission=Private)
def delete_form_definition(self, request):

    request.assert_valid_csrf_token()

    if self.type != 'custom':
        raise exc.HTTPMethodNotAllowed()

    if self.has_submissions(with_state='complete'):
        raise exc.HTTPMethodNotAllowed()

    FormCollection(request.app.session()).definitions.delete(
        self.name, with_submissions=False)
