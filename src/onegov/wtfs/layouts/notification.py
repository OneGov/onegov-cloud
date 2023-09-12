from functools import cached_property
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.wtfs import _
from onegov.wtfs.layouts.default import DefaultLayout
from onegov.wtfs.security import AddModel
from onegov.wtfs.security import DeleteModel
from onegov.wtfs.security import EditModel


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.elements import Element


class NotificationsLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _("Notifications")

    @cached_property
    def editbar_links(self) -> list['Element']:
        result: list['Element'] = []
        if self.request.has_permission(self.model, AddModel):
            result.append(
                Link(
                    text=_("Add"),
                    url=self.request.link(
                        self.model,
                        name='add'
                    ),
                    attrs={'class': 'add-icon'}
                )
            )
        return result

    @cached_property
    def breadcrumbs(self) -> list['Element']:
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, self.notifications_url)
        ]


class NotificationLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return self.model.title

    @cached_property
    def editbar_links(self) -> list['Element']:
        result: list['Element'] = []
        if self.request.has_permission(self.model, EditModel):
            result.append(
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-icon'}
                )
            )
        if self.request.has_permission(self.model, DeleteModel):
            result.append(
                Link(
                    text=_("Delete"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-icon'},
                    traits=(
                        Confirm(
                            _(
                                "Do you really want to delete this "
                                "notification?"
                            ),
                            _("This cannot be undone."),
                            _("Delete"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.notifications_url
                        )
                    )
                )
            )
        return result

    @cached_property
    def breadcrumbs(self) -> list['Element']:
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Notifications"), self.notifications_url),
            Link(self.title, '#')
        ]


class AddNotificationLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _("Add notification")

    @cached_property
    def breadcrumbs(self) -> list['Element']:
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Notifications"), self.notifications_url),
            Link(_("Add"), '#')
        ]

    @cached_property
    def cancel_url(self) -> str:
        return self.notifications_url

    @cached_property
    def success_url(self) -> str:
        return self.notifications_url


class EditNotificationLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _("Edit notification")

    @cached_property
    def breadcrumbs(self) -> list['Element']:
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Notifications"), self.notifications_url),
            Link(self.model.title, self.request.link(self.model)),
            Link(_("Edit"), '#')
        ]

    @cached_property
    def cancel_url(self) -> str:
        return self.request.link(self.model)

    @cached_property
    def success_url(self) -> str:
        return self.request.link(self.model)
