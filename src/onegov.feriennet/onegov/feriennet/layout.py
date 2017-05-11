from cached_property import cached_property
from onegov.activity import Activity, PeriodCollection, Occasion
from onegov.feriennet import _
from onegov.feriennet import security
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.const import OWNER_EDITABLE_STATES
from onegov.org.elements import Link, ConfirmLink, DeleteLink
from onegov.org.layout import DefaultLayout as BaseLayout
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
            url=self.request.link(self.model, name='neu'),
            classes=('new-activity', )
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
    def ticket(self):
        return TicketCollection(self.request.app.session())\
            .by_handler_id(self.model.id.hex)

    @cached_property
    def editbar_links(self):
        if self.is_editable:
            links = []
            period = self.request.app.active_period

            if self.model.state == 'preview':
                if period and self.model.has_occasion_in_period(period):
                    links.append(ConfirmLink(
                        text=_("Request Publication"),
                        url=self.request.link(self.model, name='beantragen'),
                        confirm=_(
                            "Do you really want to request publication?"
                        ),
                        extra_information=_("This cannot be undone."),
                        classes=('confirm', 'request-publication'),
                        yes_button_text=_("Request Publication")
                    ))
                else:
                    links.append(ConfirmLink(
                        text=_("Request Publication"),
                        url=self.request.link(self.model, name='beantragen'),
                        confirm=_(
                            "Please add at least one occasion "
                            "before requesting publication."
                        ),
                        classes=('confirm', 'request-publication'),
                    ))

                links.append(DeleteLink(
                    text=_("Discard Activity"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    confirm=_(
                        'Do you really want to discrd "${title}"?', mapping={
                            'title': self.model.title
                        }
                    ),
                    extra_information=_("This cannot be undone."),
                    redirect_after=self.request.class_link(
                        VacationActivityCollection
                    ),
                    yes_button_text=_("Discard Activity"),
                    classes=('confirm', 'delete-link')
                ))

            links.append(Link(
                text=_("Edit Activity"),
                url=self.request.link(self.model, name='bearbeiten'),
                classes=('edit-link', )
            ))

            if not self.request.app.periods:
                links.append(ConfirmLink(
                    text=_("New Occasion"),
                    url='#',
                    confirm=_("Occasions cannot be created yet"),
                    extra_information=_(
                        "There are no periods defined yet. At least one "
                        "period needs to be defined before occasions can "
                        "be created"
                    ),
                    classes=('confirm', 'new-occasion', )
                ))
            else:
                links.append(Link(
                    text=_("New Occasion"),
                    url=self.request.link(self.model, 'neue-durchfuehrung'),
                    classes=('new-occasion', )
                ))

            if self.request.is_admin and self.ticket:
                links.append(Link(
                    text=_("Show Ticket"),
                    url=self.request.link(self.ticket),
                    classes=('show-ticket', )
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
                self.request.link(self.model, 'neu'),
                classes=('new-period', )
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
                classes=('import', )
            ),
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
                    self.request.link(self.model, 'neu'),
                    classes=('new-notification', )
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
