import morepath

from morepath.request import Response
from onegov.core.security import Public, Private
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.forms import PersonForm
from onegov.org.layout import PersonLayout, PersonCollectionLayout
from onegov.org.models import AtoZ, Topic
from onegov.people import Person, PersonCollection


@OrgApp.html(model=PersonCollection, template='people.pt', permission=Public)
def view_people(self, request, layout=None):

    people = self.query().order_by(Person.last_name, Person.first_name)

    class AtoZPeople(AtoZ):

        def get_title(self, item):
            return item.title

        def get_items(self):
            return people

    return {
        'title': _("People"),
        'people': AtoZPeople(request).get_items_by_letter().items(),
        'layout': layout or PersonCollectionLayout(self, request)
    }


@OrgApp.html(model=Person, template='person.pt', permission=Public)
def view_person(self, request, layout=None):

    pages = request.session.query(Topic)
    pages = pages.filter(Topic.people is not None).all()
    orgs, functions = person_functions_by_organization(self, pages)

    return {
        'title': self.title,
        'person': self,
        'layout': layout or PersonLayout(self, request),
        'organizations': orgs,
        'functions': functions
    }


def person_functions_by_organization(subject, pages):
    """ Collects 1:1 mappings of all context-specific functions and
     organizations for a person. Returns two lists:

        - Organization 1, Function A
        - Organization 2, Function B

    This is not necessarily the same as person.function!
    """

    organizations = []
    functions = []

    def remove_duplicated_text(function, topic):
        if topic.title in function and not topic.title == function:
            function = function.replace(topic.title, "")
            function = function.rstrip()
        return function

    for topic in pages:
        people = topic.people
        if people is None:
            continue
        for person in people:
            if person.id == subject.id:
                try:
                    function = person.context_specific_function
                except AttributeError:
                    continue
                if function:
                    function = remove_duplicated_text(function, topic)
                    functions.append(function)
                    organizations.append(topic.title)
    return organizations, functions


@OrgApp.form(model=PersonCollection, name='new', template='form.pt',
             permission=Private, form=PersonForm)
def handle_new_person(self, request, form, layout=None):

    if form.submitted(request):
        person = self.add(**form.get_useful_data())
        request.success(_("Added a new person"))

        return morepath.redirect(request.link(person))

    layout = layout or PersonCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _("New person"),
        'form': form
    }


@OrgApp.form(model=Person, name='edit', template='form.pt',
             permission=Private, form=PersonForm)
def handle_edit_person(self, request, form, layout=None):

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))

        return morepath.redirect(request.link(self))
    else:
        form.process(obj=self)

    layout = layout or PersonLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': self.title,
        'form': form
    }


@OrgApp.view(model=Person, request_method='DELETE', permission=Private)
def handle_delete_person(self, request):
    request.assert_valid_csrf_token()
    PersonCollection(request.session).delete(self)


@OrgApp.view(model=Person, name='vcard', permission=Public)
def vcard_export_person(self, request):
    """ Returns the persons vCard. """

    exclude = request.app.org.excluded_person_fields(request) + ['notes']

    return Response(
        self.vcard(exclude),
        content_type='text/vcard',
        content_disposition='inline; filename=card.vcf'
    )
