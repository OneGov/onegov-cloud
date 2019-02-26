from cached_property import cached_property
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.wtfs import _
from onegov.wtfs.layouts.default import DefaultLayout
from onegov.wtfs.security import AddModel
from onegov.wtfs.security import DeleteModel
from onegov.wtfs.security import EditModel


class UserGroupsLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("User groups")

    @cached_property
    def editbar_links(self):
        result = []
        if self.request.has_permission(self.model, AddModel):
            result.append(
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("User group"),
                            url=self.request.link(
                                self.model,
                                name='add'
                            ),
                            attrs={'class': 'user-group-icon'}
                        )
                    ]
                ),
            )
        return result

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, self.user_groups_url)
        ]


class UserGroupLayout(DefaultLayout):

    @cached_property
    def title(self):
        return self.model.name

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
                                "Do you really want to delete this user group?"
                            ),
                            _("This cannot be undone."),
                            _("Delete"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.user_groups_url
                        )
                    )
                )
            )
        return result

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("User groups"), self.user_groups_url),
            Link(self.title, '#')
        ]


class AddUserGroupLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Add user group")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("User groups"), self.user_groups_url),
            Link(_("Add"), '#')
        ]

    @cached_property
    def cancel_url(self):
        return self.user_groups_url

    @cached_property
    def success_url(self):
        return self.user_groups_url


class EditUserGroupLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Edit user group")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("User groups"), self.user_groups_url),
            Link(self.model.name, self.request.link(self.model)),
            Link(_("Edit"), '#')
        ]

    @cached_property
    def cancel_url(self):
        return self.request.link(self.model)

    @cached_property
    def success_url(self):
        return self.user_groups_url
