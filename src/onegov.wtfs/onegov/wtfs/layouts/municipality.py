from cached_property import cached_property
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.wtfs import _
from onegov.wtfs.layouts.default import DefaultLayout


class MunicipalitiesLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Municipalities")

    @cached_property
    def editbar_links(self):
        if self.request.has_role('admin'):
            return [
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Municipality"),
                            url=self.request.link(
                                self.model,
                                name='add'
                            ),
                            attrs={'class': 'municipality-icon'}
                        )
                    ]
                ),
            ]
        return []

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, self.municipalities_url)
        ]


class MunicipalityLayout(DefaultLayout):

    @cached_property
    def title(self):
        return self.model.name

    @cached_property
    def editbar_links(self):
        if self.request.has_role('admin'):
            return [
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-icon'}
                ),
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
                                "municipality?"
                            ),
                            _("This cannot be undone."),
                            _("Delete"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.municipalities_url
                        )
                    )
                ),
            ]
        return []

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Municipalities"), self.municipalities_url),
            Link(self.title, '#')
        ]


class AddMunicipalityLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Add")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Municipalities"), self.municipalities_url),
            Link(self.title, '#')
        ]

    @cached_property
    def cancel_url(self):
        return self.municipalities_url

    @cached_property
    def success_url(self):
        return self.municipalities_url


class EditMunicipalityLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Edit")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Municipalities"), self.municipalities_url),
            Link(self.model.name, self.request.link(self.model)),
            Link(self.title, '#')
        ]

    @cached_property
    def cancel_url(self):
        return self.request.link(self.model)

    @cached_property
    def success_url(self):
        return self.municipalities_url
