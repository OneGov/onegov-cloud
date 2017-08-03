from onegov.activity import BookingCollection, InvoiceItemCollection
from onegov.feriennet.collections import VacationActivityCollection
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


def as_paragraphs(text):
    paragraph = []

    for line in text.splitlines():
        if line.strip() == '':
            if paragraph:
                yield '<p>{}</p>'.format('<br>'.join(paragraph))
                del paragraph[:]
        else:
            paragraph.append(line)

    if paragraph:
        yield '<p>{}</p>'.format('<br>'.join(paragraph))


class TemplateVariables(object):

    def __init__(self, request, period):
        self.request = request
        self.period = period

        self.bound = {}
        self.bind(
            _("Period"),
            _("Title of the period."),
            self.period_title,
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
        self.bind(
            _("Activities"),
            _("Link to the activities."),
            self.activities_link
        )
        self.bind(
            _("Homepage"),
            _("Link to the homepage."),
            self.homepage_link
        )

    def bind(self, name, description, method):
        token = TOKEN.format(self.request.translate(name))
        method.__func__.__doc__ = self.request.translate(description)
        self.bound[token] = method

    def render(self, text):
        for token, method in self.bound.items():
            if token in text:
                text = text.replace(token, method())

        paragraphs = tuple(as_paragraphs(text))

        if len(paragraphs) <= 1:
            return text
        else:
            return '\n'.join(as_paragraphs(text))

    def period_title(self):
        return self.period.title

    def bookings_link(self):
        return '<a href="{}">{}</a>'.format(
            self.request.class_link(BookingCollection, {
                'period_id': self.period.id
            }),
            self.request.translate(_("Bookings"))
        )

    def invoices_link(self):
        return '<a href="{}">{}</a>'.format(
            self.request.class_link(InvoiceItemCollection),
            self.request.translate(_("Invoices"))
        )

    def activities_link(self):
        return '<a href="{}">{}</a>'.format(
            self.request.class_link(VacationActivityCollection),
            self.request.translate(_("Activities"))
        )

    def homepage_link(self):
        return '<a href="{}">{}</a>'.format(
            self.request.link(self.request.app.org),
            self.request.translate(_("Homepage"))
        )
