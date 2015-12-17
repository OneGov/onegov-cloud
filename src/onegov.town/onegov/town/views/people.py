import morepath

from onegov.core.security import Public, Private
from onegov.people import Person, PersonCollection
from onegov.town import _, TownApp
from onegov.town.elements import Link
from onegov.town.forms import PersonForm
from onegov.town.layout import PersonLayout, PersonCollectionLayout
from onegov.town.models import AtoZ


@TownApp.html(model=PersonCollection, template='people.pt', permission=Public)
def view_people(self, request):

    people = self.query().order_by(Person.last_name, Person.first_name)

    class AtoZPeople(AtoZ):

        def get_title(self, item):
            return item.title

        def get_items(self):
            return people

    return {
        'title': _("People"),
        'people': AtoZPeople(request).get_items_by_letter().items(),
        'layout': PersonCollectionLayout(self, request)
    }


@TownApp.html(model=Person, template='person.pt', permission=Public)
def view_person(self, request):

    return {
        'title': self.title,
        'person': self,
        'layout': PersonLayout(self, request)
    }


@TownApp.form(model=PersonCollection, name='neu', template='form.pt',
              permission=Private, form=PersonForm)
def handle_new_person(self, request, form):

    if form.submitted(request):
        person = self.add(**form.get_useful_data())
        request.success(_("Added a new person"))

        return morepath.redirect(request.link(person))

    layout = PersonCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _("New person"),
        'form': form
    }


@TownApp.form(model=Person, name='bearbeiten', template='form.pt',
              permission=Private, form=PersonForm)
def handle_edit_person(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))

        return morepath.redirect(request.link(self))
    else:
        form.process(obj=self)

    layout = PersonLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': self.title,
        'form': form
    }


@TownApp.view(model=Person, request_method='DELETE', permission=Private)
def handle_delete_person(self, request):
    PersonCollection(request.app.session()).delete(self)
