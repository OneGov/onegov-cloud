from __future__ import annotations

from datetime import datetime
from markupsafe import Markup
from onegov.activity import BookingCollection, BookingPeriodInvoiceCollection
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.feriennet import _
from onegov.feriennet.collections import VacationActivityCollection
from sqlalchemy.orm import mapped_column, Mapped
from uuid import uuid4, UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.activity.models import BookingPeriod
    from onegov.feriennet.request import FeriennetRequest
    from typing import Protocol
    from typing import Self

    class BoundCallable(Protocol):
        __doc__: str

        def __call__(self) -> str: ...


MISSING = object()
TOKEN = '[{}]'  # nosec: B105


class NotificationTemplate(Base, ContentMixin, TimestampMixin):

    __tablename__ = 'notification_templates'

    if TYPE_CHECKING:
        # NOTE: We don't want this to end up in __annotations__
        #       since it should not be mapped by SQLAlchemy
        period_id: UUID | None

    #: holds the selected period id (not stored in the database)
    period_id = None

    #: The public id of the notification template
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The subject of the notification
    subject: Mapped[str] = mapped_column(unique=True)

    # FIXME: Should this be annotated as `Markup` instead?
    #: The template text in html, fully rendered html content
    text: Mapped[str]

    #: The date the notification was last sent
    last_sent: Mapped[datetime | None]

    def for_period(self, period: BookingPeriod) -> Self:
        """ Implements the required interface for the 'periods' macro in
        onegov.feriennet.

        """
        self.period_id = period.id
        return self


class TemplateVariables:

    bound: dict[str, BoundCallable]
    expanded: dict[str, str]

    def __init__(
        self,
        request: FeriennetRequest,
        period: BookingPeriod | None
    ) -> None:
        self.request = request
        self.period = period
        self.expanded = {}

        self.bound = {}
        self.bind(
            _('Period'),
            _('Title of the period.'),
            self.period_title,
        )
        self.bind(
            _('Invoices'),
            _("Link to the user's invoices."),
            self.invoices_link,
        )
        self.bind(
            _('Bookings'),
            _("Link to the user's bookings."),
            self.bookings_link
        )
        self.bind(
            _('Activities'),
            _('Link to the activities.'),
            self.activities_link
        )
        self.bind(
            _('Homepage'),
            _('Link to the homepage.'),
            self.homepage_link
        )

    def bind(
        self,
        name: str,
        description: str,
        method: Callable[[], str]
    ) -> None:

        assert hasattr(method, '__func__')
        token = TOKEN.format(self.request.translate(name))
        method.__func__.__doc__ = self.request.translate(description)
        self.bound[token] = method

    def render(self, text: Markup) -> Markup:
        """
        Replaces the tokens with the corresponding internal links.

        """
        for token, method in self.bound.items():
            if token in text:
                text = text.replace(token, method())

        return text

    def period_title(self) -> str:
        return self.period.title if self.period else ''

    def bookings_link(self) -> Markup:
        return Markup('<a href="{}">{}</a>').format(
            self.request.class_link(BookingCollection, {
                'period_id': self.period.id if self.period else None
            }),
            self.request.translate(_('Bookings'))
        )

    def invoices_link(self) -> Markup:
        return Markup('<a href="{}">{}</a>').format(
            self.request.class_link(BookingPeriodInvoiceCollection),
            self.request.translate(_('Invoices'))
        )

    def activities_link(self) -> Markup:
        return Markup('<a href="{}">{}</a>').format(
            self.request.class_link(VacationActivityCollection),
            self.request.translate(_('Activities'))
        )

    def homepage_link(self) -> Markup:
        return Markup('<a href="{}">{}</a>').format(
            self.request.link(self.request.app.org),
            self.request.translate(_('Homepage'))
        )
