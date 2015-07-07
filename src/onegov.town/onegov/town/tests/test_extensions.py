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

        def update_model(self, model):
            pass

        def apply_model(self, model):
            pass

    topic = Topic()
    assert not topic.is_hidden_from_public

    form_class = topic.with_content_extensions(TopicForm, request=object())
    form = form_class()

    assert 'is_hidden_from_public' in form._fields
    assert not form.is_hidden_from_public.data

    form.is_hidden_from_public.data = True
    form.update_model(topic)

    assert topic.is_hidden_from_public

    form_class = topic.with_content_extensions(TopicForm, request=object())
    form = form_class()

    form.apply_model(topic)

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

        def update_model(self, model):
            pass

        def apply_model(self, model):
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


def test_contact_extension():

    class Topic(ContactExtension):
        content = {}

    class TopicForm(Form):

        def update_model(self, model):
            pass

        def apply_model(self, model):
            pass

    topic = Topic()
    assert topic.contact is None
    assert topic.contact_html is None

    form_class = topic.with_content_extensions(TopicForm, request=object())
    form = form_class()

    assert 'contact_address' in form._fields

    form.contact_address.data = (
        "Steve Jobs\n"
        "steve@apple.com\n"
        "https://www.apple.com"
    )

    form.update_model(topic)

    assert topic.contact == (
        "Steve Jobs\n"
        "steve@apple.com\n"
        "https://www.apple.com"
    )

    assert topic.contact_html == (
        "Steve Jobs\n"
        '<a href="mailto:steve@apple.com">steve@apple.com</a>\n'
        '<a href="https://www.apple.com" rel="nofollow">'
        'https://www.apple.com</a>'
    )

    form_class = topic.with_content_extensions(TopicForm, request=object())
    form = form_class()

    form.apply_model(topic)

    assert form.contact_address.data == (
        "Steve Jobs\n"
        "steve@apple.com\n"
        "https://www.apple.com"
    )
