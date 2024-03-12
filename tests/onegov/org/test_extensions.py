import os.path
from tempfile import TemporaryDirectory

import pytest

from uuid import UUID
from depot.manager import DepotManager
from io import BytesIO

from onegov.core.utils import Bunch
from onegov.form import Form
from onegov.form.extensions import Extendable
from onegov.org.models.extensions import (
    PersonLinkExtension, ContactExtension, AccessExtension, HoneyPotExtension,
    SidebarLinksExtension, GeneralFileLinkExtension,
    PeopleShownOnMainPageExtension,
)
from onegov.people import Person
from tests.shared.utils import create_pdf


def test_disable_extension():
    class Topic(AccessExtension):
        meta = {}

    class TopicForm(Form):
        pass

    topic = Topic()
    request = Bunch(app=Bunch(**{
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


def test_access_extension():
    class Topic(AccessExtension):
        meta = {}

    class TopicForm(Form):
        pass

    topic = Topic()
    assert topic.access == 'public'

    request = Bunch(app=Bunch(**{
        'settings.org.disabled_extensions': [],
        'can_deliver_sms': False
    }))
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class()

    assert 'access' in form._fields
    assert form.access.data == 'public'
    assert {'mtan', 'secret_mtan'}.isdisjoint(
        value for value, _ in form.access.choices)

    form.access.data = 'private'
    form.populate_obj(topic)

    assert topic.access == 'private'

    request = Bunch(app=Bunch(**{
        'settings.org.disabled_extensions': [],
        'can_deliver_sms': True
    }))
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class()
    assert {'mtan', 'secret_mtan'}.issubset(
        value for value, _ in form.access.choices)

    form.process(obj=topic)

    assert form.access.data == 'private'

    form.access.data = 'member'
    form.populate_obj(topic)

    assert topic.access == 'member'


def test_person_link_extension():
    class Topic(PersonLinkExtension):
        content = {}

        def get_selectable_people(self, request):
            return [
                Bunch(
                    id=UUID('6d120102-d903-4486-8eb3-2614cf3acb1a'),
                    title='Troy Barnes'
                ),
                Bunch(
                    id=UUID('adad98ff-74e2-497a-9e1d-fbba0a6bbe96'),
                    title='Abed Nadir'
                )
            ]

    class TopicForm(Form):
        pass

    topic = Topic()
    assert topic.people is None

    request = Bunch(**{
        'translate': lambda text: text,
        'app.settings.org.disabled_extensions': []
    })
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class()

    assert 'people_6d120102d90344868eb32614cf3acb1a' in form._fields
    assert 'people_6d120102d90344868eb32614cf3acb1a_function' in form._fields
    assert 'people_adad98ff74e2497a9e1dfbba0a6bbe96' in form._fields
    assert 'people_adad98ff74e2497a9e1dfbba0a6bbe96_function' in form._fields

    form.people_6d120102d90344868eb32614cf3acb1a.data = True
    form.update_model(topic)

    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', (None, False))
    ]

    form.people_6d120102d90344868eb32614cf3acb1a_function.data \
        = 'The Truest Repairman'

    form.update_model(topic)

    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', ('The Truest Repairman', False))
    ]

    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class()
    form.apply_model(topic)

    assert form.people_6d120102d90344868eb32614cf3acb1a.data is True
    assert form.people_6d120102d90344868eb32614cf3acb1a_function.data \
           == 'The Truest Repairman'

    assert form.people_6d120102d90344868eb32614cf3acb1a_is_visible_function \
               .data == False
    assert not form.people_adad98ff74e2497a9e1dfbba0a6bbe96.data
    assert not form.people_adad98ff74e2497a9e1dfbba0a6bbe96_function.data


def test_person_link_extension_duplicate_name():
    class Topic(PersonLinkExtension):
        content = {}

        def get_selectable_people(self, request):
            return [
                Bunch(
                    id=UUID('6d120102-d903-4486-8eb3-2614cf3acb1a'),
                    title='Foo'
                ),
                Bunch(
                    id=UUID('adad98ff-74e2-497a-9e1d-fbba0a6bbe96'),
                    title='Foo'
                )
            ]

    class TopicForm(Form):
        pass

    topic = Topic()
    assert topic.people is None

    request = Bunch(**{
        'translate': lambda text: text,
        'app.settings.org.disabled_extensions': []
    })
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class()

    assert 'people_6d120102d90344868eb32614cf3acb1a' in form._fields
    assert 'people_6d120102d90344868eb32614cf3acb1a_function' in form._fields
    assert 'people_adad98ff74e2497a9e1dfbba0a6bbe96' in form._fields
    assert 'people_adad98ff74e2497a9e1dfbba0a6bbe96_function' in form._fields


def test_person_link_extension_order():
    class Topic(PersonLinkExtension):
        content = {}

        def get_selectable_people(self, request):
            return [
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
            ]

    class TopicForm(Form):
        pass

    request = Bunch(**{
        'translate': lambda text: text,
        'app.settings.org.disabled_extensions': []
    })
    topic = Topic()
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class()

    form.people_6d120102d90344868eb32614cf3acb1a.data = True
    form.people_f0281b558a5f43f6ac81589d79538a87.data = True
    form.update_model(topic)

    # the people are kept sorted by lastname, firstname by default
    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', (None, False)),  # Troy _B_arnes
        ('f0281b558a5f43f6ac81589d79538a87', (None, False))  # Britta _P_erry
    ]

    form.people_aa37e9cc40ab402ea70b0d2b4d672de3.data = True
    form.update_model(topic)

    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', (None, False)),  # Troy _B_arnes
        ('aa37e9cc40ab402ea70b0d2b4d672de3', (None, False)),  # Annie _E_dison
        ('f0281b558a5f43f6ac81589d79538a87', (None, False))  # Britta _P_erry
    ]

    # once the order changes, people are added at the end
    topic.move_person(
        subject='f0281b558a5f43f6ac81589d79538a87',  # Britta
        target='6d120102d90344868eb32614cf3acb1a',  # Troy
        direction='above'
    )

    assert topic.content['people'] == [
        ('f0281b558a5f43f6ac81589d79538a87', (None, False)),  # Britta _P_erry
        ('6d120102d90344868eb32614cf3acb1a', (None, False)),  # Troy _B_arnes
        ('aa37e9cc40ab402ea70b0d2b4d672de3', (None, False)),  # Annie _E_dison
    ]

    topic.move_person(
        subject='6d120102d90344868eb32614cf3acb1a',  # Troy
        target='aa37e9cc40ab402ea70b0d2b4d672de3',  # Annie
        direction='below'
    )

    assert topic.content['people'] == [
        ('f0281b558a5f43f6ac81589d79538a87', (None, False)),  # Britta _P_erry
        ('aa37e9cc40ab402ea70b0d2b4d672de3', (None, False)),  # Annie _E_dison
        ('6d120102d90344868eb32614cf3acb1a', (None, False)),  # Troy _B_arnes
    ]

    form.people_adad98ff74e2497a9e1dfbba0a6bbe96.data = True
    form.update_model(topic)

    assert topic.content['people'] == [
        ('f0281b558a5f43f6ac81589d79538a87', (None, False)),  # Britta _P_erry
        ('aa37e9cc40ab402ea70b0d2b4d672de3', (None, False)),  # Annie _E_dison
        ('6d120102d90344868eb32614cf3acb1a', (None, False)),  # Troy _B_arnes
        ('adad98ff74e2497a9e1dfbba0a6bbe96', (None, False)),  # Abed _N_adir
    ]


def test_person_link_move_function():
    class Topic(PersonLinkExtension):
        content = {}

        def get_selectable_people(self, request):
            return [
                Bunch(
                    id=UUID('aa37e9cc-40ab-402e-a70b-0d2b4d672de3'),
                    title="Joe Biden"
                ),
                Bunch(
                    id=UUID('6d120102-d903-4486-8eb3-2614cf3acb1a'),
                    title="Barack Obama"
                ),
            ]

    class TopicForm(Form):
        pass

    topic = Topic()
    request = Bunch(**{
        'translate': lambda text: text,
        'app.settings.org.disabled_extensions': []
    })
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class()

    form.people_6d120102d90344868eb32614cf3acb1a.data = True
    form.people_6d120102d90344868eb32614cf3acb1a_function.data = "President"

    form.people_aa37e9cc40ab402ea70b0d2b4d672de3.data = True
    form.people_aa37e9cc40ab402ea70b0d2b4d672de3_function.data = \
        "Vice-President"

    form.update_model(topic)

    assert topic.content['people'] == [
        ('aa37e9cc40ab402ea70b0d2b4d672de3', ("Vice-President", False)),
        ('6d120102d90344868eb32614cf3acb1a', ("President", False))
    ]

    topic.move_person(
        subject='6d120102d90344868eb32614cf3acb1a',
        target='aa37e9cc40ab402ea70b0d2b4d672de3',
        direction='above'
    )

    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', ("President", False)),
        ('aa37e9cc40ab402ea70b0d2b4d672de3', ("Vice-President", False)),
    ]


def test_contact_extension():
    class Topic(ContactExtension):
        content = {}

    class TopicForm(Form):
        pass

    topic = Topic()
    assert topic.contact is None
    assert topic.contact_html is None

    request = Bunch(**{'app.settings.org.disabled_extensions': []})
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class()

    assert 'contact' in form._fields

    form.contact.data = (
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

    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class()

    form.process(obj=topic)

    assert form.contact.data == (
        "Steve Jobs\n"
        "steve@apple.com\n"
        "https://www.apple.com"
    )


def test_contact_extension_with_top_level_domain_agency():
    class Topic(ContactExtension):
        content = {}

    class TopicForm(Form):
        pass

    topic = Topic()

    assert topic.contact is None
    assert topic.contact_html is None

    request = Bunch(**{'app.settings.org.disabled_extensions': []})
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class()

    assert 'contact' in form._fields

    form.contact.data = (
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
    d = topic.contact_html
    assert '<a href="mailto:hello@website.ag"' not in d


def test_people_shown_on_main_page_extension(client):
    client.login_admin()

    class Topic(PeopleShownOnMainPageExtension):
        content = {}

    class TopicForm(Form):
        pass

    people = client.get('/people')
    assert "keine Personen" in people

    new_person = people.click('Person', href='new')
    new_person.form['first_name'] = 'Fritzli'
    new_person.form['last_name'] = 'Müller'
    new_person.form['function'] = 'Dorf-Clown'
    new_person.form.submit().follow()

    fritzli = client.app.session().query(Person) \
        .filter(Person.last_name == 'Müller') \
        .one()

    # add person to side panel
    page = client.get('/topics/themen')
    page = page.click('Bearbeiten')
    page.form['show_people_on_main_page'] = False
    page.form['people_' + fritzli.id.hex] = True
    page = page.form.submit().follow()
    assert 'Fritzli' in page
    assert 'Müller' in page
    assert 'Dorf-Clown' in page

    # show person on main page
    page = client.get('/topics/themen')
    page = page.click('Bearbeiten')
    page.form['show_people_on_main_page'] = True
    page.form['people_' + fritzli.id.hex + '_function'] = 'Super-Clown'
    page = page.form.submit().follow()
    assert 'Fritzli' in page
    assert 'Müller' in page
    assert 'Super-Clown' in page


def test_honeypot_extension():
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

    request = Bunch(**{'app.settings.org.disabled_extensions': []})
    form_class = submission.with_content_extensions(
        EditSubmissionForm, request=request
    )
    form = form_class()
    assert 'honeypot' in form._fields
    assert form.honeypot.data is True

    # ... change
    form.honeypot.data = False
    form.populate_obj(submission)
    assert submission.honeypot is False

    # ... apply
    form_class = submission.with_content_extensions(
        EditSubmissionForm, request=request
    )
    form = form_class()
    form.process(obj=submission)
    assert form.honeypot.data is False

    # Extend submission
    # ... add
    submission.honeypot = True
    form_class = submission.extend_form_class(
        SubmissionForm, extensions=['honeypot']
    )
    form = form_class()
    form.model = submission
    form.on_request()
    assert 'duplicate_of' in form._fields

    # ... don't add
    submission.honeypot = False
    form = form_class()
    form.model = submission
    form.on_request()
    assert 'duplicate_of' not in form._fields


@pytest.fixture(scope='function')
def depot(temporary_directory):
    DepotManager.configure('default', {
        'depot.backend': 'depot.io.local.LocalFileStorage',
        'depot.storage_path': temporary_directory
    })

    yield DepotManager.get()

    DepotManager._clear()


def test_general_file_link_extension(depot, session):
    class Topic(GeneralFileLinkExtension):
        files = []

    class TopicForm(Form):
        pass

    topic = Topic()
    assert topic.files == []

    request = Bunch(**{
        'app.settings.org.disabled_extensions': [],
        'session': session
    })
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class(meta={'request': request})

    assert 'files' in form._fields
    assert form.files.data == []

    form.files.append_entry()
    form.files[0].file = BytesIO(b'hello world')
    form.files[0].filename = 'test.txt'
    form.files[0].action = 'replace'
    form.populate_obj(topic)

    assert len(topic.files) == 1
    assert topic.files[0].name == 'test.txt'

    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class(meta={'request': request})

    form.process(obj=topic)

    assert form.files.data == [{
        'filename': 'test.txt',
        'size': 11,
        'mimetype': 'text/plain'
    }]
    form.files[0].action = 'delete'

    form.populate_obj(topic)

    assert topic.files == []


def test_show_file_links_in_sidebar(client):
    client.login_admin()

    class Topic():
        files = []

    class TopicForm(Form):
        pass

    with TemporaryDirectory() as td:
        topic = Topic()
        assert topic.files == []

        root_page = client.get('/topics/themen')
        new_page = root_page.click('Thema')

        new_page.form['title'] = "Living in Govikon is Swell"
        new_page.form['text'] = (
            "## Living in Govikon is Really Great\n"
            "*Experts say it's the fact that Govikon does not really exist.*"
        )
        filename = os.path.join(td, 'simple.pdf')
        pdf = create_pdf(filename)
        new_page.form.fields['files'][-1].value = [filename]
        new_page.files = pdf
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


def test_sidebar_links_extension(session):

    class Topic(SidebarLinksExtension):
        sidepanel_links = []

    class TopicForm(Form):
        pass

    topic = Topic()
    assert topic.sidepanel_links == []

    request = Bunch(**{
        'app.settings.org.disabled_extensions': [],
        'session': session
    })
    form_class = topic.with_content_extensions(TopicForm, request=request)
    form = form_class(meta={'request': request})

    assert 'sidepanel_links' in form._fields
    assert form.sidepanel_links.data == None

    form.sidepanel_links.data = '''
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
