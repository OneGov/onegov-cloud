from onegov.activity import BookingCollection, InvoiceItemCollection
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID, UTCDateTime
from onegov.feriennet import _
from sqlalchemy import Column, Text
from uuid import uuid4


MISSING = object()
TOKEN = '[{}]'


class NotificationTemplate(Base, ContentMixin, TimestampMixin):

    __tablename__ = 'notification_templates'

    #: The public id of the notification template
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The subject of the notification
    subject = Column(Text, nullable=False, unique=True)

    #: The template text
    text = Column(Text, nullable=False)

    #: The date the notification was last sent
    last_sent = Column(UTCDateTime, nullable=True)


class TemplateVariables(object):

    def __init__(self, request, period):
        self.request = request
        self.period = period

        self.bound = {}
        self.bind(
            _("Period"),
            _("Title of the period."),
            self.pass_title,
        )
        self.bind(
            _("Invoices"),
            _("Link to the user's invoices."),
            self.invoices_link,
        )
        self.bind(
            _("Bookings"),
            _("Link to the user's bookings."),
            self.bookings_link
        )

    def bind(self, name, description, method):
        token = TOKEN.format(self.request.translate(name))
        method.__func__.__doc__ = self.request.translate(description)
        self.bound[token] = method

    def render(self, text):
        for token, method in self.bound.items():
            if token in text:
                text = text.replace(token, method())

        return text

    def pass_title(self):
        return self.period.title

    def bookings_link(self):
        return self.request.class_link(BookingCollection, {
            'period_id': self.period.id
        })

    def invoices_link(self):
        return self.request.class_link(InvoiceItemCollection)
