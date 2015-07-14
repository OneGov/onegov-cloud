""" Lists the builtin and custom forms. """

from onegov.core.security import Public
from onegov.form import FormCollection, FormDefinition
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.layout import FormCollectionLayout


@TownApp.html(model=FormCollection, template='forms.pt', permission=Public)
def view_form_collection(self, request):

    forms = self.definitions.query().order_by(FormDefinition.name).all()

    return {
        'layout': FormCollectionLayout(self, request),
        'title': _("Forms"),
        'forms': request.exclude_invisible(forms)
    }
