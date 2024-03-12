from onegov.landsgemeinde import _
from onegov.core.security import Private
from onegov.landsgemeinde.app import LandsgemeindeApp
from onegov.org.views.people import handle_new_person, handle_edit_person
from onegov.landsgemeinde.forms import PersonForm
from onegov.town6.layout import PersonCollectionLayout
from onegov.people import Person, PersonCollection


@LandsgemeindeApp.form(model=PersonCollection, name='new', template='form.pt',
                       permission=Private, form=PersonForm)
def landsgemeinde_handle_new_person(self, request, form):
    form.location_code_city.label.text = _('Location')
    layout = PersonCollectionLayout(self, request)
    return handle_new_person(self, request, form, layout)


@LandsgemeindeApp.form(model=Person, name='edit', template='form.pt',
                       permission=Private, form=PersonForm)
def landsgemeinde_handle_edit_person(self, request, form):
    form.location_code_city.label.text = _('Location')
    layout = PersonCollectionLayout(self, request)
    return handle_edit_person(self, request, form, layout)
