import re

from onegov.activity import BookingCollection, InvoiceCollection
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID, UTCDateTime
from onegov.feriennet import _
from onegov.feriennet.collections import VacationActivityCollection
from onegov.file import File
from onegov.file.utils import name_without_extension
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
        self.expanded = {}

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
            result = text
        else:
            result = '\n'.join(as_paragraphs(text))

        return self.expand_storage_links(result)

    def expand_storage_links(self, text):
        """ Searches the text for storage links /storage/0w8dj98rgn93... and
        uses the title of the referenced files to improve the readability of
        the link.

        """

        ex = self.request.class_link(File, {'id': '0xdeadbeef'})
        ex = ex.replace('0xdeadbeef', r'(?P<id>[0-9A-Za-z]+)')

        def expand(match):
            return self.expand_with_cache(match, match.group('id'))

        return re.sub(ex, expand, text)

    def expand_with_cache(self, match, id):

        if id not in self.expanded:
            record = self.request.session.query(File)\
                .with_entities(File.name)\
                .filter_by(id=match.group('id'))\
                .first()

            if record:
                name = name_without_extension(record.name)
                self.expanded[id] = f'<a href="{match.group()}">{name}</a>'
            else:
                self.expanded[id] = match.group()

        return self.expanded[id]

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
            self.request.class_link(InvoiceCollection),
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
