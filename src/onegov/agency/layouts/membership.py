from cached_property import cached_property
from onegov.agency.layouts.agency import AgencyLayout
from onegov.org import _
from onegov.org.layout import DefaultLayout
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link


class MembershipLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return AgencyLayout(self.model.agency, self.request).breadcrumbs + [
            Link(self.model.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_("Delete"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _("Do you really want to delete this membership?"),
                            _("This cannot be undone."),
                            _("Delete membership"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.model.agency)
                        )
                    )
                )
            ]
