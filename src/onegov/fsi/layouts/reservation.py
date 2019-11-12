from cached_property import cached_property

from onegov.core.elements import Link
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
