from __future__ import annotations

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


def organisations_as_dict(person: Person) -> dict[str, list[str]]:
    current_org: str = ''
    org_dict: dict[str, list[str]] = {}
    for org in person.content.get('organisations_multiple', []):
        if org.startswith('-'):
            sub_org = org.lstrip('-')
            if current_org:
                org_dict.setdefault(current_org, []).append(sub_org)
        else:
            current_org = org
        if current_org not in org_dict:
            org_dict[current_org] = []
    return org_dict


def get_top_level_organisations(
        data: list[dict[str, list[str]] | str]) -> list[str]:
    top_level_organisations: list[str] = []
    for item in data:
        if isinstance(item, dict):
            top_level_organisations.extend(item.keys())
        elif isinstance(item, str):
            top_level_organisations.append(item)
    return top_level_organisations


def get_sub_organisations(
        data: list[dict[str, list[str]] | str]) -> list[str]:
    sub_organisations: set[str] = set()
    for item in data:
        if isinstance(item, dict):
            for sub_orgs in item.values():
                sub_organisations.update(sub_orgs)
    return list(sub_organisations)


@OrgApp.html(model=PersonCollection, template='people.pt', permission=Public)
def view_people(
    self: PersonCollection,
    request: OrgRequest,
    layout: PersonCollectionLayout | None = None
) -> RenderData:

    selected_org = str(request.params.get('organisation', ''))
    selected_sub_org = str(request.params.get('sub_organisation', ''))

    top_orgs = get_top_level_organisations(
        request.app.org.organisation_hierarchy)
    sub_orgs = get_sub_organisations(
            request.app.org.organisation_hierarchy)
    if selected_org:
        index = top_orgs.index(selected_org)
        top_org = request.app.org.organisation_hierarchy[index]
        if isinstance(top_org, dict):
            sub_orgs = top_org[selected_org]

    if selected_sub_org and selected_sub_org not in sub_orgs:
        sub_orgs.append(selected_sub_org)

    people = self.people_by_organisation(selected_org, selected_sub_org)

    class AtoZPeople(AtoZ[Person]):

        def get_title(self, item: Person) -> str:
            return item.title

        def get_items(self) -> list[Person]:
            return people

    return {
        'title': _('People'),
        'count': len(people),
        'people': AtoZPeople(request).get_items_by_letter().items(),
        'layout': layout or PersonCollectionLayout(self, request),
        'organisations_as_dict': organisations_as_dict,
        'organisations': sorted(top_orgs),
        'sub_organisations': sorted(sub_orgs),
        'selected_organisation': selected_org,
        'selected_sub_organisation': selected_sub_org
    }


@OrgApp.html(model=Person, template='person.pt', permission=Public)
def view_person(
    self: Person,
    request: OrgRequest,
    layout: PersonLayout | None = None
) -> RenderData:

    query = request.session.query(Topic)
    query = query.options(undefer(Topic.content))
    org_to_func = person_functions_by_organization(self, query, request)
    return {
        'title': self.title,
        'person': self,
        'layout': layout or PersonLayout(self, request),
        'organization_to_function': org_to_func,
        'organisations_as_dict': organisations_as_dict,
    }


def person_functions_by_organization(
    subject_person: Person,
    topics: Iterable[Topic],
    request: OrgRequest
) -> Iterable[Markup]:
    """ Collects 1:1 mappings of all context-specific functions and
     organizations for a person. Organizations are pages where `subject_person`
     is listed as a person.

     Returns an Iterable of Markup in the form:

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
                and (func := getattr(pers, 'context_specific_function', None))
                is not None
                and getattr(pers, 'display_function_in_person_directory',
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
    request: OrgRequest,
    form: PersonForm,
    layout: PersonCollectionLayout | None = None
) -> RenderData | BaseResponse:

    if form.submitted(request):
        person = self.add(**form.get_useful_data())
        request.success(_('Added a new person'))

        return morepath.redirect(request.link(person))

    layout = layout or PersonCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.include_editor()
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('New person'),
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
    request: OrgRequest,
    form: PersonForm,
    layout: PersonLayout | None = None
) -> RenderData | BaseResponse:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))

        return morepath.redirect(request.link(self))
    else:
        form.process(obj=self)

    layout = layout or PersonLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.include_editor()
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': self.title,
        'form': form
    }


@OrgApp.view(model=Person, request_method='DELETE', permission=Private)
def handle_delete_person(self: Person, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    PersonCollection(request.session).delete(self)


@OrgApp.view(model=Person, name='vcard', permission=Public)
def vcard_export_person(self: Person, request: OrgRequest) -> Response:
    """ Returns the persons vCard. """

    exclude = [*request.app.org.excluded_person_fields(request), 'notes']

    return Response(
        self.vcard(exclude),
        content_type='text/vcard',
        content_disposition='inline; filename=card.vcf'
    )
