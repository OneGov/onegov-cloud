from onegov.form import Form, merge_forms, with_options
from wtforms import RadioField, StringField, TextAreaField, validators
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired
from wtforms.widgets import TextArea
from wtforms_components import TimeField


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


class DummyRequest(object):
    def __init__(self, POST):
        self.POST = DummyPostData(POST)


class DummyField(object):
    def __init__(self, id, name, value):
        self.id = id
        self.name = name
        self.value = value

    def _value(self):
        return self.value


def test_submitted():

    class TestForm(Form):
        test = StringField("Test", [validators.DataRequired()])

    request = DummyRequest({})
    assert not TestForm(request.POST).submitted(request)

    request = DummyRequest({'test': 'Test'})
    assert TestForm(request.POST).submitted(request)


def test_useful_data():

    class TestForm(Form):
        a = StringField("a")
        b = StringField("b")
        c = StringField("c")

    request = DummyRequest({'a': 'A', 'b': 'B', 'c': 'C'})
    assert TestForm(request.POST).get_useful_data(exclude={'a', 'b'}) \
        == {'c': 'C'}


def test_with_options():
    widget = with_options(TextArea, class_="markdown")
    assert 'class="markdown"' in widget(DummyField('one', 'one', '1'))

    widget = with_options(TextArea, class_="x")
    assert 'class="x"' in widget(DummyField('one', 'one', '1'))


def test_match_fields():

    class TestForm(Form):
        name = StringField("Name", [validators.DataRequired()])
        email = EmailField("E-Mail")
        comment = TextAreaField("Comment")

    form = TestForm()
    assert form.match_fields(required=True) == ['name']
    assert form.match_fields(required=False) == ['email', 'comment']
    assert form.match_fields(required=None) == ['name', 'email', 'comment']
    assert form.match_fields(required=None, limit=1) == ['name']
    assert form.match_fields(include_classes=(StringField, ))\
        == ['name', 'email', 'comment']
    assert form.match_fields(include_classes=(EmailField, )) == ['email']
    assert form.match_fields(exclude_classes=(TextAreaField, ))\
        == ['name', 'email']


def test_dependent_field():

    class TestForm(Form):
        switch = RadioField(
            label="Switch",
            choices=[
                ('on', "On"),
                ('off', "Off")
            ]
        )

        optional = TimeField(
            label="Optional",
            validators=[InputRequired()],
            depends_on=('switch', 'on')
        )

    request = DummyRequest({'switch': 'off'})
    form = TestForm(request.POST)
    assert form.validate()

    request = DummyRequest({'switch': 'off', 'optional': ''})
    form = TestForm(request.POST)
    assert form.validate()

    # even though the second field is optional, it still needs to be valid
    # if there's a value (it may be empty) - we can never accept invalid values
    # as this presents a possible security risk (we could accessing something
    # that a validator filters out for security reasons).
    request = DummyRequest({'switch': 'off', 'optional': 'asdf'})
    form = TestForm(request.POST)
    assert not form.validate()

    request = DummyRequest({'switch': 'off', 'optional': '12:00'})
    form = TestForm(request.POST)
    assert form.validate()

    request = DummyRequest({'switch': 'on'})
    form = TestForm(request.POST)
    assert not form.validate()

    request = DummyRequest({'switch': 'on', 'optional': ''})
    form = TestForm(request.POST)
    assert not form.validate()

    request = DummyRequest({'switch': 'on', 'optional': 'asdf'})
    form = TestForm(request.POST)
    assert not form.validate()

    request = DummyRequest({'switch': 'on', 'optional': '12:00'})
    form = TestForm(request.POST)
    assert form.validate()


def test_merge_forms():

    class Name(Form):
        form = 'Name'
        name = StringField("Name")

        def is_valid_name(self):
            return True

    class Location(Form):
        form = 'Location'
        lat = StringField("Lat")
        lon = StringField("Lat")

        def is_valid_coordinate(self):
            return True

    class User(Form):
        form = 'User'
        name = StringField("User")

        def is_valid_user(self):
            return True

    full = merge_forms(Name, Location, User)()
    assert list(full._fields.keys()) == ['name', 'lat', 'lon']
    assert full.name.label.text == "Name"
    assert full.form == 'Name'
    assert full.is_valid_name()
    assert full.is_valid_coordinate()
    assert full.is_valid_user()

    full = merge_forms(User, Location, Name)()
    assert list(full._fields.keys()) == ['name', 'lat', 'lon']
    assert full.name.label.text == "User"
    assert full.form == 'User'
    assert full.is_valid_name()
    assert full.is_valid_coordinate()
    assert full.is_valid_user()

    full = merge_forms(Location, User, Name)()
    assert list(full._fields.keys()) == ['lat', 'lon', 'name']
    assert full.name.label.text == "User"
    assert full.form == 'Location'
    assert full.is_valid_name()
    assert full.is_valid_coordinate()
    assert full.is_valid_user()
