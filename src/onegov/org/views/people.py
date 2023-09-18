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
from sqlalchemy import case, null
from sqlalchemy import select, exists, and_
from sqlalchemy.sql.expression import text
from sqlalchemy import any_


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
    # pages = pages.filter(Topic.people is not None).all()
    org_to_func = person_functions_by_organization(self, request)

    return {
        'title': self.title,
        'person': self,
        'layout': layout or PersonLayout(self, request),
        'organization_to_function': org_to_func
    }


def person_functions_by_organization(subject_person, request):
    """ ... """

    organization_to_function = []

    # condition = text('CASE WHEN :attr IS NOT NULL THEN 1 ELSE 0 END').params(
    #     attr=hasattr(subject_person, 'display_function_in_person_directory'))
    #
    # subquery = exists().where(
    #     and_(
    #         condition == 1,
    #         Person.context_specific_function.isnot(None),
    #         )
    # )
    #
    # query = (
    #     request.session.query(Topic)
    #     .select_from(Topic.join(Person, Topic.people == Person.id))
    #     .filter(Topic.people is not None)
    #     .filter(Person.id == subject_person.id)
    #     .filter(getattr(Person, 'context_specific_function', None).isnot(None))
    #     .filter(getattr(Person, 'display_function_in_person_directory', None).isnot(None))
    #     # .add_columns(select([Person.context_specific_function]).where(
    #     # subquery).as_scalar())
    #     .all()
    # )

    # subquery = exists().where(
    #     and_(
    #         Person.id == subject_person.id,
    #         # Person.display_function_in_person_directory == True,
    #         # Person.context_specific_function.isnot(None),
    #     )
    # )
    from sqlalchemy import exists, and_, literal
    query = (
        request.session.query(Topic)
        .filter(Topic.people is not None)
        .filter(
            exists().where(
                and_(
                    Person.id == subject_person.id,
                    Topic.content['people'].has_key("context_specific_function"),
                    Topic.content['people'].has_key("display_function_in_person_directory")
                )
            )
        )


        # .add_columns(select([Person.context_specific_function]).where(
        #     subquery).as_scalar())

        # .filter(
        #     # Person.display_function_in_person_directory == True,
        #     subquery
        # )
        .all()
    )

    for topic in query:
        breakpoint()
        page = Markup('<a href="{0}">{1}</a>').format(
            request.link(topic), topic.title
        )
        func = topic.people.context_specific_function
        organization_to_function.append(
            Markup('<span>{0}: {1}</span>').format(page, func)
        )

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
