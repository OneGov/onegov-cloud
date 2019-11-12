from cached_property import cached_property

from onegov.core.elements import Link, Confirm, Intercooler
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _


class ReservationCollectionLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _('Reservation Overview')

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                Link(
                    text=_("Add Reservation"),
                    url=self.request.class_link(
                        ReservationCollection, name='add'
                    ),
                    attrs={'class': 'add-icon'}
                ),
            ]
        return []

    @cached_property
    def current_course_event(self):
        if not self.model.course_event_id:
            return None
        return self.model.query().first().course_event

    @property
    def send_info_mail_url(self):
        return self.request.link(
            self.current_course_event.info_template, name='send')

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(
            Link(_('Manage Reservations'), self.request.link(self.model))
        )
        return links

    def intercooler_btn_for_item(self, reservation):
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
                    redirect_after=self.request.link(self.model)
                )
            )
        )


class ReservationLayout(ReservationCollectionLayout):

    @cached_property
    def title(self):
        if self.request.view_name == 'add':
            return _('Add Reservation')
        return _('Reservation Details')

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(
            Link(_('Current Reservation'), '#')
        )
        return links
