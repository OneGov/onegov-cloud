""" Lists the builtin and custom forms. """

from onegov.core.security import Public
from onegov.form import FormCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.layout import FormCollectionLayout
from unidecode import unidecode


@TownApp.html(model=FormCollection, template='forms.pt', permission=Public)
def view_form_collection(self, request):

    # XXX add collation support to the core (create collations automatically)
    forms = self.definitions.query().all()
    forms = sorted(forms, key=lambda d: unidecode(d.title))

    return {
        'layout': FormCollectionLayout(self, request),
        'title': _("Forms"),
        'forms': request.exclude_invisible(forms)
    }
