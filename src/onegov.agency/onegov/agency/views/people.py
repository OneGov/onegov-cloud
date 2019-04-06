from collections import namedtuple
from collections import OrderedDict
from itertools import groupby
from morepath import redirect
from onegov.agency import _
from onegov.agency import AgencyApp
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.layouts import ExtendedPersonCollectionLayout
from onegov.agency.layouts import ExtendedPersonLayout
from onegov.agency.models import ExtendedPerson
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.org.elements import Link
from onegov.org.forms import PersonForm
from onegov.org.models import AtoZ
from unidecode import unidecode


def get_person_form_class(model, request):
    if isinstance(model, ExtendedPerson):
        return model.with_content_extensions(PersonForm, request)
    return ExtendedPerson().with_content_extensions(PersonForm, request)


@AgencyApp.html(
    model=ExtendedPersonCollection,
    template='extended_people.pt',
    permission=Public
)
def view_people(self, request):
    request.include('common')
    request.include('chosen')
    request.include('people-select')

    if not request.is_logged_in:
        self.exclude_hidden = True

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
            title='',
            value=request.link(self.for_filter(agency=None)),
            selected=(self.agency is None),
        )
    )

    people = self.batch

    class AtoZPeople(AtoZ):

        def get_title(self, item):
            return item.title

        def get_items(self):
            return people

        def get_items_by_letter(self):
            items_by_letter = OrderedDict()
            for letter, items in groupby(self.get_items(), self.sortkey):
                items_by_letter[unidecode(letter)] = tuple(items)
            return items_by_letter

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
    form=get_person_form_class
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
    form=get_person_form_class
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
