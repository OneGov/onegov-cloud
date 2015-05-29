""" Builtin and custom forms defined in the database. """

from onegov.form import FormCollection, FormDefinition
from onegov.core.security import Public
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout


@TownApp.html(model=FormCollection, template='forms.pt', permission=Public)
def view_get_form_collection(self, request):
    forms = self.definitions.query().order_by(FormDefinition.name).all()

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Forms"), request.link(self))
    ]

    return {
        'layout': layout,
        'title': _("Forms"),
        'forms': forms,
    }


@TownApp.form(model=FormDefinition, form=lambda e: e.form_class,
              template='form.pt', permission=Public)
def handle_defined_form(self, request, form):

    collection = FormCollection(request.app.session())

    if form.submitted(request):
        pass

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Forms"), request.link(collection)),
        Link(self.title, request.link(self))
    ]

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
        'form_width': 'small'
    }
