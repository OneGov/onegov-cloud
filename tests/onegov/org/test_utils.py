from datetime import date, datetime
from onegov.core.utils import Bunch
from onegov.org import utils
from pytz import timezone
from onegov.org.utils import (
    ticket_directory_groups, user_group_emails_for_new_ticket,
    timestamp_to_seconds)
from onegov.ticket import Ticket
from onegov.user import UserGroup, User


def test_annotate_html():
    html = "<p><img/></p><p></p>"
    assert utils.annotate_html(html) == (
        '<p class="has-img"><img class="lazyload-alt"></p><p></p>'
    )

    html = "<p class='x'><img/></p><p></p>"
    assert utils.annotate_html(html) == (
        '<p class="x has-img"><img class="lazyload-alt"></p><p></p>'
    )

    html = "<strong></strong>"
    assert utils.annotate_html(html) == html

    html = '<a href="http://www.seantis.ch"></a>'
    assert utils.annotate_html(html) == html

    html = 'no html'
    assert utils.annotate_html(html) == 'no html'

    html = '<p><a href="http://www.seantis.ch"></a></p>'
    assert utils.annotate_html(html) == html

    html = (
        '<p><a href="https://www.youtube.com/watch?v=dQw4w9WgXcQ"></a></p>'
    )
    assert '<p class="has-video">' in utils.annotate_html(html)
    assert 'class="has-video"></a>' in utils.annotate_html(html)

    html = (
        '<p><a href="https://youtu.be/gEbx_0dBjbM"></a></p>'
    )
    assert '<p class="has-video">' in utils.annotate_html(html)
    assert 'class="has-video"></a>' in utils.annotate_html(html)

    html = (
        '<p>'
        '<a href="https://www.youtube.com/watch?v=dQw4w9WgXcQ"></a>'
        '<img />'
        '</p>'
    )
    assert '<p class="has-img has-video">' in utils.annotate_html(html)
    assert 'class="has-video"></a>' in utils.annotate_html(html)

    html = (
        '<p># foo, #bar, #baz qux</p>'
    )

    assert "has-hashtag" in utils.annotate_html('<p>#foo</p>')
    assert "has-hashtag" in utils.annotate_html('<p>#bar</p>')
    assert "has-hashtag" not in utils.annotate_html('<p>#xy</p>')


def test_remove_empty_paragraphs():
    html = "<p><br></p>"
    assert utils.remove_empty_paragraphs(html) == ""

    # multiple br elements added by shift+enter are left alone (this is
    # a way to manually override the empty paragraphs removal)
    html = "<p><br><br></p>"
    assert utils.remove_empty_paragraphs(html) == "<p><br><br></p>"

    html = "<p> <br></p>"
    assert utils.remove_empty_paragraphs(html) == ""

    html = "<p>hey</p>"
    assert utils.remove_empty_paragraphs(html) == "<p>hey</p>"

    html = "<p><img></p>"
    assert utils.remove_empty_paragraphs(html) == "<p><img></p>"


def test_predict_next_value():
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


def test_predict_next_daterange():
    assert utils.predict_next_daterange((
        (date(2017, 1, 1), date(2017, 1, 1)),
        (date(2017, 1, 2), date(2017, 1, 2)),
        (date(2017, 1, 3), date(2017, 1, 3)),
    )) == (date(2017, 1, 4), date(2017, 1, 4))

    assert utils.predict_next_daterange((
        (date(2017, 1, 1), date(2017, 1, 1)),
        (date(2017, 1, 3), date(2017, 1, 3)),
        (date(2017, 1, 5), date(2017, 1, 5)),
    )) == (date(2017, 1, 7), date(2017, 1, 7))

    assert utils.predict_next_daterange((
        (datetime(2017, 1, 1, 10), datetime(2017, 1, 1, 12)),
        (datetime(2017, 1, 3, 10), datetime(2017, 1, 3, 12)),
        (datetime(2017, 1, 5, 10), datetime(2017, 1, 5, 12)),
    )) == (datetime(2017, 1, 7, 10), datetime(2017, 1, 7, 12))


def test_predict_next_daterange_dst_st_transitions():
    tz_ch = timezone('Europe/Zurich')

    def dt_ch(*args, is_dst=None):
        # None -> not ambiguous, pick for me
        dt = datetime(*args, tzinfo=None)
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


def test_select_ticket_groups(session):

    def create_ticket(handler_code, group=''):
        result = Ticket(
            number=f'{handler_code}-{group}-1',
            title=f'{handler_code}-{group}',
            group=group,
            handler_code=handler_code,
            handler_id=f'{handler_code}-{group}'
        )
        session.add(result)
        return result

    create_ticket('EVN')

    dir_groups = ticket_directory_groups(session)
    assert tuple(dir_groups) == ()

    create_ticket('DIR', 'Steuererklärung')
    create_ticket('DIR', 'Wohnsitzbestätigung')
    session.flush()

    dir_groups = ticket_directory_groups(session)
    assert tuple(dir_groups) == ('Steuererklärung', 'Wohnsitzbestätigung')


def test_user_group_emails_for_new_ticket(session):

    session.query(User).delete()
    group_meta = dict(directories=['Sports', 'Music'])

    group1 = UserGroup(name="somename", meta=group_meta)

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

    group1.users = [user1]  # user1 is in the group

    session.add(user1)
    session.add(user2)
    session.add(group1)
    session.flush()

    request = Bunch(
        session=session,
    )
    ticket1 = Ticket(handler_code="DIR", group="Sports")

    result = user_group_emails_for_new_ticket(request, ticket1)
    assert result == {"user1@example.org"}

    session.query(User).delete()

    group2 = UserGroup(name="foo", meta={})  # no directories
    user1 = User(
        username='user2@example.org',
        password_hash='password_hash',
        role='editor'
    )

    group2.users = [user1]

    session.add(user1)
    session.add(group1)
    session.flush()

    request = Bunch(
        session=session,
    )
    ticket1 = Ticket(handler_code="DIR")
    result = user_group_emails_for_new_ticket(request, ticket1)
    assert result == set()


def test_timestamps_to_seconds():
    t1 = '1h2m3s'
    t2 = '2m3s'
    t3 = '50s'

    assert timestamp_to_seconds(t1) == 3723
    assert timestamp_to_seconds(t2) == 123
    assert timestamp_to_seconds(t3) == 50
