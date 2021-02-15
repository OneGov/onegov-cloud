from onegov.core.security import Public, Private
from onegov.org.views.people import view_people, view_person, \
    handle_new_person, handle_edit_person
from onegov.town6 import _, TownApp
from onegov.org.forms import PersonForm

from onegov.people import Person, PersonCollection


@TownApp.html(model=PersonCollection, template='people.pt', permission=Public)
def town_view_people(self, request):
    return view_people(self, request)


@TownApp.html(model=Person, template='person.pt', permission=Public)
def town_view_person(self, request):
    return view_person(self, request)


@TownApp.form(model=PersonCollection, name='new', template='form.pt',
             permission=Private, form=PersonForm)
def town_handle_new_person(self, request, form):
    return handle_new_person(self, request, form)


@TownApp.form(model=Person, name='edit', template='form.pt',
             permission=Private, form=PersonForm)
def town_handle_edit_person(self, request, form):
    return handle_edit_person(self, request, form)
