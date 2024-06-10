from datetime import timedelta, date

from freezegun import freeze_time
from sedate import utcnow

from onegov.core.utils import Bunch
from onegov.feriennet.models.notification_template import TemplateVariables
from uuid import uuid4


class MockRequest:

    def __repr__(self):
        return 'MockRequest'

    def translate(self, text):
        return text.upper()

    def link(self, obj, *args, **kwargs):
        return repr(obj)

    def class_link(self, cls, *args, **kwargs):
        return cls.__name__

    @property
    def app(self):
        return Bunch(org=self)


class MockPeriod:
    id = uuid4()
    title = 'Foobar Pass'


def test_template_variables():

    t = TemplateVariables(MockRequest(), MockPeriod())

    assert sorted(t.bound.keys()) == [
        "[ACTIVITIES]",
        "[BOOKINGS]",
        "[HOMEPAGE]",
        "[INVOICES]",
        "[PERIOD]",
    ]

    assert t.render("Welcome to [PERIOD]") == "Welcome to Foobar Pass"
    assert t.render("Go to [INVOICES]") \
        == 'Go to <a href="InvoiceCollection">INVOICES</a>'
    assert t.render("Go to [BOOKINGS]") \
        == 'Go to <a href="BookingCollection">BOOKINGS</a>'
    assert t.render("Go to [ACTIVITIES]") \
        == 'Go to <a href="VacationActivityCollection">ACTIVITIES</a>'
    assert t.render("Go to [HOMEPAGE]") \
        == 'Go to <a href="MockRequest">HOMEPAGE</a>'


def test_template_rendering_link():
    t = TemplateVariables(MockRequest(), MockPeriod())

    # test allowed tags <p>, <br>
    text = ("<p>Peter Piper picked a peck of pickled peppers.<br>"
            "A peck of pickled peppers Peter Piper picked.</p>")
    assert t.render(text) == text

    # test allowed tag <a>, attribute href
    text = """
    This is a link to <a href="https://github.com/OneGov/onegov-cloud">
    onegov-cloud</a> on github.
    """
    assert t.render(text) == text

    # test allowed tag <mailto>, <tel> tags
    text = """<a href="mailto:example@example.com">Send Email</a><br>
    <a href="tel:+41791234567">Call Me</a>"""
    assert t.render(text) == text

    text = "<strong>Bold text</strong>"
    assert t.render(text) == '&lt;strong&gt;Bold text&lt;/strong&gt;'

    # test malicious tag script being escaped
    text = "<script>alert('html injection')</script>"
    assert t.render(text) == ("&lt;script&gt;alert('html "
                              "injection')&lt;/script&gt;")


def test_period(scenario):
    scenario.add_period()
    scenario.commit()
    scenario.refresh()

    period = scenario.latest_period
    prebook = period.prebooking_start
    prebook_end = period.prebooking_end

    def local_(date):
        return period.as_local_datetime(date)

    midnight = local_(prebook)

    with freeze_time(midnight):
        # We can see that the timezone already comes to play here leading
        # to a bug that cost one persons sleep
        assert local_(date.today()) != midnight
        # so we replaced it with utcnow() to fix the error
        assert utcnow() == midnight
        assert period.phase == 'wishlist'
        assert period.is_currently_prebooking

    with freeze_time(midnight - timedelta(minutes=1)):
        assert period.phase == 'inactive'
        assert not period.wishlist_phase
        assert not period.is_currently_prebooking

    with freeze_time(local_(prebook_end) + timedelta(hours=23, minutes=59)):
        assert period.phase == 'wishlist'
        assert period.wishlist_phase
        assert period.is_currently_prebooking
        assert not period.is_prebooking_in_past

    with freeze_time(local_(prebook_end) + timedelta(days=1)):
        assert not period.is_currently_prebooking
        assert period.is_prebooking_in_past

    # exactly midnight in the chosen timezone
    with freeze_time(local_(prebook_end)):
        assert period.wishlist_phase
        assert period.is_currently_prebooking
        assert not period.is_prebooking_in_past
