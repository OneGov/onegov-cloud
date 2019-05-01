from cached_property import cached_property
from onegov.core.elements import Link
from onegov.wtfs import _
from onegov.wtfs.layouts.default import DefaultLayout
from onegov.wtfs.security import EditModel


class UserManualLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("User manual")

    @cached_property
    def editbar_links(self):
        result = []
        if self.request.has_permission(self.model, EditModel):
            result.append(
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-icon'}
                )
            )
        return result

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, '#')
        ]


class EditUserManualLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Edit user manual")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("User manual"), self.user_manual_url),
            Link(_("Edit"), '#')
        ]

    @cached_property
    def cancel_url(self):
        return self.user_manual_url

    @cached_property
    def success_url(self):
        return self.user_manual_url
