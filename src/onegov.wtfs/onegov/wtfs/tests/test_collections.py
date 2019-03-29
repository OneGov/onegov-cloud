from datetime import date
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.collections import NotificationCollection
from onegov.wtfs.collections import PaymentTypeCollection
from onegov.wtfs.collections import ScanJobCollection
from uuid import uuid4


def test_payment_types(session):
    payment_types = PaymentTypeCollection(session)
    payment_type = payment_types.add(
        name='normal',
        _price_per_quantity=700
    )

    assert payment_type.name == 'normal'
    assert payment_type._price_per_quantity == 700
    assert payment_type.price_per_quantity == 7.0


def test_municipalities(session):
    municipalities = MunicipalityCollection(session)
    municipalities.add(
        name='Boppelsen',
        bfs_number=82,
    )
    municipalities.add(
        name='Adlikon',
        bfs_number=21,
    )

    assert [(m.name, m.bfs_number) for m in municipalities.query()] == [
        ('Adlikon', 21),
        ('Boppelsen', 82)
    ]

    # Import data
    data = {
        21: {'dates': [date(2019, 1, 1), date(2019, 1, 7)]},
        241: {'dates': [date(2019, 1, 2), date(2019, 1, 8)]},
        82: {'dates': [date(2019, 1, 4), date(2019, 1, 10)]}
    }
    municipalities.import_data(data)
    assert [
        (m.bfs_number, [d.date for d in m.pickup_dates])
        for m in municipalities.query()
    ] == [
        (21, [date(2019, 1, 1), date(2019, 1, 7)]),
        (82, [date(2019, 1, 4), date(2019, 1, 10)])
    ]

    municipalities.add(
        name='Aesch',
        bfs_number=241,
    )
    data = {
        21: {'dates': [date(2019, 1, 7), date(2019, 1, 8)]},
        241: {'dates': [date(2019, 1, 2), date(2019, 1, 8)]},
        82: {'dates': []}
    }
    municipalities.import_data(data)
    assert [
        (m.bfs_number, [d.date for d in m.pickup_dates])
        for m in municipalities.query()
    ] == [
        (21, [date(2019, 1, 1), date(2019, 1, 7), date(2019, 1, 8)]),
        (241, [date(2019, 1, 2), date(2019, 1, 8)]),
        (82, [date(2019, 1, 4), date(2019, 1, 10)])
    ]


def test_notifications(session):
    notifications = NotificationCollection(session)
    notification = notifications.add(
        title="Lorem ipsum",
        text="Lorem ipsum dolor sit amet.",
        channel_id="wtfs",
        owner="admin"
    )

    assert notification.title == "Lorem ipsum"
    assert notification.text == "Lorem ipsum dolor sit amet."
    assert notification.channel_id == "wtfs"
    assert notification.owner == "admin"
    assert notification.type == "wtfs_notification"


def test_scan_jobs(session):
    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(name='Boppelsen', bfs_number=82)

    scan_jobs = ScanJobCollection(session)
    for day in (2, 1, 4, 3):
        scan_jobs.add(
            type='normal',
            municipality_id=municipality.id,
            dispatch_date=date(2019, 1, day)
        )

    assert [s.dispatch_date.day for s in scan_jobs.query()] == [4, 3, 2, 1]


def test_scan_jobs_default():
    scan_jobs = ScanJobCollection(
        session=1,
        page=3,
        from_date=4,
        to_date=5,
        type=6,
        municipality_id=7,
        sort_by=8,
        sort_order=9
    )
    assert scan_jobs.session == 1
    assert scan_jobs.page == 3
    assert scan_jobs.from_date == 4
    assert scan_jobs.to_date == 5
    assert scan_jobs.type == 6
    assert scan_jobs.municipality_id == 7
    assert scan_jobs.sort_by == 8
    assert scan_jobs.sort_order == 9

    scan_jobs = scan_jobs.default()
    assert scan_jobs.session == 1
    assert scan_jobs.page is None
    assert scan_jobs.from_date is None
    assert scan_jobs.to_date is None
    assert scan_jobs.type is None
    assert scan_jobs.municipality_id is None
    assert scan_jobs.sort_by is None
    assert scan_jobs.sort_order is None


def test_scan_jobs_pagination(session):
    municipality_id = uuid4()
    MunicipalityCollection(session).add(
        id=municipality_id,
        name='Adlikon',
        bfs_number=21
    )

    scan_jobs = ScanJobCollection(session)

    assert scan_jobs.pages_count == 0
    assert scan_jobs.batch == []
    assert scan_jobs.page_index == 0
    assert scan_jobs.offset == 0
    assert scan_jobs.previous is None
    assert scan_jobs.next is None
    assert scan_jobs.page_by_index(0) == scan_jobs

    for day in range(1, 27):
        scan_jobs.add(
            type='express',
            dispatch_date=date(2019, 1, day),
            municipality_id=municipality_id,
        )

    scan_jobs = ScanJobCollection(session)
    assert scan_jobs.query().count() == 26
    assert scan_jobs.subset_count == 26
    assert scan_jobs.pages_count == 2
    assert len(scan_jobs.batch) == 20
    assert scan_jobs.page_index == 0
    assert scan_jobs.offset == 0
    assert scan_jobs.previous is None
    assert scan_jobs.next == scan_jobs.page_by_index(1)
    assert scan_jobs.page_by_index(0) == scan_jobs

    assert scan_jobs.next.page_index == 1
    assert len(scan_jobs.next.batch) == 6
    assert scan_jobs.next.previous == scan_jobs


def test_scan_jobs_query(session):
    municipalities = MunicipalityCollection(session)
    municipalities = {
        'Adlikon': municipalities.add(name='Adlikon', bfs_number=21),
        'Aesch': municipalities.add(name='Aesch', bfs_number=241)
    }

    def add(name, dispatch_date, type, dispatch_note, return_note):
        ScanJobCollection(session).add(
            dispatch_date=dispatch_date,
            type=type,
            municipality_id=municipalities[name].id,
            dispatch_note=dispatch_note,
            return_note=return_note,
        )

    add('Adlikon', date(2019, 1, 6), 'normal', None, 'bc')
    add('Adlikon', date(2019, 1, 5), 'express', 'abc', None)
    add('Adlikon', date(2019, 1, 4), 'express', '', '')
    add('Aesch', date(2019, 1, 4), 'normal', None, 'Lorem ipsum')
    add('Aesch', date(2019, 1, 3), 'express', 'Lorem Ipsum', None)
    add('Aesch', date(2019, 1, 2), 'express', None, 'loremipsum')

    def count(**kwargs):
        return ScanJobCollection(session, **kwargs).query().count()

    assert count() == 6

    assert count(from_date=date(2019, 1, 1)) == 6
    assert count(from_date=date(2019, 1, 2)) == 6
    assert count(from_date=date(2019, 1, 3)) == 5
    assert count(from_date=date(2019, 1, 5)) == 2
    assert count(from_date=date(2019, 1, 6)) == 1
    assert count(from_date=date(2019, 1, 7)) == 0

    assert count(to_date=date(2019, 1, 1)) == 0
    assert count(to_date=date(2019, 1, 2)) == 1
    assert count(to_date=date(2019, 1, 3)) == 2
    assert count(to_date=date(2019, 1, 5)) == 5
    assert count(to_date=date(2019, 1, 6)) == 6
    assert count(to_date=date(2019, 1, 7)) == 6

    assert count(from_date=date(2019, 1, 3), to_date=date(2019, 1, 4)) == 3
    assert count(from_date=date(2019, 1, 4), to_date=date(2019, 1, 3)) == 0

    assert count(type=[]) == 6
    assert count(type=['normal']) == 2
    assert count(type=['express']) == 4
    assert count(type=['normal', 'express']) == 6

    assert count(municipality_id=[]) == 6
    assert count(municipality_id=[municipalities['Adlikon'].id]) == 3
    assert count(municipality_id=[municipalities['Adlikon'].id,
                                  municipalities['Aesch'].id]) == 6

    assert count(term='abc') == 1
    assert count(term='bc') == 2
    assert count(term='C') == 2
    assert count(term='LOREM IPSUM') == 2
    assert count(term='ips') == 3

    assert count(
        municipality_id=[municipalities['Adlikon'].id],
        type=['express'],
        from_date=date(2019, 1, 4),
        term='a'
    ) == 1


def test_scan_jobs_order(session):
    for day, name in ((3, 'First'), (1, 'Śecond'), (2, 'Phirrrrd')):
        municipality = MunicipalityCollection(session).add(
            name=name,
            bfs_number=day,
        )
        ScanJobCollection(session).add(
            dispatch_date=date(2019, 1, day),
            type='normal',
            municipality_id=municipality.id,
        )

    def collection(sort_by=None, sort_order=None):
        return ScanJobCollection(
            session, sort_by=sort_by, sort_order=sort_order
        )

    scan_jobs = collection()
    assert scan_jobs.sort_order_by_key('dispatch_date') == 'descending'
    assert scan_jobs.sort_order_by_key('delivery_number') == 'unsorted'
    assert scan_jobs.sort_order_by_key('municipality_id') == 'unsorted'
    assert scan_jobs.sort_order_by_key('invalid') == 'unsorted'

    scan_jobs = collection('', '')
    assert scan_jobs.current_sort_by == 'dispatch_date'
    assert scan_jobs.current_sort_order == 'descending'

    scan_jobs = collection('xx', 'yy')
    assert scan_jobs.current_sort_by == 'dispatch_date'
    assert scan_jobs.current_sort_order == 'descending'

    scan_jobs = collection('dispatch_date', 'yy')
    assert scan_jobs.current_sort_by == 'dispatch_date'
    assert scan_jobs.current_sort_order == 'descending'

    scan_jobs = collection('xx', 'ascending')
    assert scan_jobs.current_sort_by == 'dispatch_date'
    assert scan_jobs.current_sort_order == 'descending'

    scan_jobs = collection('delivery_number', 'yy')
    assert scan_jobs.current_sort_by == 'delivery_number'
    assert scan_jobs.current_sort_order == 'ascending'

    scan_jobs = collection()
    assert scan_jobs.current_sort_by == 'dispatch_date'
    assert scan_jobs.current_sort_order == 'descending'
    assert 'dispatch_date' in str(scan_jobs.order_by)
    assert 'DESC' in str(scan_jobs.order_by)
    assert [s.dispatch_date.day for s in scan_jobs.query()] == [3, 2, 1]

    scan_jobs = scan_jobs.by_order('dispatch_date')
    assert scan_jobs.current_sort_by == 'dispatch_date'
    assert scan_jobs.current_sort_order == 'ascending'
    assert 'dispatch_date' in str(scan_jobs.order_by)
    assert [s.dispatch_date.day for s in scan_jobs.query()] == [1, 2, 3]

    scan_jobs = scan_jobs.by_order('delivery_number')
    assert scan_jobs.current_sort_by == 'delivery_number'
    assert scan_jobs.current_sort_order == 'ascending'
    assert 'delivery_number' in str(scan_jobs.order_by)
    assert [s.delivery_number for s in scan_jobs.query()] == [1, 2, 3]

    scan_jobs = scan_jobs.by_order('delivery_number')
    assert scan_jobs.current_sort_by == 'delivery_number'
    assert scan_jobs.current_sort_order == 'descending'
    assert 'delivery_number' in str(scan_jobs.order_by)
    assert 'DESC' in str(scan_jobs.order_by)
    assert [s.delivery_number for s in scan_jobs.query()] == [3, 2, 1]

    scan_jobs = scan_jobs.by_order('municipality_id')
    assert scan_jobs.current_sort_by == 'municipality_id'
    assert scan_jobs.current_sort_order == 'ascending'
    assert 'name' in str(scan_jobs.order_by)
    assert [s.municipality.name for s in scan_jobs.query()] == [
        'First', 'Phirrrrd', 'Śecond'
    ]

    scan_jobs = scan_jobs.by_order('municipality_id')
    assert scan_jobs.current_sort_by == 'municipality_id'
    assert scan_jobs.current_sort_order == 'descending'
    assert 'name' in str(scan_jobs.order_by)
    assert 'DESC' in str(scan_jobs.order_by)
    assert [s.municipality.name for s in scan_jobs.query()] == [
        'Śecond', 'Phirrrrd', 'First'
    ]

    scan_jobs = scan_jobs.by_order(None)
    assert scan_jobs.current_sort_by == 'dispatch_date'
    assert scan_jobs.current_sort_order == 'descending'

    scan_jobs = scan_jobs.by_order('')
    assert scan_jobs.current_sort_by == 'dispatch_date'
    assert scan_jobs.current_sort_order == 'descending'

    scan_jobs = scan_jobs.by_order('xxx')
    assert scan_jobs.current_sort_by == 'dispatch_date'
    assert scan_jobs.current_sort_order == 'descending'
