from __future__ import annotations

from datetime import date, datetime
from markupsafe import Markup
from onegov.core.utils import Bunch, generate_fts_phonenumbers
from onegov.org import utils
from pytz import timezone
from onegov.org.utils import emails_for_new_ticket
from onegov.ticket import Ticket, TicketPermission
from onegov.user import UserGroup, User


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_annotate_html() -> None:
    html = Markup("<p><img/></p><p></p>")
    assert utils.annotate_html(html) == (
        '<p class="has-img"><img class="lazyload-alt"></p><p></p>'
    )

    html = Markup("<p class='x'><img/></p><p></p>")
    assert utils.annotate_html(html) == (
        '<p class="x has-img"><img class="lazyload-alt"></p><p></p>'
    )

    html = Markup("<strong></strong>")
    assert utils.annotate_html(html) == html

    html = Markup('<a href="http://www.seantis.ch"></a>')
    assert utils.annotate_html(html) == html

    html = Markup('no html')
    assert utils.annotate_html(html) == 'no html'

    html = Markup('<p><a href="http://www.seantis.ch"></a></p>')
    assert utils.annotate_html(html) == html

    html = Markup(
        '<p><a href="https://www.youtube.com/watch?v=dQw4w9WgXcQ"></a></p>'
    )
    assert '<p class="has-video">' in utils.annotate_html(html)
    assert 'class="has-video"></a>' in utils.annotate_html(html)

    html = Markup(
        '<p><a href="https://youtu.be/gEbx_0dBjbM"></a></p>'
    )
    assert '<p class="has-video">' in utils.annotate_html(html)
    assert 'class="has-video"></a>' in utils.annotate_html(html)

    html = Markup(
        '<p>'
        '<a href="https://www.youtube.com/watch?v=dQw4w9WgXcQ"></a>'
        '<img />'
        '</p>'
    )
    assert '<p class="has-img has-video">' in utils.annotate_html(html)
    assert 'class="has-video"></a>' in utils.annotate_html(html)

    html = Markup(
        '<p># foo, #bar, #baz qux</p>'
    )

    assert "has-hashtag" in utils.annotate_html(Markup('<p>#foo</p>'))
    assert "has-hashtag" in utils.annotate_html(Markup('<p>#bar</p>'))
    assert "has-hashtag" not in utils.annotate_html(Markup('<p>#xy</p>'))


def test_remove_empty_paragraphs() -> None:
    html = Markup("<p><br></p>")
    assert utils.remove_empty_paragraphs(html) == ""

    # multiple br elements added by shift+enter are left alone (this is
    # a way to manually override the empty paragraphs removal)
    html = Markup("<p><br><br></p>")
    assert utils.remove_empty_paragraphs(html) == "<p><br><br></p>"

    html = Markup("<p> <br></p>")
    assert utils.remove_empty_paragraphs(html) == ""

    html = Markup("<p>hey</p>")
    assert utils.remove_empty_paragraphs(html) == "<p>hey</p>"

    html = Markup("<p><img></p>")
    assert utils.remove_empty_paragraphs(html) == "<p><img></p>"


def test_predict_next_value() -> None:
    assert utils.predict_next_value((1, )) is None
    assert utils.predict_next_value((1, 1)) is None
    assert utils.predict_next_value((1, 1, 1)) == 1
    assert utils.predict_next_value((2, 1, 2, 1)) == 2
    assert utils.predict_next_value((1, 2, 1, 2)) == 1
    assert utils.predict_next_value((2, 2, 2, 1)) is None
    assert utils.predict_next_value((2, 4, 6)) == 8
    assert utils.predict_next_value((1, 2, 3)) == 4
    assert utils.predict_next_value((1, 2, 3, 5)) is None
    assert utils.predict_next_value((1, 2, 3, 5, 6), min_probability=0) == 7
    assert utils.predict_next_value((1, 2, 3, 5, 6), min_probability=.5) == 7
    assert utils.predict_next_value(
        (1, 2, 3, 5, 6), min_probability=.6) is None


def test_predict_next_daterange() -> None:
    assert utils.predict_next_daterange((  # type: ignore[arg-type]
        (date(2017, 1, 1), date(2017, 1, 1)),
        (date(2017, 1, 2), date(2017, 1, 2)),
        (date(2017, 1, 3), date(2017, 1, 3)),
    )) == (date(2017, 1, 4), date(2017, 1, 4))

    assert utils.predict_next_daterange((  # type: ignore[arg-type]
        (date(2017, 1, 1), date(2017, 1, 1)),
        (date(2017, 1, 3), date(2017, 1, 3)),
        (date(2017, 1, 5), date(2017, 1, 5)),
    )) == (date(2017, 1, 7), date(2017, 1, 7))

    assert utils.predict_next_daterange((
        (datetime(2017, 1, 1, 10), datetime(2017, 1, 1, 12)),
        (datetime(2017, 1, 3, 10), datetime(2017, 1, 3, 12)),
        (datetime(2017, 1, 5, 10), datetime(2017, 1, 5, 12)),
    )) == (datetime(2017, 1, 7, 10), datetime(2017, 1, 7, 12))


def test_predict_next_daterange_dst_st_transitions() -> None:
    tz_ch = timezone('Europe/Zurich')

    def dt_ch(*args: int, is_dst: bool | None = None) -> datetime:
        # None -> not ambiguous, pick for me
        dt = datetime(*args, tzinfo=None)  # type: ignore[arg-type, misc]
        return tz_ch.localize(dt, is_dst=is_dst)

    # DST -> ST both times abiguous
    assert utils.predict_next_daterange((
        (dt_ch(2022, 10, 9, 2), dt_ch(2022, 10, 9, 2, 30)),
        (dt_ch(2022, 10, 16, 2), dt_ch(2022, 10, 16, 2, 30)),
        (dt_ch(2022, 10, 23, 2), dt_ch(2022, 10, 23, 2, 30)),
    )) == (
        # we expect the start and end to both be in ST
        dt_ch(2022, 10, 30, 2, is_dst=False),
        dt_ch(2022, 10, 30, 2, 30, is_dst=False)
    )

    # DST -> ST start time ambiguous
    assert utils.predict_next_daterange((
        (dt_ch(2022, 10, 9, 2), dt_ch(2022, 10, 9, 4)),
        (dt_ch(2022, 10, 16, 2), dt_ch(2022, 10, 16, 4)),
        (dt_ch(2022, 10, 23, 2), dt_ch(2022, 10, 23, 4)),
    )) == (
        # we expect the start to be in ST
        dt_ch(2022, 10, 30, 2, is_dst=False),
        dt_ch(2022, 10, 30, 4)
    )

    # DST -> ST end time ambiguous
    assert utils.predict_next_daterange((
        (dt_ch(2022, 10, 9, 1), dt_ch(2022, 10, 9, 2)),
        (dt_ch(2022, 10, 16, 1), dt_ch(2022, 10, 16, 2)),
        (dt_ch(2022, 10, 23, 1), dt_ch(2022, 10, 23, 2)),
    )) == (
        # we expect the end to be in ST
        dt_ch(2022, 10, 30, 1),
        dt_ch(2022, 10, 30, 2, is_dst=False)
    )

    # DST -> ST some other time
    assert utils.predict_next_daterange((
        (dt_ch(2022, 10, 9, 10), dt_ch(2022, 10, 9, 12)),
        (dt_ch(2022, 10, 16, 10), dt_ch(2022, 10, 16, 12)),
        (dt_ch(2022, 10, 23, 10), dt_ch(2022, 10, 23, 12)),
    )) == (dt_ch(2022, 10, 30, 10), dt_ch(2022, 10, 30, 12))

    # ST -> DST start time doesn't exist (no suggestion)
    assert utils.predict_next_daterange((
        (dt_ch(2022, 3, 6, 2), dt_ch(2022, 3, 6, 3)),
        (dt_ch(2022, 3, 13, 2), dt_ch(2022, 3, 13, 3)),
        (dt_ch(2022, 3, 20, 2), dt_ch(2022, 3, 20, 3)),
    )) is None

    # ST -> DST some other time
    assert utils.predict_next_daterange((
        (dt_ch(2022, 3, 6, 10), dt_ch(2022, 3, 6, 12)),
        (dt_ch(2022, 3, 13, 10), dt_ch(2022, 3, 13, 12)),
        (dt_ch(2022, 3, 20, 10), dt_ch(2022, 3, 20, 12)),
    )) == (dt_ch(2022, 3, 27, 10), dt_ch(2022, 3, 27, 12))


def test_emails_for_new_ticket(session: Session) -> None:
    session.query(User).delete()

    group1 = UserGroup(name='somename')

    permission1 = TicketPermission(
        handler_code='DIR',
        group='Sports',
        user_group=group1,
        exclusive=True,
        immediate_notification=True,
    )

    permission2 = TicketPermission(
        handler_code='FRM',
        group='Music',
        user_group=group1,
        exclusive=False,
        immediate_notification=True,
    )

    user1 = User(
        username='user1@example.org',
        password_hash='password_hash',
        role='editor'
    )
    user2 = User(
        username='user2@example.org',
        password_hash='password_hash',
        role='editor'
    )
    user_with_bogus_username = User(
        username='admin',
        password_hash='password_hash',
        role='admin'
    )

    group1.users = [user1, user_with_bogus_username]

    session.add(user1)
    session.add(user2)
    session.add(permission1)
    session.add(permission2)
    session.add(group1)
    session.flush()

    request: Any = Bunch(**{
        'session': session,
        'email_for_new_tickets': 'tickets@example.org',
        'app.ticket_permissions': {
            'DIR': {'Sports': [group1.id.hex]},
        },
    })
    ticket1 = Ticket(handler_code='DIR', group='Sports')

    result = {a.addr_spec for a in emails_for_new_ticket(request, ticket1)}
    assert result == {'tickets@example.org', 'user1@example.org'}

    group2 = UserGroup(name="foo")
    user3 = User(
        username='user3@example.org',
        password_hash='password_hash',
        role='editor'
    )

    permission3 = TicketPermission(
        handler_code='DIR',
        group=None,
        user_group=group2,
        exclusive=False,
        immediate_notification=True,
    )

    permission4 = TicketPermission(
        handler_code='FRM',
        group=None,
        user_group=group2,
        exclusive=False,
        immediate_notification=True,
    )

    group2.users = [user3]

    session.add(user3)
    session.add(group2)
    session.flush()

    request = Bunch(**{
        'session': session,
        'email_for_new_tickets': None,
        'app.ticket_permissions': {
            'DIR': {'Sports': [group1.id.hex]},
        },
    })
    ticket2 = Ticket(handler_code='DIR', group='Sports')
    result = {a.addr_spec for a in emails_for_new_ticket(request, ticket2)}
    assert result == {'user1@example.org'}

    ticket3 = Ticket(handler_code='FRM', group='Music')
    result = {a.addr_spec for a in emails_for_new_ticket(request, ticket3)}
    assert result == {'user1@example.org', 'user3@example.org'}

    request = Bunch(**{
        'session': session,
        'email_for_new_tickets': 'user3@example.org',
        'app.ticket_permissions': {
            'DIR': {'Sports': [group1.id.hex]},
        },
    })
    result = {a.addr_spec for a in emails_for_new_ticket(request, ticket2)}
    assert result == {'user1@example.org', 'user3@example.org'}
    result = {a.addr_spec for a in emails_for_new_ticket(request, ticket3)}
    assert result == {'user1@example.org', 'user3@example.org'}

    # set a shared email instead
    group2.meta = {'shared_email': 'shared@example.org'}
    session.flush()
    request = Bunch(**{
        'session': session,
        'email_for_new_tickets': None,
        'app.ticket_permissions': {
            'DIR': {'Sports': [group1.id.hex]},
        },
    })
    result = {a.addr_spec for a in emails_for_new_ticket(request, ticket2)}
    assert result == {'user1@example.org'}
    result = {a.addr_spec for a in emails_for_new_ticket(request, ticket3)}
    assert result == {'user1@example.org', 'shared@example.org'}

    request = Bunch(**{
        'session': session,
        'email_for_new_tickets': 'user3@example.org',
        'app.ticket_permissions': {
            'DIR': {'Sports': [group1.id.hex]},
        },
    })
    result = {a.addr_spec for a in emails_for_new_ticket(request, ticket2)}
    assert result == {'user1@example.org', 'user3@example.org'}
    result = {a.addr_spec for a in emails_for_new_ticket(request, ticket3)}
    assert result == {
        'user1@example.org', 'user3@example.org', 'shared@example.org'
    }


def test_extract_categories_and_subcategories() -> None:
    assert utils.extract_categories_and_subcategories([]) == ([], [])
    # FIXME: This is a weird singularity, this should probably return
    #        just an empty list
    assert utils.extract_categories_and_subcategories(  # type: ignore[comparison-overlap]
        [], flattened=True) == ([], [])

    categories = [
        'Category 1',
        'Category 2',
    ]
    assert utils.extract_categories_and_subcategories(categories) == (
        ['Category 1', 'Category 2'],
        [[], []]
    )
    assert utils.extract_categories_and_subcategories(
        categories, flattened=True) == ['Category 1', 'Category 2']

    assert utils.extract_categories_and_subcategories([
        {'a': ['a1', 'a2']},
        {'b': ['b1']},
        {'c': []},
        'd'
    ]) == (
        ['a', 'b', 'c', 'd'],
        [['a1', 'a2'], ['b1'], [], []]
    )
    assert utils.extract_categories_and_subcategories([
        {'a': ['a1', 'a2']},
        {'b': ['b1']},
        {'c': []},
        'd'
    ], flattened=True) == ['a', 'b', 'c', 'd', 'a1', 'a2', 'b1']


def test_format_phone_number() -> None:
    assert utils.format_phone_number('+41411112233') == '+41 41 111 22 33'
    assert utils.format_phone_number('0041411112233') == '+41 41 111 22 33'
    assert utils.format_phone_number('0411112233') == '+41 41 111 22 33'
    assert utils.format_phone_number('411112233') == '+41 41 111 22 33'
    assert utils.format_phone_number('41 111 22 33') == '+41 41 111 22 33'
    assert utils.format_phone_number('041 111 22 33') == '+41 41 111 22 33'
    assert utils.format_phone_number('041-111-22-33') == '+41 41 111 22 33'
    assert utils.format_phone_number('041/111/22/33') == '+41 41 111 22 33'
    assert utils.format_phone_number('041/111-22 33') == '+41 41 111 22 33'

    # invalid phone numbers are just prefixed with the country code
    assert utils.format_phone_number('41111223') == '+41 41111223'
    assert utils.format_phone_number('4111122') == '+41 4111122'
    assert utils.format_phone_number('411112') == '+41 411112'
    assert utils.format_phone_number('41111') == '+41 41111'
    assert utils.format_phone_number('4111') == '+41 4111'
    assert utils.format_phone_number('411') == '+41 411'
    assert utils.format_phone_number('41') == '+41 41'
    assert utils.format_phone_number('') == ''
    assert utils.format_phone_number(None) == ''  # type: ignore[arg-type]

    # force error (too long for phone number), will return the input
    long_text = ('You can reach me during office hours at 041 111 22 33 '
                 'otherwise at 041 111 22 44')
    assert utils.format_phone_number(long_text) == long_text


def test_generate_fts_phonenumbers() -> None:
    assert [] == generate_fts_phonenumbers([])
    assert [] == generate_fts_phonenumbers(())
    assert [] == generate_fts_phonenumbers({})

    numbers = ['+41 44 567 88 99']
    expected = ['+41445678899', '0445678899', '5678899', '8899']
    result = generate_fts_phonenumbers(numbers)
    assert result == expected

    numbers = ['+41 44 567 88 99', '+41 41 445 31 11']
    expected = ['+41445678899', '0445678899', '5678899', '8899',
                '+41414453111', '0414453111', '4453111', '3111']
    result = generate_fts_phonenumbers(numbers)
    assert result == expected

    # invalid number
    assert ['+41'] == generate_fts_phonenumbers(['+41'])
