from cached_property import cached_property
from onegov.activity import Activity, PeriodCollection, Occasion
from onegov.feriennet import _
from onegov.feriennet import security
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.collections import OccasionAttendeeCollection
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.const import OWNER_EDITABLE_STATES
from onegov.feriennet.models import InvoiceAction, VacationActivity
from onegov.org.new_elements import Link, Confirm, Intercooler, Block
from onegov.org.new_elements import LinkGroup
from onegov.org.layout import DefaultLayout as BaseLayout
from onegov.pay import PaymentProviderCollection
from onegov.ticket import TicketCollection


class DefaultLayout(BaseLayout):

    @property
    def is_owner(self):
        return security.is_owner(self.request.current_username, self.model)

    @property
    def is_editable(self):
        if self.request.is_admin:
            return True

        if not self.request.is_organiser:
            return False

        if isinstance(self.model, Activity):
            return self.model.state in OWNER_EDITABLE_STATES

        if isinstance(self.model, Occasion):
            return self.model.activity.state in OWNER_EDITABLE_STATES

        return True

    def offer_again_link(self, activity, title):
        return Link(
            text=title,
            url=self.request.class_link(
                VacationActivity,
                {'name': activity.name},
                name="offer-again"
            ),
            traits=(
                Confirm(
                    _(
                        'Do you really want to provide "${title}" again?',
                        mapping={'title': activity.title}
                    ),
                    _("You will have to request publication again"),
                    _("Provide Again")
                ),
                Intercooler(
                    request_method="POST",
                    redirect_after=self.request.class_link(
                        VacationActivity, {'name': activity.name},
                    )
                )
            ),
            attrs={'class': 'offer-again'}
        )


class VacationActivityCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Activities"), self.request.class_link(
                VacationActivityCollection)),
        ]

    @property
    def organiser_links(self):
        yield Link(
            text=_("Submit Activity"),
            url=self.request.link(self.model, name='new'),
            attrs={'class': 'new-activity'}
        )

        yield self.offer_again_links

    @property
    def offer_again_links(self):
        q = self.app.session().query(VacationActivity)
        q = q.filter_by(username=self.request.current_username)
        q = q.filter_by(state='archived')
        q = q.with_entities(
            VacationActivity.title,
            VacationActivity.name,
        )
        q = q.order_by(VacationActivity.order)

        activities = tuple(q)

        if activities:
            return LinkGroup(
                _("Provide activity again"),
                tuple(self.offer_again_link(a, a.title) for a in activities),
                right_side=False,
                classes=('provide-activity-again', )
            )

    @cached_property
    def editbar_links(self):
        if not self.request.is_organiser:
            return None

        links = []

        if self.request.is_organiser:
            links.extend(self.organiser_links)

        return links


class BookingCollectionLayout(DefaultLayout):

    def __init__(self, model, request, user=None):
        super().__init__(model, request)
        self.user = user or request.current_user

    @cached_property
    def title(self):
        wishlist_phase = self.app.active_period \
            and self.app.active_period.wishlist_phase

        if self.user.username == self.request.current_username:
            return wishlist_phase and _("Wishlist") or _("Bookings")
        elif wishlist_phase:
            return _("Wishlist of ${user}", mapping={
                'user': self.user.title
            })
        else:
            return _("Bookings of ${user}", mapping={
                'user': self.user.title
            })

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, self.request.link(self.model))
        ]


class VacationActivityFormLayout(DefaultLayout):

    def __init__(self, model, request, title):
        super().__init__(model, request)
        self.include_editor()
        self.title = title

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(_("Activities"), self.request.link(self.model)),
            Link(self.title, '#')
        )

    @cached_property
    def editbar_links(self):
        return None


class OccasionFormLayout(DefaultLayout):

    def __init__(self, model, request, title):
        assert isinstance(model, Activity)

        super().__init__(model, request)
        self.title = title

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(_("Activities"), self.request.class_link(
                VacationActivityCollection)),
            Link(self.model.title, self.request.link(self.model)),
            Link(self.title, '#')
        )

    @cached_property
    def editbar_links(self):
        return None


class VacationActivityLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(_("Activities"), self.request.class_link(
                VacationActivityCollection)),
            Link(self.model.title, self.request.link(self.model))
        )

    @cached_property
    def latest_request(self):
        return self.model.latest_request

    @cached_property
    def ticket(self):
        if self.latest_request:
            tickets = TicketCollection(self.request.session)
            return tickets.by_handler_id(self.latest_request.id.hex)

    @cached_property
    def attendees(self):
        if self.request.app.default_period:
            return OccasionAttendeeCollection(
                self.request.session,
                self.request.app.default_period,
                self.model
            )

    @cached_property
    def editbar_links(self):
        links = []
        period = self.request.app.active_period

        if self.request.is_admin or self.is_owner:
            if self.model.state == 'archived' and period:
                links.append(
                    self.offer_again_link(self.model, _("Provide Again")))

        if self.is_editable:

            if self.model.state == 'preview':
                if period and self.model.has_occasion_in_period(period):
                    links.append(Link(
                        text=_("Request Publication"),
                        url=self.request.link(self.model, name='propose'),
                        attrs={'class': 'request-publication'},
                        traits=(
                            Confirm(
                                _(
                                    "Do you really want to request "
                                    "publication?"
                                ),
                                _("This cannot be undone."),
                                _("Request Publication")
                            ),
                            Intercooler(
                                request_method="POST",
                                redirect_after=self.request.link(self.model)
                            )
                        )
                    ))
                else:
                    links.append(Link(
                        text=_("Request Publication"),
                        url='#',
                        attrs={'class': 'request-publication'},
                        traits=(
                            Block(
                                _(
                                    "Please add at least one occasion "
                                    "before requesting publication."
                                )
                            ),
                        )
                    ))

                if not self.model.publication_requests:
                    links.append(Link(
                        text=_("Discard"),
                        url=self.csrf_protected_url(
                            self.request.link(self.model)
                        ),
                        attrs={'class': 'delete-link'},
                        traits=(
                            Confirm(_(
                                'Do you really want to discard "${title}"?',
                                mapping={'title': self.model.title}
                            ), _(
                                "This cannot be undone."
                            ), _(
                                "Discard Activity")
                            ),
                            Intercooler(
                                request_method="DELETE",
                                redirect_after=self.request.class_link(
                                    VacationActivityCollection
                                )
                            )
                        )
                    ))

            links.append(Link(
                text=_("Edit"),
                url=self.request.link(self.model, name='edit'),
                attrs={'class': 'edit-link'}
            ))

            if not self.request.app.periods:
                links.append(Link(
                    text=_("New Occasion"),
                    url='#',
                    attrs={'class': 'new-occasion'},
                    traits=(
                        Block(
                            _("Occasions cannot be created yet"),
                            _(
                                "There are no periods defined yet. At least "
                                "one period needs to be defined before "
                                "occasions can be created"
                            )
                        )
                    )
                ))
            else:
                links.append(Link(
                    text=_("New Occasion"),
                    url=self.request.link(self.model, 'new-occasion'),
                    attrs={'class': 'new-occasion'}
                ))

        if self.request.is_admin or self.is_owner:
            if self.attendees:
                links.append(Link(
                    text=_("Attendees"),
                    url=self.request.link(self.attendees),
                    attrs={'class': 'show-attendees'}
                ))

        if self.request.is_admin and self.ticket:
            links.append(Link(
                text=_("Show Ticket"),
                url=self.request.link(self.ticket),
                attrs={'class': 'show-ticket'}
            ))

        return links


class PeriodCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(
                _("Activities"),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(_("Manage Periods"), '#')
        )

    @cached_property
    def editbar_links(self):
        return (
            Link(
                _("New Period"),
                self.request.link(self.model, 'new'),
                attrs={'class': 'new-period'}
            ),
        )


class PeriodFormLayout(DefaultLayout):

    def __init__(self, model, request, title):
        super().__init__(model, request)
        self.title = title

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(
                _("Activities"),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(
                _("Manage Periods"),
                self.request.class_link(PeriodCollection)
            ),
            Link(self.title, '#')
        )

    @cached_property
    def editbar_links(self):
        return None


class MatchCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(
                _("Activities"),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(_("Matches"), '#')
        )


class BillingCollectionLayout(DefaultLayout):

    @property
    def families(self):
        yield from self.app.session().execute("""
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
        """)

    @property
    def family_removal_links(self):
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

            if record.has_online_payments:
                traits = (
                    Block(
                        _(
                            "This booking cannot be removed, at least one "
                            "booking has been paid online."
                        ),
                        _(
                            "You may remove the bookings manually one by one."
                        )
                    ),
                )
            else:
                traits = (
                    Confirm(
                        _('Do you really want to remove "${text}"?', mapping={
                            'text': record.text
                        }),
                        _("${count} bookings will be removed", mapping={
                            'count': record.count
                        }),
                        _("Remove ${count} bookings", mapping={
                            'count': record.count
                        })
                    ),
                    Intercooler(request_method='POST')
                )

            yield Link(text=text, url=url, attrs=attrs, traits=traits)

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(
                _("Activities"),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(_("Billing"), '#')
        )

    @cached_property
    def editbar_links(self):
        return (
            Link(
                _("Import Bank Statement"),
                self.request.link(self.model, 'import'),
                attrs={'class': 'import'}
            ),
            Link(
                _("Synchronise Online Payments"),
                self.request.return_here(
                    self.request.class_link(
                        PaymentProviderCollection, name='sync')),
                attrs={'class': 'sync'},
            ),
            LinkGroup(
                title=_("Accounting"),
                links=[
                    Link(
                        text=_("Manual Booking"),
                        url=self.request.link(
                            self.model,
                            name='booking'
                        ),
                        attrs={'class': 'new-booking'},
                        traits=(
                            Block(_(
                                "Manual bookings can only be added "
                                "once the billing has been confirmed"
                            )),
                        ) if not self.model.period.finalized else tuple()
                    ),
                    *self.family_removal_links
                ]
            )
        )


class OnlinePaymentsLayout(DefaultLayout):

    def __init__(self, *args, **kwargs):
        self.title = kwargs.pop('title')
        super().__init__(*args, **kwargs)

    @cached_property
    def editbar_links(self):
        return (
            Link(
                _("Synchronise Online Payments"),
                self.request.return_here(
                    self.request.class_link(
                        PaymentProviderCollection, name='sync')),
                attrs={'class': 'sync'},
            ),
        )

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(
                _("Activities"),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(
                _("Billing"),
                self.request.class_link(BillingCollection)
            ),
            Link(self.title, '#')
        )


class BillingCollectionImportLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(
                _("Activities"),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(_("Billing"), self.request.link(self.model)),
            Link(_("Import Bank Statement"), '#')
        )


class BillingCollectionManualBookingLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(
                _("Activities"),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(_("Billing"), self.request.link(self.model)),
            Link(_("Manual Booking"), '#')
        )


class InvoiceLayout(DefaultLayout):

    def __init__(self, model, request, title):
        super().__init__(model, request)
        self.title = title

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, '#')
        )


class OccasionAttendeeLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(
                _("Activities"),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(
                self.model.activity.title,
                self.request.link(self.model.activity)
            ),
            Link(_("Attendees"), '#')
        )


class NotificationTemplateCollectionLayout(DefaultLayout):

    def __init__(self, model, request, subtitle=None):
        super().__init__(model, request)
        self.subtitle = subtitle

    @cached_property
    def breadcrumbs(self):
        links = [
            Link(_("Homepage"), self.homepage_url),
            Link(
                _("Activities"),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(
                _("Notification Templates"),
                self.request.class_link(NotificationTemplateCollection)
            )
        ]

        if self.subtitle:
            links.append(Link(self.subtitle, '#'))

        return links

    @cached_property
    def editbar_links(self):
        if not self.subtitle:
            return (
                Link(
                    _("New Notification Template"),
                    self.request.link(self.model, 'new'),
                    attrs={'class': 'new-notification'}
                ),
            )


class NotificationTemplateLayout(DefaultLayout):

    def __init__(self, model, request, subtitle=None):
        super().__init__(model, request)
        self.subtitle = subtitle

    @cached_property
    def breadcrumbs(self):
        links = [
            Link(_("Homepage"), self.homepage_url),
            Link(
                _("Activities"),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(
                _("Notification Templates"),
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
