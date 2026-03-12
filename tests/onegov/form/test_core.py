from __future__ import annotations

from decimal import Decimal
from onegov.form import Form, merge_forms, move_fields
from onegov.form.fields import HoneyPotField, TimeField
from onegov.pay import Price
from wtforms.fields import EmailField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired


from typing import Any


class DummyPostData(dict[str, Any]):
    def getlist(self, key: str) -> list[Any]:
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


class DummyRequest:
    def __init__(self, POST: dict[str, Any]) -> None:
        self.POST = DummyPostData(POST)


class DummyField:
    def __init__(self, id: str, name: str, value: str) -> None:
        self.id = id
        self.name = name
        self.value = value

    def _value(self) -> str:
        return self.value


def test_submitted() -> None:

    class TestForm(Form):
        test = StringField("Test", [DataRequired()])

    request: Any = DummyRequest({})
    assert not TestForm(request.POST).submitted(request)

    request = DummyRequest({'test': 'Test'})
    assert TestForm(request.POST).submitted(request)


def test_useful_data() -> None:

    class TestForm(Form):
        a = StringField("a")
        b = StringField("b")
        c = StringField("c")
        d = HoneyPotField()

    request: Any = DummyRequest({'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D'})
    assert TestForm(request.POST).get_useful_data(
        exclude={'a', 'b'}
    ) == {'c': 'C'}


def test_match_fields() -> None:

    class TestForm(Form):
        name = StringField("Name", [DataRequired()])
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


def test_dependent_field() -> None:

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

    request: Any = DummyRequest({'switch': 'off'})
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


def test_dependent_field_inverted() -> None:

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
            depends_on=('switch', '!off')
        )

    request: Any = DummyRequest({'switch': 'off'})
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


def test_dependent_field_multiple() -> None:

    class TestForm(Form):
        switch_1 = RadioField(
            label="Switch",
            choices=[
                ('on', "On"),
                ('off', "Off")
            ]
        )

        switch_2 = RadioField(
            label="Switch",
            choices=[
                ('on', "On"),
                ('off', "Off")
            ]
        )

        optional = TimeField(
            label="Optional",
            validators=[InputRequired()],
            depends_on=('switch_1', 'on', 'switch_2', 'off')
        )

    # optional not present
    request: Any = DummyRequest({'switch_1': 'on', 'switch_2': 'on'})
    form = TestForm(request.POST)
    assert form.validate()
    request = DummyRequest({'switch_1': 'off', 'switch_2': 'off'})
    form = TestForm(request.POST)
    assert form.validate()
    request = DummyRequest({'switch_1': 'off', 'switch_2': 'on'})
    form = TestForm(request.POST)
    assert form.validate()

    # optional empty
    request = DummyRequest(
        {'switch_1': 'on', 'switch_2': 'on', 'optional': ''}
    )
    form = TestForm(request.POST)
    assert form.validate()
    request = DummyRequest(
        {'switch_1': 'off', 'switch_2': 'off', 'optional': ''}
    )
    form = TestForm(request.POST)
    assert form.validate()
    request = DummyRequest(
        {'switch_1': 'off', 'switch_2': 'on', 'optional': ''}
    )
    form = TestForm(request.POST)
    assert form.validate()

    # even though the second field is optional, it still needs to be valid
    # if there's a value (it may be empty) - we can never accept invalid values
    # as this presents a possible security risk (we could accessing something
    # that a validator filters out for security reasons).
    request = DummyRequest(
        {'switch_1': 'on', 'switch_2': 'on', 'optional': 'asdf'}
    )
    form = TestForm(request.POST)
    assert not form.validate()
    request = DummyRequest(
        {'switch_1': 'off', 'switch_2': 'off', 'optional': 'asdf'}
    )
    form = TestForm(request.POST)
    assert not form.validate()
    request = DummyRequest(
        {'switch_1': 'off', 'switch_2': 'on', 'optional': 'asdf'}
    )
    form = TestForm(request.POST)
    assert not form.validate()
    request = DummyRequest(
        {'switch_1': 'on', 'switch_2': 'off', 'optional': 'asdf'}
    )
    form = TestForm(request.POST)
    assert not form.validate()

    # dependency fullfilled
    request = DummyRequest(
        {'switch_1': 'on', 'switch_2': 'off'}
    )
    form = TestForm(request.POST)
    assert not form.validate()
    request = DummyRequest(
        {'switch_1': 'on', 'switch_2': 'off', 'optional': ''}
    )
    form = TestForm(request.POST)
    assert not form.validate()

    request = DummyRequest(
        {'switch_1': 'on', 'switch_2': 'off', 'optional': '12:00'}
    )
    form = TestForm(request.POST)
    assert form.validate()


def test_merge_forms() -> None:

    class Name(Form):
        form = 'Name'
        name = StringField("Name")

        def is_valid_name(self) -> bool:
            return True

    class Location(Form):
        form = 'Location'
        lat = StringField("Lat")
        lon = StringField("Lat")

        def is_valid_coordinate(self) -> bool:
            return True

    class User(Form):
        form = 'User'
        name = StringField("User")

        def is_valid_user(self) -> bool:
            return True

    full: Any = merge_forms(Name, Location, User)()
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


def test_move_fields() -> None:

    class Test(Form):
        a = StringField('a')
        b = StringField('b')
        c = StringField('c')

    Moved = move_fields(Test, ['a'], None)

    assert list(Test()._fields.keys()) == ['a', 'b', 'c']
    assert list(Moved()._fields.keys()) == ['b', 'c', 'a']


def test_delete_fields() -> None:

    class Test(Form):
        a = StringField('a', fieldset='Letters')
        one = StringField('1', fieldset='Numerals')
        two = StringField('2', fieldset='Numerals')

    form = Test()
    assert form.a.name == 'a'
    assert form.one.name == 'one'
    assert form.two.name == 'two'
    assert len(form.fieldsets) == 2

    form.delete_field('one')

    assert form.a.name == 'a'
    assert 'one' not in form
    assert form.two.name == 'two'
    assert len(form.fieldsets) == 2

    form.delete_field('two')

    assert form.a.name == 'a'
    assert 'one' not in form
    assert 'two' not in form
    assert len(form.fieldsets) == 1


def test_ensurances() -> None:

    class EnsuredForm(Form):
        foo = StringField('foo')
        bar = StringField('bar')

        ensure_foo_and_bar_called = 0
        ensure_foo_or_bar_called = 0

        @property
        def ensure_not_triggered(self) -> bool | None:
            raise AssertionError()

        def ensure_foo_and_bar(self) -> bool | None:
            self.ensure_foo_and_bar_called += 1

            if not (self.foo.data and self.bar.data):
                return False
            return None

        def ensure_foo_or_bar(self) -> bool | None:
            self.ensure_foo_or_bar_called += 1

            if not (self.foo.data or self.bar.data):
                return False
            return None

    form = EnsuredForm()

    assert not form.validate()
    assert form.ensure_foo_and_bar_called == 1
    assert form.ensure_foo_or_bar_called == 1

    form.foo.data = 'foo'
    form.bar.data = 'bar'

    assert form.validate()

    assert form.ensure_foo_and_bar_called == 2
    assert form.ensure_foo_or_bar_called == 2


def test_pricing() -> None:

    class TestForm(Form):
        ticket_insurance = RadioField('Option', choices=[
            ('yes', 'Yes'),
            ('no', 'No')
        ], pricing={
            'yes': (10.0, 'CHF'),
        })

        discount_code = StringField('Discount Code', pricing={
            'FOO': (-5.0, 'CHF')
        })

    def post(data: dict[str, Any]) -> Any:
        return DummyRequest(data).POST

    form = TestForm(post({}))
    assert form.total() is None
    assert form.prices() == []

    form = TestForm(post({'ticket_insurance': 'no'}))
    assert form.total() is None
    assert form.prices() == []

    form = TestForm(post({'ticket_insurance': 'yes'}))
    assert form.total() == Price(Decimal('10.0'), 'CHF')
    assert form.prices() == [
        ('ticket_insurance', Price(Decimal(10.0), 'CHF'))
    ]

    form = TestForm(post({'ticket_insurance': 'yes', 'discount_code': 'test'}))
    assert form.total() == Price(Decimal('10.0'), 'CHF')
    assert form.prices() == [
        ('ticket_insurance', Price(Decimal(10.0), 'CHF'))
    ]

    form = TestForm(post({'ticket_insurance': 'yes', 'discount_code': 'FOO'}))
    assert form.total() == Price(Decimal('5.0'), 'CHF')
    assert form.prices() == [
        ('ticket_insurance', Price(Decimal(10.0), 'CHF')),
        ('discount_code', Price(Decimal(-5.0), 'CHF'))
    ]


def test_dependent_pricing() -> None:

    class TestForm(Form):

        give_donation = RadioField('Option', choices=[
            ('yes', 'Yes'),
            ('no', 'No')
        ])

        donation = RadioField('Option', choices=[
            ('small', '10 CHF'),
            ('big', '100 CHF'),
        ], pricing={
            'small': (10.0, 'CHF'),
            'big': (100.0, 'CHF')
        }, depends_on=(
            'give_donation', 'yes'
        ))

    def post(data: dict[str, Any]) -> Any:
        return DummyRequest(data).POST

    form = TestForm(post({'give_donation': 'yes', 'donation': 'small'}))
    assert form.total() == Price(Decimal('10.0'), 'CHF')
    assert form.prices() == [
        ('donation', Price(Decimal(10.0), 'CHF'))
    ]

    form = TestForm(post({'give_donation': 'yes', 'donation': 'big'}))
    assert form.total() == Price(Decimal('100.0'), 'CHF')
    assert form.prices() == [
        ('donation', Price(Decimal(100.0), 'CHF'))
    ]

    form = TestForm(post({'give_donation': 'no', 'donation': 'small'}))
    assert form.total() is None
    assert form.prices() == []

    form = TestForm(post({'give_donation': 'no', 'donation': 'big'}))
    assert form.total() is None
    assert form.prices() == []


def test_nested_dependent_pricing() -> None:

    class TestForm(Form):

        give_donation = RadioField('Option', choices=[
            ('yes', 'Yes'),
            ('no', 'No')
        ])

        really_give = RadioField('Option', choices=[
            ('yes', 'Yes'),
            ('no', 'No')
        ], depends_on=('give_donation', 'yes'))

        donation = RadioField('Option', choices=[
            ('small', '10 CHF'),
            ('big', '100 CHF'),
        ], pricing={
            'small': (10.0, 'CHF'),
            'big': (100.0, 'CHF')
        }, depends_on=(
            'really_give', 'yes'
        ))

    def post(data: dict[str, Any]) -> Any:
        return DummyRequest(data).POST

    assert TestForm(post({
        'give_donation': 'no',
        'really_give': 'yes',
        'donation': 'small'
    })).total() is None

    assert TestForm(post({
        'give_donation': 'yes',
        'really_give': 'no',
        'donation': 'small'
    })).total() is None

    assert TestForm(post({
        'give_donation': 'yes',
        'really_give': 'yes',
        'donation': 'small'
    })).total() == Price(Decimal(10.0), 'CHF')


def test_clone_form() -> None:

    class FooForm(Form):
        base = StringField('123')
        name = StringField('Foo')

    class BarForm(FooForm):
        name = StringField('Bar')

    assert BarForm().base.label.text == '123'
    assert FooForm().base.label.text == '123'

    assert BarForm().name.label.text == 'Bar'
    assert FooForm().name.label.text == 'Foo'

    FooForm.name.args = ('Noo', )
    FooForm.base.args = ('Abc', )

    assert BarForm().base.label.text == 'Abc'
    assert FooForm().base.label.text == 'Abc'

    assert BarForm().name.label.text == 'Bar'
    assert FooForm().name.label.text == 'Noo'

    NewForm = FooForm.clone()
    NewForm.base.args = ('Xyz', )

    assert BarForm().base.label.text == 'Abc'
    assert FooForm().base.label.text == 'Abc'
    assert NewForm().base.label.text == 'Xyz'

    assert BarForm().name.label.text == 'Bar'
    assert FooForm().name.label.text == 'Noo'
    assert NewForm().name.label.text == 'Noo'
