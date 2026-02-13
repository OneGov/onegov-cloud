from __future__ import annotations

from functools import cached_property
from onegov.activity import Activity, BookingPeriodCollection, Occasion
from onegov.activity import BookingCollection
from onegov.core.elements import Link, Confirm, Intercooler, Block
from onegov.core.elements import LinkGroup
from onegov.core.utils import linkify, paragraphify
from onegov.feriennet import _
from onegov.feriennet import security
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.collections import OccasionAttendeeCollection
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.const import OWNER_EDITABLE_STATES
from onegov.feriennet.models import InvoiceAction, VacationActivity
from onegov.pay import PaymentProviderCollection
from onegov.ticket import TicketCollection
from onegov.town6.layout import DefaultLayout as BaseLayout
from onegov.town6.layout import UserLayout as TownUserLayout
from onegov.user.collections.user import UserCollection
from sqlalchemy import text


from typing import Any, NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from markupsafe import Markup
    from onegov.activity.models import (
        Attendee, Booking, BookingPeriod, PublicationRequest)
    from onegov.activity.collections import (
        BookingPeriodInvoiceCollection, VolunteerCollection)
    from onegov.core.elements import Trait
    from onegov.feriennet.app import FeriennetApp
    from onegov.feriennet.models import NotificationTemplate
    from onegov.feriennet.request import FeriennetRequest
    from onegov.org.models import Organisation
    from onegov.ticket import Ticket
    from onegov.user import User

    class ActivityRow:
        title: str
        name: str


class DefaultLayout(BaseLayout):

    app: FeriennetApp
    request: FeriennetRequest

    @property
    def is_owner(self) -> bool:
        if not self.request.current_username:
            return False
        return security.is_owner(self.request.current_username, self.model)

    @property
    def is_editable(self) -> bool:
        if self.request.is_admin:
            return True

        if not self.request.is_organiser:
            return False

        if isinstance(self.model, Activity):
            return self.model.state in OWNER_EDITABLE_STATES

        if isinstance(self.model, Occasion):
            return self.model.activity.state in OWNER_EDITABLE_STATES

        return True

    def offer_again_link(
        self,
        activity: VacationActivity | ActivityRow,
        title: str
    ) -> Link:
        return Link(
            text=title,
            url=self.request.class_link(
                VacationActivity,
                {'name': activity.name},
                name='offer-again'
            ),
            traits=(
                Confirm(
                    _(
                        'Do you really want to provide "${title}" again?',
                        mapping={'title': activity.title}
                    ),
                    _('You will have to request publication again'),
                    _('Provide Again'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='POST',
                    redirect_after=self.request.class_link(
                        VacationActivity, {'name': activity.name},
                    )
                )
            ),
            attrs={'class': 'offer-again'}
        )

    def linkify(self, text: str | None) -> Markup:  # type:ignore[override]
        return linkify(text)

    def paragraphify(self, text: str) -> Markup:
        return paragraphify(text)


class VacationActivityCollectionLayout(DefaultLayout):

    model: VacationActivityCollection

    if TYPE_CHECKING:
        def __init__(
            self,
            model: VacationActivityCollection,
            request: FeriennetRequest
        ) -> None: ...

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Activities'), self.request.class_link(
                VacationActivityCollection)),
        ]

    @property
    def organiser_links(self) -> Iterator[Link | LinkGroup]:
        if self.app.active_period:
            yield Link(
                text=_('Submit Activity'),
                url=self.request.link(self.model, name='new'),
                attrs={'class': 'new-activity'}
            )

            link_group = self.offer_again_links
            if link_group is not None:
                yield link_group

    @property
    def offer_again_links(self) -> LinkGroup | None:
        activities: tuple[ActivityRow, ...] = tuple(
            self.app.session().query(VacationActivity)  # type: ignore[arg-type]
            .with_entities(
                VacationActivity.title,
                VacationActivity.name,
            )
            .filter_by(username=self.request.current_username)
            .filter_by(state='archived')
            .order_by(VacationActivity.order)
        )

        if activities:
            return LinkGroup(
                _('Provide activity again'),
                tuple(self.offer_again_link(a, a.title) for a in activities),
                right_side=False,
                classes=('provide-activity-again', )
            )
        return None

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if not self.request.is_organiser:
            return None

        return list(self.organiser_links)


class BookingCollectionLayout(DefaultLayout):

    model: BookingCollection

    def __init__(
        self,
        model: BookingCollection,
        request: FeriennetRequest,
        user: User | None = None
    ) -> None:
        super().__init__(model, request)
        if user is None:
            user = request.current_user
            assert user is not None
        self.user = user

    def rega_link(
        self,
        attendee: Attendee | None,
        period: BookingPeriod | None,
        grouped_bookings: dict[Attendee, dict[str, list[Booking]]]
    ) -> str | None:

        if not (period or attendee or grouped_bookings):
            return None

        if self.request.app.org.meta['locales'] == 'de_CH':
            return ('https://www.rega.ch/partner/'
                    'das-pro-juventute-engagement-der-rega')
        if self.request.app.org.meta['locales'] == 'it_CH':
            return ('https://www.rega.ch/it/partner/'
                    'limpegno-pro-juventute-della-rega')
        return ('https://www.rega.ch/fr/partenariats/'
                'lengagement-de-la-rega-en-faveur-de-pro-juventute')

    @cached_property
    def title(self) -> str:
        wishlist_phase = (self.app.active_period
                          and self.app.active_period.wishlist_phase)

        if self.user.username == self.request.current_username:
            return wishlist_phase and _('Wishlist') or _('Bookings')
        elif wishlist_phase:
            return _('Wishlist of ${user}', mapping={
                'user': self.user.title
            })
        else:
            return _('Bookings of ${user}', mapping={
                'user': self.user.title
            })

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(self.title, self.request.link(self.model))
        ]


class GroupInviteLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        wishlist_phase = (self.app.active_period
                          and self.app.active_period.wishlist_phase)

        if self.request.is_logged_in:
            return [
                Link(_('Homepage'), self.homepage_url),
                Link(
                    wishlist_phase and _('Wishlist') or _('Bookings'),
                    self.request.class_link(BookingCollection)
                ),
                Link(_('Group'), '#')
            ]
        else:
            return [
                Link(_('Homepage'), self.homepage_url),
                Link(_('Group'), '#')
            ]


class VacationActivityFormLayout(DefaultLayout):

    model: VacationActivity | VacationActivityCollection

    def __init__(
        self,
        model: VacationActivity | VacationActivityCollection,
        request: FeriennetRequest,
        title: str
    ) -> None:

        super().__init__(model, request)
        self.include_editor()
        self.title = title

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            # FIXME: This breadcrumb seems wrong for VacationActivity
            Link(_('Activities'), self.request.link(self.model)),
            Link(self.title, '#')
        ]

    @cached_property
    def editbar_links(self) -> None:
        return None


class OccasionFormLayout(DefaultLayout):

    model: Activity

    def __init__(
        self,
        model: Activity,
        request: FeriennetRequest,
        title: str
    ) -> None:

        assert isinstance(model, Activity)
        super().__init__(model, request)
        self.title = title

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Activities'), self.request.class_link(
                VacationActivityCollection)),
            Link(self.model.title, self.request.link(self.model)),
            Link(self.title, '#')
        ]


class VacationActivityLayout(DefaultLayout):

    model: VacationActivity

    if TYPE_CHECKING:
        def __init__(
            self,
            model: VacationActivity,
            request: FeriennetRequest
        ) -> None: ...

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Activities'), self.request.class_link(
                VacationActivityCollection)),
            Link(self.model.title, self.request.link(self.model))
        ]

    @cached_property
    def latest_request(self) -> PublicationRequest | None:
        return self.model.latest_request

    @cached_property
    def ticket(self) -> Ticket | None:
        if self.latest_request:
            tickets = TicketCollection(self.request.session)
            return tickets.by_handler_id(self.latest_request.id.hex)
        return None

    @cached_property
    def attendees(self) -> OccasionAttendeeCollection | None:
        if self.request.app.default_period:
            return OccasionAttendeeCollection(
                self.request.session,
                self.request.app.default_period,
                self.model
            )
        return None

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        links: list[Link | LinkGroup] = []
        period = self.request.app.active_period

        if self.request.is_admin or self.is_owner:
            if self.model.state == 'archived' and period:
                links.append(
                    self.offer_again_link(self.model, _('Provide Again')))

        if self.is_editable:

            if self.model.state == 'preview':
                if not period:
                    links.append(Link(
                        text=_('Request Publication'),
                        url='#',
                        attrs={'class': 'request-publication'},
                        traits=(
                            Block(
                                _(
                                    'There is currently no active period. '
                                    'Please retry once a period has been '
                                    'activated.'
                                ),
                                no=_('Cancel')
                            ),
                        )
                    ))
                elif self.model.has_occasion_in_period(period):
                    links.append(Link(
                        text=_('Request Publication'),
                        url=self.request.link(self.model, name='propose'),
                        attrs={'class': 'request-publication'},
                        traits=(
                            Confirm(
                                _(
                                    'Do you really want to request '
                                    'publication?'
                                ),
                                _('This cannot be undone.'),
                                _('Request Publication')
                            ),
                            Intercooler(
                                request_method='POST',
                                redirect_after=self.request.link(self.model)
                            )
                        )
                    ))
                else:
                    links.append(Link(
                        text=_('Request Publication'),
                        url='#',
                        attrs={'class': 'request-publication'},
                        traits=(
                            Block(
                                _(
                                    'Please add at least one occasion '
                                    'before requesting publication.'
                                ),
                                no=_('Cancel')
                            ),
                        )
                    ))

                if not self.model.publication_requests:
                    links.append(Link(
                        text=_('Discard'),
                        url=self.csrf_protected_url(
                            self.request.link(self.model)
                        ),
                        attrs={'class': 'delete-link'},
                        traits=(
                            Confirm(_(
                                'Do you really want to discard "${title}"?',
                                mapping={'title': self.model.title}
                            ), _(
                                'This cannot be undone.'
                            ), _(
                                'Discard Activity'
                            ), _(
                                'Cancel')
                            ),
                            Intercooler(
                                request_method='DELETE',
                                redirect_after=self.request.class_link(
                                    VacationActivityCollection
                                )
                            )
                        )
                    ))

            links.append(Link(
                text=_('Edit'),
                url=self.request.link(self.model, name='edit'),
                attrs={'class': 'edit-link'}
            ))

            if not self.request.app.periods:
                links.append(Link(
                    text=_('New Occasion'),
                    url='#',
                    attrs={'class': 'new-occasion'},
                    traits=(
                        Block(
                            _('Occasions cannot be created yet'),
                            _(
                                'There are no periods defined yet. At least '
                                'one period needs to be defined before '
                                'occasions can be created.'
                            ),
                            _('Cancel')
                        )
                    )
                ))
            else:
                links.append(Link(
                    text=_('New Occasion'),
                    url=self.request.link(self.model, 'new-occasion'),
                    attrs={'class': 'new-occasion'}
                ))

        if self.request.is_admin or self.is_owner:
            if self.attendees:
                links.append(Link(
                    text=_('Attendees'),
                    url=self.request.link(self.attendees),
                    attrs={'class': 'show-attendees'}
                ))

        if self.request.is_admin:
            if self.model.state != 'preview' and self.ticket:
                links.append(Link(
                    text=_('Show Ticket'),
                    url=self.request.link(self.ticket),
                    attrs={'class': 'show-ticket'}
                ))

        return links


class PeriodCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Activities'),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(_('Manage Periods'), '#')
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        return [
            Link(
                _('New Period'),
                self.request.class_link(BookingPeriodCollection, name='new'),
                attrs={'class': 'new-period'}
            ),
        ]


class PeriodFormLayout(DefaultLayout):

    model: BookingPeriod | BookingPeriodCollection

    def __init__(
        self,
        model: BookingPeriod | BookingPeriodCollection,
        request: FeriennetRequest,
        title: str
    ) -> None:
        super().__init__(model, request)
        self.title = title

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Activities'),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(
                _('Manage Periods'),
                self.request.class_link(BookingPeriodCollection)
            ),
            Link(self.title, '#')
        ]

    @cached_property
    def editbar_links(self) -> None:
        return None


class MatchCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Activities'),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(_('Matches'), '#')
        ]


class BillingCollectionLayout(DefaultLayout):

    model: BillingCollection

    if TYPE_CHECKING:
        def __init__(
            self,
            model: BillingCollection,
            request: FeriennetRequest
        ) -> None: ...

    class FamilyRow(NamedTuple):
        text: str
        item: str
        count: int  # type:ignore[assignment]
        has_online_payments: bool

    @property
    def families(self) -> Iterator[FamilyRow]:
        yield from self.app.session().execute(text("""
            SELECT
                text
                    || ' ('
                    || replace(avg(unit * quantity)::money::text, '$', '')
                    || ' CHF)'
                AS text
                ,
                MIN(id::text) AS item,
                COUNT(*) AS count,
                family IN (
                    SELECT DISTINCT(family)
                    FROM invoice_items
                    WHERE source IS NOT NULL and source != 'xml'
                ) AS has_online_payments
            FROM invoice_items
            WHERE family IS NOT NULL
            GROUP BY family, text
            ORDER BY text
        """)).tuples()

    @property
    def family_removal_links(self) -> Iterator[Link]:
        attrs = {
            'class': ('remove-manual', 'extend-to-family')
        }

        for record in self.families:
            text = _('Delete "${text}"', mapping={
                'text': record.text,
            })

            url = self.csrf_protected_url(
                self.request.class_link(InvoiceAction, {
                    'id': record.item,
                    'action': 'remove-manual',
                    'extend_to': 'family'
                })
            )

            traits: Sequence[Trait]
            if record.has_online_payments:
                traits = (
                    Block(
                        _(
                            'This booking cannot be removed, at least one '
                            'booking has been paid online.'
                        ),
                        _(
                            'You may remove the bookings manually one by one.'
                        ),
                        _('Cancel')
                    ),
                )
            else:
                traits = (
                    Confirm(
                        _('Do you really want to remove "${text}"?', mapping={
                            'text': record.text
                        }),
                        _('${count} bookings will be removed', mapping={
                            'count': record.count
                        }),
                        _('Remove ${count} bookings', mapping={
                            'count': record.count
                        }),
                        _('Cancel')
                    ),
                    Intercooler(request_method='POST')
                )

            yield Link(text=text, url=url, attrs=attrs, traits=traits)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Activities'),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(_('Billing'), '#')
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        return [
            Link(
                _('Import Bank Statement'),
                self.request.link(self.model, 'import'),
                attrs={'class': 'import'}
            ),
            Link(
                _('Synchronise Online Payments'),
                self.request.return_here(
                    self.request.class_link(
                        PaymentProviderCollection, name='sync')),
                attrs={'class': 'sync'},
            ),
            LinkGroup(
                title=_('Accounting'),
                links=[
                    Link(
                        text=_('Manual Booking'),
                        url=self.request.link(
                            self.model,
                            name='booking'
                        ),
                        attrs={'class': 'new-booking'},
                        traits=(
                            Block(_(
                                'Manual bookings can only be added '
                                'once the billing has been confirmed.'
                            ), no=_('Cancel')),
                        ) if not self.model.period.finalized else ()
                    ),
                    *self.family_removal_links
                ]
            )
        ]


class OnlinePaymentsLayout(DefaultLayout):

    def __init__(
        self,
        model: Any,
        request: FeriennetRequest,
        title: str
    ) -> None:

        self.title = title
        super().__init__(model, request)

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        return [
            Link(
                _('Synchronise Online Payments'),
                self.request.return_here(
                    self.request.class_link(
                        PaymentProviderCollection, name='sync')),
                attrs={'class': 'sync'},
            ),
        ]

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Activities'),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(
                _('Billing'),
                self.request.class_link(BillingCollection)
            ),
            Link(self.title, '#')
        ]


class BillingCollectionImportLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Activities'),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(_('Billing'), self.request.link(self.model)),
            Link(_('Import Bank Statement'), '#')
        ]


class BillingCollectionManualBookingLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Activities'),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(_('Billing'), self.request.link(self.model)),
            Link(_('Manual Booking'), '#')
        ]


class BillingCollectionPaymentWithDateLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Activities'),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(_('Billing'), self.request.link(self.model)),
            Link(_('Payment with date'), '#')
        ]


class InvoiceLayout(DefaultLayout):

    def __init__(
        self,
        model: Any,
        request: FeriennetRequest,
        title: str
    ) -> None:
        super().__init__(model, request)
        self.title = title

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(self.title, '#')
        ]


class DonationLayout(DefaultLayout):

    def __init__(
        self,
        model: BookingPeriodInvoiceCollection,
        request: FeriennetRequest,
        title: str
    ) -> None:
        super().__init__(model, request)
        self.title = title

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Invoices'), self.request.link(self.model)),
            Link(_('Donation'), self.title)
        ]


class OccasionAttendeeLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Activities'),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(
                self.model.activity.title,
                self.request.link(self.model.activity)
            ),
            Link(_('Attendees'), '#')
        ]


class NotificationTemplateCollectionLayout(DefaultLayout):

    model: NotificationTemplateCollection

    def __init__(
        self,
        model: NotificationTemplateCollection,
        request: FeriennetRequest,
        subtitle: str | None = None
    ) -> None:
        super().__init__(model, request)
        self.subtitle = subtitle
        self.include_editor()

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Activities'),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(
                _('Notification Templates'),
                self.request.class_link(NotificationTemplateCollection)
            )
        ]

        if self.subtitle:
            links.append(Link(self.subtitle, '#'))

        return links

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if not self.subtitle:
            return [
                Link(
                    _('New Notification Template'),
                    self.request.link(self.model, 'new'),
                    attrs={'class': 'new-notification'}
                ),
            ]
        return None


class NotificationTemplateLayout(DefaultLayout):

    model: NotificationTemplate

    def __init__(
        self,
        model: NotificationTemplate,
        request: FeriennetRequest,
        subtitle: str | None = None
    ) -> None:
        super().__init__(model, request)
        self.subtitle = subtitle
        self.include_editor()

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Activities'),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(
                _('Notification Templates'),
                self.request.class_link(NotificationTemplateCollection)
            ),
            Link(
                self.model.subject,
                self.request.link(self.model)
            )
        ]

        if self.subtitle:
            links.append(Link(self.subtitle, '#'))

        return links


class VolunteerLayout(DefaultLayout):

    model: VolunteerCollection

    if TYPE_CHECKING:
        def __init__(
            self,
            model: VolunteerCollection,
            request: FeriennetRequest
        ) -> None: ...

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Volunteers'), self.request.link(self.model))
        ]


class VolunteerFormLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Join as a Volunteer'),
                self.request.class_link(
                    VacationActivityCollection, name='volunteer'
                )
            ),
            Link(
                _('Register as Volunteer'),
                '#'
            )
        ]


class HomepageLayout(DefaultLayout):

    model: Organisation

    if TYPE_CHECKING:
        def __init__(
            self,
            model: Organisation,
            request: FeriennetRequest
        ) -> None: ...

    @property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    _('Sort'),
                    self.request.link(self.model, 'sort'),
                    attrs={'class': ('sort-link')}
                )
            ]
        return None


class UserLayout(TownUserLayout):

    model: User

    if TYPE_CHECKING:
        def __init__(
            self,
            model: User,
            request: FeriennetRequest
        ) -> None: ...

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        links: list[Link | LinkGroup] = []
        if self.request.is_admin and not self.model.source:
            links.append(
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                )
            )

            if self.model.role != 'admin':
                links.append(Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete this user?'),
                            _('This cannot be undone.'),
                            _('Delete user'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.class_link(
                                UserCollection)
                        )
                    )
                ))
            return links
        return None
