from onegov.feriennet.models.notification_template import TemplateVariables
from uuid import uuid4


def test_template_variables():

    class MockRequest(object):

        def translate(self, text):
            return text.upper()

        def link(self, obj, *args, **kwargs):
            return repr(obj)

        def class_link(self, cls, *args, **kwargs):
            return cls.__name__

    class MockPeriod(object):
        id = uuid4()
        title = 'Foobar Pass'

    t = TemplateVariables(MockRequest(), MockPeriod())

    assert sorted(t.bound.keys()) == [
        "[BOOKINGS]",
        "[INVOICES]",
        "[PERIOD]",
    ]

    assert t.render("Welcome to [PERIOD]") == "Welcome to Foobar Pass"
    assert t.render("Go to [INVOICES]") \
        == 'Go to <a href="InvoiceItemCollection">INVOICES</a>'
    assert t.render("Go to [BOOKINGS]") \
        == 'Go to <a href="BookingCollection">BOOKINGS</a>'
