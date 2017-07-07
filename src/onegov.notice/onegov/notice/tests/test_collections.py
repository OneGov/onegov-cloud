from datetime import datetime
from onegov.notice import OfficialNoticeCollection
from sedate import replace_timezone
from transaction import commit


def tzdatetime(year, month, day, hour, minute, timezone):
    return replace_timezone(datetime(year, month, day, hour, minute), timezone)


def test_notice_collection(session):
    notices = OfficialNoticeCollection(session)
    assert notices.query().count() == 0

    notice_1 = notices.add(
        title='Important Announcement',
        issue_date=datetime(2015, 6, 16, 9, 30),
        timezone='US/Eastern',
        text='<em>Important</em> things happened!',
        code='ABCD',
        category='important'
    )
    notice_1.submit()
    notice_1.publish()

    commit()

    notice_1 = notices.query().one()
    assert notice_1.title == 'Important Announcement'
    assert notice_1.issue_date == tzdatetime(2015, 6, 16, 9, 30, 'US/Eastern')
    assert str(notice_1.issue_date.tzinfo) == 'UTC'
    assert notice_1.timezone == 'US/Eastern'
    assert notice_1.issue_date_localized == tzdatetime(
        2015, 6, 16, 9, 30, 'US/Eastern'
    )
    assert str(notice_1.issue_date_localized.tzinfo) == 'US/Eastern'
    assert notice_1.text == '<em>Important</em> things happened!'
    assert notice_1.code == 'ABCD'
    assert notice_1.category == 'important'

    notice_2 = notices.add(
        title='Important Announcement',
        issue_date=datetime(2015, 6, 16, 9, 30),
        timezone='US/Pacific',
        text='<em>Important</em> things happened!'
    )
    notice_2.submit()

    assert notices.query().count() == 2
    assert notices.for_state('drafted').query().count() == 0
    assert notices.for_state('submitted').query().count() == 1
    assert notices.for_state('published').query().count() == 1

    notices.delete(notice_1)
    notices.delete(notice_2)

    assert notices.query().count() == 0
    assert notices.for_state('drafted').query().count() == 0
    assert notices.for_state('submitted').query().count() == 0
    assert notices.for_state('published').query().count() == 0


def test_notice_collection_pagination(session):
    notices = OfficialNoticeCollection(session)

    assert notices.page_index == 0
    assert notices.pages_count == 0
    assert notices.batch == []

    for year in range(2008, 2010):
        for month in range(1, 13):
            notice = notices.add(
                title='Notice {0}-{1}'.format(year, month),
                issue_date=datetime(year, month, 18, 14, 00),
                timezone='US/Eastern',
                text='text'
            )
            notice.submit()
            if year > 2008:
                notice.publish()
    assert notices.query().count() == 24

    assert notices.for_state('drafted').subset_count == 0

    submitted = notices.for_state('submitted')
    assert submitted.subset_count == 12
    assert all([n.issue_date.year == 2008 for n in submitted.batch])
    assert all([n.issue_date.month < 11 for n in submitted.batch])
    assert len(submitted.next.batch) == 12 - submitted.batch_size
    assert all([n.issue_date.year == 2008 for n in submitted.next.batch])
    assert all([n.issue_date.month > 10 for n in submitted.next.batch])

    published = notices.for_state('published')
    assert published.subset_count == 12
    assert all([n.issue_date.year == 2009 for n in published.batch])
    assert all([n.issue_date.month < 11 for n in published.batch])
    assert len(published.next.batch) == 12 - published.batch_size
    assert all([n.issue_date.year == 2009 for n in published.next.batch])
    assert all([n.issue_date.month > 10 for n in published.next.batch])
