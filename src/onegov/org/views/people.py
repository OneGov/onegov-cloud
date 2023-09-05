import morepath

from morepath.request import Response
from onegov.core.security import Public, Private
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.forms import PersonForm
from onegov.org.layout import PersonLayout, PersonCollectionLayout
from onegov.org.models import AtoZ, Topic
from onegov.people import Person, PersonCollection
from markupsafe import Markup


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
    org_to_func = (person_functions_by_organization(self, pages, request)
        if self.show_context_specific_functions else []
    )

    return {
        'title': self.title,
        'person': self,
        'layout': layout or PersonLayout(self, request),
        'organization_to_function': org_to_func
    }


def person_functions_by_organization(subject_person, pages, request):
    """ Collects 1:1 mappings of all context-specific functions and
     organizations for a person. Organizations are pages where `subject_person`
     is listed as a person.

     Returns a List of strings in the form:

        - Organization 1, Function A
        - Organization 2, Function B

    This is not necessarily the same as person.function!
    """

    organization_to_function = []

    for topic in pages:
        people = topic.people
        for person in people or []:
            if person.id == subject_person.id:
                try:
                    if person.display_function_in_person_directory:
                        func = person.context_specific_function
                        if func:
                            page = f"<a href=\"{request.link(topic)}\">" \
                                   f"{topic.title}</a>"
                            organization_to_function.append(
                                Markup(f"<span>{page}: {func}</span>"))
                except AttributeError:
                    continue
    return organization_to_function


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
