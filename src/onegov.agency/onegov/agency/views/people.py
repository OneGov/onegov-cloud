from collections import namedtuple
from morepath import redirect
from onegov.agency import _
from onegov.agency import AgencyApp
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.forms import ExtendedPersonForm
from onegov.agency.models import ExtendedPerson
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.org.elements import Link
from onegov.agency.layouts import ExtendedPersonCollectionLayout
from onegov.agency.layouts import ExtendedPersonLayout
from onegov.org.models import AtoZ


@AgencyApp.html(
    model=ExtendedPersonCollection,
    template='people.pt',
    permission=Public
)
def view_people(self, request):
    request.include('common')

    letters = [
        Link(
            text=letter.upper(),
            url=request.link(
                self.for_filter(
                    letter=letter if (letter != self.letter) else None
                )
            ),
            active=(letter == self.letter),
        ) for letter in self.used_letters
    ]

    Option = namedtuple('Option', ['title', 'value', 'selected'])
    agencies = [
        Option(
            title=agency,
            value=request.link(self.for_filter(agency=agency)),
            selected=(agency == self.agency),
        ) for agency in self.used_agencies
    ]
    agencies.insert(
        0,
        Option(
            title='-',
            value=request.link(self.for_filter(agency=None)),
            selected=(self.agency is None),
        )
    )

    people = self.batch

    class AtoZPeople(AtoZ):

        def get_title(self, item):
            return item.title

        def get_items(self):
            # todo: exclude invisible
            return people

    people = AtoZPeople(request).get_items_by_letter()

    return {
        'title': _("People"),
        'layout': ExtendedPersonCollectionLayout(self, request),
        'letters': letters,
        'agencies': agencies,
        'people': people.items()
    }


@AgencyApp.html(
    model=ExtendedPerson,
    template='person.pt',
    permission=Public
)
def view_person(self, request):

    return {
        'title': self.title,
        'person': self,
        'layout': ExtendedPersonLayout(self, request)
    }


@AgencyApp.form(
    model=ExtendedPersonCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=ExtendedPersonForm
)
def add_person(self, request, form):

    if form.submitted(request):
        person = self.add(**form.get_useful_data())
        request.success(_("Added a new person"))

        return redirect(request.link(person))

    layout = ExtendedPersonCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _("New person"),
        'form': form
    }


@AgencyApp.form(
    model=ExtendedPerson,
    name='edit',
    template='form.pt',
    permission=Private,
    form=ExtendedPersonForm
)
def edit_person(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))

        return redirect(request.link(self))
    else:
        form.process(obj=self)

    layout = ExtendedPersonLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': self.title,
        'form': form
    }
