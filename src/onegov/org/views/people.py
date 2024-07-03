import morepath
from morepath.request import Response
from sqlalchemy.orm import undefer
from onegov.core.security import Public, Private
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.forms import PersonForm
from onegov.org.layout import PersonLayout, PersonCollectionLayout
from onegov.org.models import AtoZ, Topic
from onegov.people import Person, PersonCollection
from markupsafe import Markup


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from webob import Response as BaseResponse


@OrgApp.html(model=PersonCollection, template='people.pt', permission=Public)
def view_people(
    self: PersonCollection,
    request: 'OrgRequest',
    layout: PersonCollectionLayout | None = None
) -> 'RenderData':

    selected_org = request.params.get('organisation', None)
    selected_sub_org = request.params.get('sub_organisation', None)

    query = self.query().order_by(Person.last_name, Person.first_name)

    if selected_org:
        query = query.filter(Person.organisation == selected_org)
    if selected_sub_org:
        query = query.filter(Person.sub_organisation == selected_sub_org)

    people = query.all()

    class AtoZPeople(AtoZ[Person]):

        def get_title(self, item: Person) -> str:
            return item.title

        def get_items(self) -> list[Person]:
            return people

    orgs = (PersonCollection(request.session)
            .unique_organisations)  # type: ignore[attr-defined]
    sub_orgs = (PersonCollection(request.session)
                .unique_sub_organisations)  # type: ignore[attr-defined]

    return {
        'title': _("People"),
        'people': AtoZPeople(request).get_items_by_letter().items(),
        'layout': layout or PersonCollectionLayout(self, request),
        'organisations': orgs,
        'sub_organisations': sub_orgs,
        'selected_organisation': selected_org,
        'selected_sub_organisation': selected_sub_org
    }


@OrgApp.html(model=Person, template='person.pt', permission=Public)
def view_person(
    self: Person,
    request: 'OrgRequest',
    layout: PersonLayout | None = None
) -> 'RenderData':

    query = request.session.query(Topic)
    query = query.options(undefer('content'))
    org_to_func = person_functions_by_organization(self, query, request)
    return {
        'title': self.title,
        'person': self,
        'layout': layout or PersonLayout(self, request),
        'organization_to_function': org_to_func
    }


def person_functions_by_organization(
    subject_person: Person,
    topics: 'Iterable[Topic]',
    request: 'OrgRequest'
) -> 'Iterable[Markup]':
    """ Collects 1:1 mappings of all context-specific functions and
     organizations for a person. Organizations are pages where `subject_person`
     is listed as a person.

     Returns a List of Markup in the form:

        - Organization 1: Function A
        - Organization 2: Function B
        - ...

    This is not necessarily the same as person.function!
    """

    sorted_topics = sorted(
        (
            (func, topic)
            for topic in topics
            for pers in (topic.people or [])
            if (
                pers.id == subject_person.id
                and (func := getattr(pers, "context_specific_function", None))
                is not None
                and getattr(pers, "display_function_in_person_directory",
                            False) is not False
            )
        ),
        key=lambda pair: pair[1].title,
    )
    if not sorted_topics:
        return ()

    return (
        Markup('<span><a href="{url}">{title}</a>: {function}</span>').format(
            url=request.link(topic),
            title=topic.title,
            function=function
        )
        for function, topic in sorted_topics
    )


@OrgApp.form(
    model=PersonCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=PersonForm
)
def handle_new_person(
    self: PersonCollection,
    request: 'OrgRequest',
    form: PersonForm,
    layout: PersonCollectionLayout | None = None
) -> 'RenderData | BaseResponse':

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


@OrgApp.form(
    model=Person,
    name='edit',
    template='form.pt',
    permission=Private,
    form=PersonForm
)
def handle_edit_person(
    self: Person,
    request: 'OrgRequest',
    form: PersonForm,
    layout: PersonLayout | None = None
) -> 'RenderData | BaseResponse':

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
def handle_delete_person(self: Person, request: 'OrgRequest') -> None:
    request.assert_valid_csrf_token()
    PersonCollection(request.session).delete(self)


@OrgApp.view(model=Person, name='vcard', permission=Public)
def vcard_export_person(self: Person, request: 'OrgRequest') -> Response:
    """ Returns the persons vCard. """

    exclude = request.app.org.excluded_person_fields(request) + ['notes']

    return Response(
        self.vcard(exclude),
        content_type='text/vcard',
        content_disposition='inline; filename=card.vcf'
    )
