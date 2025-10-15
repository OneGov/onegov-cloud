from __future__ import annotations

import os.path

from collections import defaultdict
from markupsafe import Markup
from onegov.core.orm.abstract import MoveDirection
from onegov.core.utils import Bunch
from onegov.form import Form
from onegov.form.extensions import Extendable
from onegov.org.models import Topic
from onegov.org.models.extensions import (
    PersonLinkExtension, ContactExtension, AccessExtension, HoneyPotExtension,
    SidebarLinksExtension, PeopleShownOnMainPageExtension,
    InlinePhotoAlbumExtension, SidebarContactLinkExtension,
)
from onegov.people import Person
from tempfile import TemporaryDirectory
from tests.shared.utils import create_pdf
from uuid import UUID
from webtest import Upload


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from .conftest import Client, TestOrgApp


def test_disable_extension() -> None:
    class Topic(AccessExtension):
        meta = {}

    class TopicForm(Form):
        pass

    topic = Topic()
    request: Any = Bunch(app=Bunch(**{
        'settings.org.disabled_extensions': [],
        'can_deliver_sms': False
    }))
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class()
    assert 'access' in form._fields

    topic = Topic()
    request = Bunch(app=Bunch(**{
        'settings.org.disabled_extensions': ['AccessExtension'],
        'can_deliver_sms': False
    }))
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class()
    assert 'access' not in form._fields


def test_access_extension() -> None:
    class Topic(AccessExtension):
        meta = {}

    class TopicForm(Form):
        pass

    topic = Topic()
    assert topic.access == 'public'

    request: Any = Bunch(app=Bunch(**{
        'settings.org.disabled_extensions': [],
        'can_deliver_sms': False
    }))
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class()

    assert 'access' in form
    assert form['access'].data == 'public'
    assert {'mtan', 'secret_mtan'}.isdisjoint(
        value for value, _ in form['access'].choices)  # type: ignore[attr-defined]

    form['access'].data = 'private'
    form.populate_obj(topic)

    assert topic.access == 'private'

    request = Bunch(app=Bunch(**{
        'settings.org.disabled_extensions': [],
        'can_deliver_sms': True
    }))
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class()
    assert {'mtan', 'secret_mtan'}.issubset(
        value for value, _ in form['access'].choices)  # type: ignore[attr-defined]

    form.process(obj=topic)

    assert form['access'].data == 'private'

    form['access'].data = 'member'
    form.populate_obj(topic)

    assert topic.access == 'member'


# FIXME: There is a lot of mocking going on, we're probably better off
#        actually using a real model with a database, instead of mocking
#        that part.
def setup_person_link_extension(people: Any) -> tuple[Any, Any]:
    class Topic(PersonLinkExtension):
        content = {}

        def get_selectable_people(self, request: object) -> Any:
            return people

        @property
        def people(self) -> list[Any] | None:
            if not (people_items := self.content.get('people')):
                return None

            people = dict(people_items)
            result = []
            for person in self.get_selectable_people(None):
                if item := people.get(person.id.hex):
                    result.append(Bunch(
                        id=person.id,
                        title=person.title,
                        person=person.id.hex,
                        context_specific_function=item[0],
                        display_function_in_person_directory=item[1]
                    ))
            return result

    topic = Topic()
    assert topic.people is None

    request = Bunch(**{
        'locale': 'de',
        'translate': lambda text: text,
        'get_translate': lambda *a, **kw: None,
        'get_form': lambda form, *a, **kw: form,
        'app.settings.org.disabled_extensions': [],
        'template_loader.macros': defaultdict(Markup),
    })

    return topic, request

def test_person_link_extension() -> None:
    class TopicForm(Form):
        pass

    topic, request = setup_person_link_extension([
        Bunch(
            id=UUID('6d120102-d903-4486-8eb3-2614cf3acb1a'),
            title='Troy Barnes'
        ),
        Bunch(
            id=UUID('adad98ff-74e2-497a-9e1d-fbba0a6bbe96'),
            title='Abed Nadir'
        )
    ])
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class(obj=topic)

    assert 'people' in form
    field = form.people
    assert len(field) == 1
    assert field[0].form.person.data is None
    assert field[0].form.context_specific_function.data is None
    assert field[0].form.display_function_in_person_directory.data is False

    field[0].form.person.data = '6d120102d90344868eb32614cf3acb1a'
    form.populate_obj(topic)

    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', (None, False))
    ]

    field[0].form.context_specific_function.data = 'The Truest Repairman'

    form.populate_obj(topic)

    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', ('The Truest Repairman', False))
    ]

    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class(obj=topic)

    field = form.people
    assert len(field) == 2
    assert field[0].form.person.data == '6d120102d90344868eb32614cf3acb1a'
    assert field[0].form.context_specific_function.data == (
        'The Truest Repairman')

    assert field[1].form.person.data is None
    assert field[1].form.context_specific_function.data is None
    assert field[1].form.display_function_in_person_directory.data is False


def test_person_link_extension_order() -> None:

    class TopicForm(Form):
        pass

    topic, request = setup_person_link_extension([
        Bunch(
            id=UUID('6d120102-d903-4486-8eb3-2614cf3acb1a'),
            title='Troy Barnes'
        ),
        Bunch(
            id=UUID('aa37e9cc-40ab-402e-a70b-0d2b4d672de3'),
            title='Annie Edison'
        ),
        Bunch(
            id=UUID('adad98ff-74e2-497a-9e1d-fbba0a6bbe96'),
            title='Abed Nadir'
        ),
        Bunch(
            id=UUID('f0281b55-8a5f43f6-ac81-589d79538a87'),
            title='Britta Perry'
        )
    ])
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class(obj=topic)

    field = form.people
    field.append_entry()
    assert len(field) == 2
    field[0].form.person.data = '6d120102d90344868eb32614cf3acb1a'
    field[1].form.person.data = 'f0281b558a5f43f6ac81589d79538a87'
    form.populate_obj(topic)

    # the people are kept sorted by lastname, firstname by default
    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', (None, False)),  # Troy _B_arnes
        ('f0281b558a5f43f6ac81589d79538a87', (None, False))  # Britta _P_erry
    ]

    field.append_entry()
    field[2].form.person.data = 'aa37e9cc40ab402ea70b0d2b4d672de3'
    form.populate_obj(topic)

    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', (None, False)),  # Troy _B_arnes
        ('aa37e9cc40ab402ea70b0d2b4d672de3', (None, False)),  # Annie _E_dison
        ('f0281b558a5f43f6ac81589d79538a87', (None, False))  # Britta _P_erry
    ]

    # once the order changes, people are added at the end
    topic.move_person(
        subject='f0281b558a5f43f6ac81589d79538a87',  # Britta
        target='6d120102d90344868eb32614cf3acb1a',  # Troy
        direction=MoveDirection.above
    )

    assert topic.content['people'] == [
        ('f0281b558a5f43f6ac81589d79538a87', (None, False)),  # Britta _P_erry
        ('6d120102d90344868eb32614cf3acb1a', (None, False)),  # Troy _B_arnes
        ('aa37e9cc40ab402ea70b0d2b4d672de3', (None, False)),  # Annie _E_dison
    ]

    topic.move_person(
        subject='6d120102d90344868eb32614cf3acb1a',  # Troy
        target='aa37e9cc40ab402ea70b0d2b4d672de3',  # Annie
        direction=MoveDirection.below
    )

    assert topic.content['people'] == [
        ('f0281b558a5f43f6ac81589d79538a87', (None, False)),  # Britta _P_erry
        ('aa37e9cc40ab402ea70b0d2b4d672de3', (None, False)),  # Annie _E_dison
        ('6d120102d90344868eb32614cf3acb1a', (None, False)),  # Troy _B_arnes
    ]

    # plug in the current order into the field, since move_person
    # does not update the field
    field[0].form.person.data = 'f0281b558a5f43f6ac81589d79538a87'
    field[1].form.person.data = 'aa37e9cc40ab402ea70b0d2b4d672de3'
    field[2].form.person.data = '6d120102d90344868eb32614cf3acb1a'

    # append new selection
    field.append_entry()
    field[3].form.person.data = 'adad98ff74e2497a9e1dfbba0a6bbe96'
    form.populate_obj(topic)

    assert topic.content['people'] == [
        ('f0281b558a5f43f6ac81589d79538a87', (None, False)),  # Britta _P_erry
        ('aa37e9cc40ab402ea70b0d2b4d672de3', (None, False)),  # Annie _E_dison
        ('6d120102d90344868eb32614cf3acb1a', (None, False)),  # Troy _B_arnes
        ('adad98ff74e2497a9e1dfbba0a6bbe96', (None, False)),  # Abed _N_adir
    ]

    # remove a person
    field[1].form.person.data = ''
    form.populate_obj(topic)

    assert topic.content['people'] == [
        ('f0281b558a5f43f6ac81589d79538a87', (None, False)),  # Britta _P_erry
        ('6d120102d90344868eb32614cf3acb1a', (None, False)),  # Troy _B_arnes
        ('adad98ff74e2497a9e1dfbba0a6bbe96', (None, False)),  # Abed _N_adir
    ]


def test_person_link_move_function() -> None:

    class TopicForm(Form):
        pass

    topic, request = setup_person_link_extension([
        Bunch(
            id=UUID('aa37e9cc-40ab-402e-a70b-0d2b4d672de3'),
            title="Joe Biden"
        ),
        Bunch(
            id=UUID('6d120102-d903-4486-8eb3-2614cf3acb1a'),
            title="Barack Obama"
        ),
    ])
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class(obj=topic)

    field = form.people
    field.append_entry()
    assert len(field) == 2
    field[0].form.person.data = '6d120102d90344868eb32614cf3acb1a'
    field[0].form.context_specific_function.data = 'President'

    field[1].form.person.data = 'aa37e9cc40ab402ea70b0d2b4d672de3'
    field[1].form.context_specific_function.data = 'Vice-President'

    form.populate_obj(topic)

    assert topic.content['people'] == [
        ('aa37e9cc40ab402ea70b0d2b4d672de3', ('Vice-President', False)),
        ('6d120102d90344868eb32614cf3acb1a', ('President', False))
    ]

    topic.move_person(
        subject='6d120102d90344868eb32614cf3acb1a',
        target='aa37e9cc40ab402ea70b0d2b4d672de3',
        direction=MoveDirection.above
    )

    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', ('President', False)),
        ('aa37e9cc40ab402ea70b0d2b4d672de3', ('Vice-President', False)),
    ]


def test_contact_extension(org_app: TestOrgApp) -> None:

    class TopicForm(Form):
        pass

    topic = Topic(name='test')
    assert topic.contact is None
    assert topic.contact_html is None

    request: Any = Bunch(app=org_app, session=org_app.session())
    form_class = topic.with_content_extensions(
        TopicForm,
        request=request,
        extensions=(ContactExtension,)
    )
    form = form_class()

    assert 'contact' in form

    form['contact'].data = (
        "Steve Jobs\n"
        "steve@apple.com\n"
        "https://www.apple.com"
    )

    form.populate_obj(topic)

    assert topic.contact == (
        "Steve Jobs\n"
        "steve@apple.com\n"
        "https://www.apple.com"
    )

    assert topic.contact_html == (
        '<p><span class="title">'
        'Steve Jobs</span></p>'
        '<p><a href="mailto:steve@apple.com">steve@apple.com</a><br>'
        '<a href="https://www.apple.com" rel="nofollow">'
        'https://www.apple.com</a>'
        '</p>'
    )

    form_class = topic.with_content_extensions(
        TopicForm,
        request=request,
        extensions=(ContactExtension,)
    )
    form = form_class()

    form.process(obj=topic)

    assert form['contact'].data == (
        "Steve Jobs\n"
        "steve@apple.com\n"
        "https://www.apple.com"
    )


def test_contact_extension_with_top_level_domain_agency(
    org_app: TestOrgApp
) -> None:

    class TopicForm(Form):
        pass

    topic = Topic(name='test')

    assert topic.contact is None
    assert topic.contact_html is None

    request: Any = Bunch(app=org_app, session=org_app.session())
    form_class = topic.with_content_extensions(
        TopicForm,
        request=request,
        extensions=(ContactExtension,)
    )
    form = form_class()
    form.request = request

    assert 'contact' in form

    form['contact'].data = (
        "longdomain GmbH\n"
        "hello@website.agency\n"
        "https://custom.longdomain"
    )

    form.populate_obj(topic)

    assert topic.contact == (
        "longdomain GmbH\n"
        "hello@website.agency\n"
        "https://custom.longdomain"
    )
    # undo mypy narrowing
    topic = topic
    html = topic.contact_html
    assert html is not None
    assert '<a href="mailto:hello@website.ag"' not in html


def test_people_shown_on_main_page_extension(
    client: Client[TestOrgApp]
) -> None:

    client.login_admin()

    class Topic(PeopleShownOnMainPageExtension):
        content = {}

    class TopicForm(Form):
        pass

    people = client.get('/people')
    assert "Keine Personen" in people

    new_person = people.click('Person', href='new')
    new_person.form['first_name'] = 'Fritzli'
    new_person.form['last_name'] = 'Müller'
    new_person.form['function'] = 'Dorf-Clown'
    new_person.form.submit().follow()

    fritzli = (
        client.app.session().query(Person)
        .filter(Person.last_name == 'Müller')
        .one()
    )

    # add person to side panel
    page = client.get('/topics/themen')
    page = page.click('Bearbeiten')
    page.form['show_people_on_main_page'] = False
    page.form['people-0-person'] = fritzli.id.hex
    # NOTE: defaults require JavaScript, so in order to test those
    #       we would need to change this to a browser-test, for now
    #       we set what would be the default value for this person
    page.form['people-0-context_specific_function'] = 'Dorf-Clown'
    page.form['people-0-display_function_in_person_directory'] = True
    page = page.form.submit().follow()
    assert 'Fritzli' in page
    assert 'Müller' in page
    assert 'Dorf-Clown' in page

    # show person on main page
    page = client.get('/topics/themen')
    page = page.click('Bearbeiten')
    page.form['show_people_on_main_page'] = True
    page.form['people-0-context_specific_function'] = 'Super-Clown'
    page = page.form.submit().follow()
    assert 'Fritzli' in page
    assert 'Müller' in page
    assert 'Super-Clown' in page


def test_honeypot_extension() -> None:
    class Submission(Extendable, HoneyPotExtension):
        meta = {}

    class EditSubmissionForm(Form):
        pass

    class SubmissionForm(Form):
        pass

    # Edit submission
    # ... default
    submission = Submission()
    assert submission.honeypot is True

    request: Any = Bunch(**{'app.settings.org.disabled_extensions': []})
    form_class = submission.with_content_extensions(
        EditSubmissionForm, request=request
    )
    form = form_class()
    assert 'honeypot' in form
    assert form['honeypot'].data is True

    # ... change
    form['honeypot'].data = False
    form.populate_obj(submission)
    # undo mypy narrowing
    submission = submission
    assert submission.honeypot is False

    # ... apply
    form_class = submission.with_content_extensions(
        EditSubmissionForm, request=request
    )
    form = form_class()
    form.process(obj=submission)
    assert form['honeypot'].data is False

    # Extend submission
    # ... add
    submission.honeypot = True
    form_class2 = submission.extend_form_class(
        SubmissionForm, extensions=['honeypot']
    )
    form2 = form_class2()
    form2.model = submission
    form2.on_request()  # type: ignore[attr-defined]
    assert 'duplicate_of' in form

    # ... don't add
    submission.honeypot = False
    form2 = form_class2()
    form2.model = submission
    form2.on_request()  # type: ignore[attr-defined]
    assert 'duplicate_of' not in form2


def test_general_file_link_extension(client: Client[TestOrgApp]) -> None:
    client.login_admin()

    with TemporaryDirectory() as td:

        root_page = client.get('/topics/themen')
        new_page = root_page.click('Thema')

        assert 'files' in new_page.form.fields

        new_page.form['title'] = "Living in Govikon is Swell"
        new_page.form['text'] = (
            "## Living in Govikon is Really Great\n"
            "*Experts say it's the fact that Govikon does not really exist.*"
        )
        filename = os.path.join(td, 'simple.pdf')
        create_pdf(filename)
        new_page.form.set('files', [Upload(filename)], -1)
        new_page.form['show_file_links_in_sidebar'] = True
        page = new_page.form.submit().follow()

        assert 'Living in Govikon is Swell' in page
        assert 'Dokumente' in page
        assert 'simple.pdf' in page

        edit_page = page.click('Bearbeiten')
        edit_page.form['show_file_links_in_sidebar'] = False
        page = edit_page.form.submit().follow()

        assert 'Living in Govikon is Swell' in page
        assert 'Dokumente' not in page
        assert 'simple.pdf' not in page


def test_general_file_link_extension_deduplication(
    client: Client[TestOrgApp]
) -> None:
    client.login_admin()

    with TemporaryDirectory() as td:

        root_page = client.get('/topics/themen')
        new_page = root_page.click('Thema')

        assert 'files' in new_page.form.fields

        new_page.form['title'] = "Living in Govikon is Swell"
        new_page.form['text'] = (
            "## Living in Govikon is Really Great\n"
            "*Experts say it's the fact that Govikon does not really exist.*"
        )
        filename = os.path.join(td, 'simple.pdf')
        create_pdf(filename)
        new_page.form.set('files', [
            Upload(filename),
            Upload(filename)
        ], -1)
        new_page.form['show_file_links_in_sidebar'] = True
        page = new_page.form.submit().follow()

        assert 'Living in Govikon is Swell' in page
        assert 'Dokumente' in page
        assert 'simple.pdf' in page

        session = client.app.session()
        topic = session.query(Topic).filter(
            Topic.title == "Living in Govikon is Swell").one()
        assert len(topic.files) == 1

        pages_id = topic.id
        file_id = topic.files[0].id

        count, = session.execute("""
            SELECT COUNT(*)
              FROM files_for_pages_files
             WHERE pages_id = :pages_id
               AND file_id = :file_id
        """, {'pages_id': pages_id, 'file_id': file_id}).fetchone()
        assert count == 1


def test_sidebar_links_extension(session: Session) -> None:

    class Topic(SidebarLinksExtension):
        sidepanel_links = []

    class TopicForm(Form):
        pass

    topic = Topic()
    assert topic.sidepanel_links == []

    request: Any = Bunch(**{
        'app.settings.org.disabled_extensions': [],
        'session': session
    })
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class(meta={'request': request})

    assert 'sidepanel_links' in form
    assert form['sidepanel_links'].data is None

    form['sidepanel_links'].data = '''
            {"labels":
                {"text": "Text",
                "link": "URL",
                "add": "Hinzuf\\u00fcgen",
                "remove": "Entfernen"},
            "values": [
                {"text": "Govikon School",
                "link": "https://www.govikon-school.ch", "error": ""},
                {"text": "Castle Govikon",
                "link": "https://www.govikon-castle.ch", "error": ""}
            ]
            }
        '''

    form.populate_obj(topic)

    assert topic.sidepanel_links == [
        ('Govikon School', 'https://www.govikon-school.ch'),
        ('Castle Govikon', 'https://www.govikon-castle.ch')]


def test_sidebar_contact_extension(session: Session) -> None:
    class Topic(SidebarContactLinkExtension):
        sidepanel_contact = []

    class TopicForm(Form):
        pass

    topic = Topic()
    assert topic.sidepanel_contact == []

    request: Any = Bunch(**{
        'app.settings.org.disabled_extensions': [],
        'session': session
    })

    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class(meta={'request': request})

    assert 'sidepanel_contact' in form
    assert form['sidepanel_contact'].data is None

    form['sidepanel_contact'].data = '''
    {"labels":
        {"text": "Contact Text",
        "link": "Contact URL",
        "add": "Add",
        "remove": "Remove"},
    "values": [
        {"text": "Town Hall",
        "link": "https://www.townhall.gov", "error": ""},
        {"text": "Public Services",
        "link": "https://www.public-services.gov", "error": ""}
    ]
    }
    '''

    form.populate_obj(topic)

    assert topic.sidepanel_contact == [
        ('Town Hall', 'https://www.townhall.gov'),
        ('Public Services', 'https://www.public-services.gov')
    ]


def test_inline_photo_album_extension(session: Session) -> None:
    class Topic(InlinePhotoAlbumExtension):
        meta = {}
        content = {}

    class TopicForm(Form):
        pass

    topic = Topic()
    assert topic.photo_album_id is None

    request: Any = Bunch(
        session=session,
        app=Bunch(**{'settings.org.disabled_extensions': []}),
        translate=lambda text: text
    )

    form_class = topic.with_content_extensions(TopicForm, request=request)
    assert form_class is TopicForm  # No albums = no form extension
