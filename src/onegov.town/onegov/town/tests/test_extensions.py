from onegov.core.utils import Bunch
from onegov.form import Form
from onegov.town.models.extensions import (
    PersonLinkExtension, ContactExtension, HiddenFromPublicExtension
)
from uuid import UUID


def test_hidden_from_public_extension():

    class Topic(HiddenFromPublicExtension):
        meta = {}

    class TopicForm(Form):
        pass

    topic = Topic()
    assert not topic.is_hidden_from_public

    form_class = topic.with_content_extensions(TopicForm, request=object())
    form = form_class()

    assert 'is_hidden_from_public' in form._fields
    assert not form.is_hidden_from_public.data

    form.is_hidden_from_public.data = True
    form.populate_obj(topic)

    assert topic.is_hidden_from_public

    form_class = topic.with_content_extensions(TopicForm, request=object())
    form = form_class()

    form.process(obj=topic)

    assert form.is_hidden_from_public.data


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

    form_class = topic.with_content_extensions(TopicForm, request=object())
    form = form_class()

    assert 'people_troy_barnes' in form._fields
    assert 'people_troy_barnes_function' in form._fields
    assert 'people_abed_nadir' in form._fields
    assert 'people_abed_nadir_function' in form._fields

    form.people_troy_barnes.data = True
    form.update_model(topic)

    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', None)
    ]

    form.people_troy_barnes_function.data = 'The Truest Repairman'
    form.update_model(topic)

    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', 'The Truest Repairman')
    ]

    form_class = topic.with_content_extensions(TopicForm, request=object())
    form = form_class()
    form.apply_model(topic)

    assert form.people_troy_barnes.data is True
    assert form.people_troy_barnes_function.data == 'The Truest Repairman'
    assert not form.people_abed_nadir.data
    assert not form.people_abed_nadir_function.data


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

    topic = Topic()
    form_class = topic.with_content_extensions(TopicForm, request=object())
    form = form_class()

    form.people_troy_barnes.data = True
    form.people_britta_perry.data = True
    form.update_model(topic)

    # the people are kept sorted by lastname, firstname by default
    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', None),  # Troy _B_arnes
        ('f0281b558a5f43f6ac81589d79538a87', None)   # Britta _P_erry
    ]

    form.people_annie_edison.data = True
    form.update_model(topic)

    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', None),  # Troy _B_arnes
        ('aa37e9cc40ab402ea70b0d2b4d672de3', None),  # Annie _E_dison
        ('f0281b558a5f43f6ac81589d79538a87', None)   # Britta _P_erry
    ]

    # once the order changes, people are added at the end
    topic.move_person(
        subject='f0281b558a5f43f6ac81589d79538a87',  # Britta
        target='6d120102d90344868eb32614cf3acb1a',   # Troy
        direction='above'
    )

    assert topic.content['people'] == [
        ('f0281b558a5f43f6ac81589d79538a87', None),  # Britta _P_erry
        ('6d120102d90344868eb32614cf3acb1a', None),  # Troy _B_arnes
        ('aa37e9cc40ab402ea70b0d2b4d672de3', None),  # Annie _E_dison
    ]

    topic.move_person(
        subject='6d120102d90344868eb32614cf3acb1a',  # Troy
        target='aa37e9cc40ab402ea70b0d2b4d672de3',   # Annie
        direction='below'
    )

    assert topic.content['people'] == [
        ('f0281b558a5f43f6ac81589d79538a87', None),  # Britta _P_erry
        ('aa37e9cc40ab402ea70b0d2b4d672de3', None),  # Annie _E_dison
        ('6d120102d90344868eb32614cf3acb1a', None),  # Troy _B_arnes
    ]

    form.people_abed_nadir.data = True
    form.update_model(topic)

    assert topic.content['people'] == [
        ('f0281b558a5f43f6ac81589d79538a87', None),  # Britta _P_erry
        ('aa37e9cc40ab402ea70b0d2b4d672de3', None),  # Annie _E_dison
        ('6d120102d90344868eb32614cf3acb1a', None),  # Troy _B_arnes
        ('adad98ff74e2497a9e1dfbba0a6bbe96', None),  # Abed _N_adir
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
    form_class = topic.with_content_extensions(TopicForm, request=object())
    form = form_class()

    form.people_barack_obama.data = True
    form.people_barack_obama_function.data = "President"

    form.people_joe_biden.data = True
    form.people_joe_biden_function.data = "Vice-President"

    form.update_model(topic)

    assert topic.content['people'] == [
        ('aa37e9cc40ab402ea70b0d2b4d672de3', "Vice-President"),
        ('6d120102d90344868eb32614cf3acb1a', "President")
    ]

    topic.move_person(
        subject='6d120102d90344868eb32614cf3acb1a',
        target='aa37e9cc40ab402ea70b0d2b4d672de3',
        direction='above'
    )

    assert topic.content['people'] == [
        ('6d120102d90344868eb32614cf3acb1a', "President"),
        ('aa37e9cc40ab402ea70b0d2b4d672de3', "Vice-President"),
    ]


def test_contact_extension():

    class Topic(ContactExtension):
        content = {}

    class TopicForm(Form):
        pass

    topic = Topic()
    assert topic.contact is None
    assert topic.contact_html is None

    form_class = topic.with_content_extensions(TopicForm, request=object())
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
        '<ul>'
        '<li>Steve Jobs</li>'
        '<li><a href="mailto:steve@apple.com">steve@apple.com</a></li>'
        '<li><a href="https://www.apple.com" rel="nofollow">'
        'https://www.apple.com</a></li>'
        '</ul>'
    )

    form_class = topic.with_content_extensions(TopicForm, request=object())
    form = form_class()

    form.process(obj=topic)

    assert form.contact.data == (
        "Steve Jobs\n"
        "steve@apple.com\n"
        "https://www.apple.com"
    )
