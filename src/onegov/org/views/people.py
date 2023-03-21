import morepath

from morepath.request import Response
from onegov.core.security import Public, Private
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.forms import PersonForm
from onegov.org.layout import PersonLayout, PersonCollectionLayout
from onegov.org.models import AtoZ, Topic, ImageFileCollection
from onegov.org.path import get_file_for_org
from onegov.people import Person, PersonCollection
from markupsafe import Markup
from onegov.people.portrait_crop import crop_to_portrait_with_face_detection


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
    org_to_func = person_functions_by_organization(self, pages, request)

    return {
        'title': self.title,
        'person': self,
        'layout': layout or PersonLayout(self, request),
        'organization_to_function': org_to_func
    }


def person_functions_by_organization(subject, pages, request):
    """ Collects 1:1 mappings of all context-specific functions and
     organizations for a person. The organizations include the link.

     Returns a List of strings in the form:

        - Organization 1, Function A
        - Organization 2, Function B

    This is not necessarily the same as person.function!
    """

    organization_to_function = []

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
                    func = person.context_specific_function
                except AttributeError:
                    continue
                if func:
                    func = remove_duplicated_text(func, topic)
                    org_with_link = f"<a href=\"{request.link(topic)}\">" \
                                    f"{topic.title}</a>"
                    organization_to_function.append(
                        Markup(f"<span>{org_with_link}: {func}</span>")
                    )
    return organization_to_function


@OrgApp.form(model=PersonCollection, name='new', template='form.pt',
             permission=Private, form=PersonForm)
def handle_new_person(self, request, form, layout=None):

    if form.submitted(request):
        form_data = form.get_useful_data()
        person = self.add(**form.get_useful_data())
        picture_url = form_data['picture_url']
        if picture_url:
            create_quadratic_profile_image(person, picture_url, request)

        form.populate_obj(person)
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


def create_quadratic_profile_image(person, picture_url, request):
    try:
        picture_id = picture_url.rsplit('/', 1)[-1]
        f = get_file_for_org(request, request.app, picture_id)
        actual_profile_image = request.app.bound_depot.get(
            f.reference.file_id
        )
        quadratic_image_bytes = crop_to_portrait_with_face_detection(
            actual_profile_image._file_path
        )
        if quadratic_image_bytes:
            quadratic_image = ImageFileCollection(request.session).add(
                filename=f"quadratic_{actual_profile_image.filename}",
                content=quadratic_image_bytes
            )
            person.quadratic_picture_url = request.link(quadratic_image)
    except Exception:
        pass


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
