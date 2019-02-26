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


class MunicipalitiesLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Municipalities")

    @cached_property
    def editbar_links(self):
        result = []
        if self.request.has_permission(self.model, EditModel):
            result.append(
                Link(
                    text=_("Import data"),
                    url=self.request.link(self.model, 'import-data'),
                    attrs={'class': 'upload-icon'}
                )
            )
        if self.request.has_permission(self.model, AddModel):
            result.append(
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
                )
            )
        return result

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, self.municipalities_url)
        ]


class ImportMunicipalityDataLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Import data")

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


class MunicipalityLayout(DefaultLayout):

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
            result.append(
                Link(
                    text=_("Delete pick-up dates"),
                    url=self.request.link(self.model, 'delete-dates'),
                    attrs={'class': 'delete-icon'}
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
                )
            )
        return result

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
        return _("Add municipality")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Municipalities"), self.municipalities_url),
            Link(_("Add"), '#')
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
        return _("Edit municipality")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Municipalities"), self.municipalities_url),
            Link(self.model.name, self.request.link(self.model)),
            Link(_("Edit"), '#')
        ]

    @cached_property
    def cancel_url(self):
        return self.request.link(self.model)

    @cached_property
    def success_url(self):
        return self.municipalities_url


class DeleteMunicipalityDatesLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Delete pick-up dates")

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
        return self.request.link(self.model)
