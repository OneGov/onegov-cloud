from cached_property import cached_property

from onegov.core.elements import Link, Confirm, Intercooler
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _


class ReservationLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _('Reservation Details')

    @cached_property
    def editbar_links(self):
        return [
            Link(
                text=_("Add Reservation"),
                url=self.request.class_link(
                    ReservationCollection, name='add'
                ),
                attrs={'class': 'add-icon'}
            ),
        ]


class ReservationCollectionLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _('Reservation Overview')

    @cached_property
    def editbar_links(self):
        if not self.request.is_manager:
            return []
        return [
            Link(
                text=_("Add Reservation"),
                url=self.request.class_link(
                    ReservationCollection, name='add'
                ),
                attrs={'class': 'add-icon'}
            ),
        ]

    def cancellation_btn(self, reservation):
        return Link(
            text=_("Delete"),
            url=self.csrf_protected_url(
                self.request.link(reservation, name='delete')
            ),
            attrs={'class': 'button tiny alert'},
            traits=(
                Confirm(
                    _("Do you want to cancel the reservation ?"),
                    _("A confirmation email will be sent to you later."),
                    _("Cancel reservation for course event"),
                    _("Cancel")
                ),
                Intercooler(
                    request_method='DELETE',
                    redirect_after=self.request.class_link(
                        ReservationCollection
                    )
                )
            )
        )
