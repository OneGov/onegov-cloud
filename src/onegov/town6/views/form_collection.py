
from onegov.core.security import Public
from onegov.form import FormCollection
from onegov.org.views.form_collection import view_form_collection
from onegov.town6 import _, TownApp


@TownApp.html(model=FormCollection, template='forms.pt', permission=Public)
def town_view_form_collection(self, request):
    return view_form_collection(self, request)
