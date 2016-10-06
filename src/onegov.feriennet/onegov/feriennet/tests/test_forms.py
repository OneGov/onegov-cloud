from onegov.core.utils import Bunch
from onegov.feriennet.forms import VacationActivityForm
from onegov.user import UserCollection


def test_vacation_activity_form(session, test_password):
    users = UserCollection(session)
    users.add(
        username='admin@example.org',
        realname='Robert Baratheon',
        password='foobar',
        role='admin')
    users.add(
        username='editor@example.org',
        realname=None,
        password='foobar',
        role='editor')
    users.add(
        username='member@example.org',
        realname=None,
        password='foobar',
        role='member')

    form = VacationActivityForm()
    form.request = Bunch(
        is_admin=True,
        current_username='editor@example.org',
        app=Bunch(
            session=lambda: session
        )
    )

    form.on_request()

    assert form.username.data == 'editor@example.org'
    assert form.username.choices == [
        ('editor@example.org', 'editor@example.org'),
        ('admin@example.org', 'Robert Baratheon')
    ]

    form.request.is_admin = False
    form.on_request()

    assert form.username is None
