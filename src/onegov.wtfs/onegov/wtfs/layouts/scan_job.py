from cached_property import cached_property
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.wtfs import _
from onegov.wtfs.layouts.default import DefaultLayout
from onegov.wtfs.security import AddModel
from onegov.wtfs.security import AddModelUnrestricted
from onegov.wtfs.security import DeleteModel
from onegov.wtfs.security import EditModel
from onegov.wtfs.security import EditModelUnrestricted


class ScanJobsLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Scan jobs")

    @cached_property
    def editbar_links(self):
        result = []
        if self.request.has_permission(self.model, AddModelUnrestricted):
            result.append(
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Scan job"),
                            url=self.request.link(
                                self.model,
                                name='add-unrestricted'
                            ),
                            attrs={'class': 'scan-job-icon'}
                        )
                    ]
                ),
            )
        elif self.request.has_permission(self.model, AddModel):
            result.append(
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Scan job"),
                            url=self.request.link(
                                self.model,
                                name='add'
                            ),
                            attrs={'class': 'scan-job-icon'}
                        )
                    ]
                )
            )
        return result

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, self.scan_jobs_url)
        ]


class ScanJobLayout(DefaultLayout):

    @cached_property
    def title(self):
        return self.model.title

    @cached_property
    def subtitle(self):
        return "{}, {}".format(
            self.model.municipality.name,
            self.format_date(self.model.dispatch_date, 'date'),
        )

    @cached_property
    def editbar_links(self):
        result = []
        result.append(
            Link(
                text=_("Print delivery note"),
                url=self.request.link(self.model, 'delivery-note'),
                attrs={'class': 'print-icon'}
            )
        )
        if self.request.has_permission(self.model, EditModelUnrestricted):
            result.append(
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, 'edit-unrestricted'),
                    attrs={'class': 'edit-icon'}
                )
            )
        elif self.request.has_permission(self.model, EditModel):
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
                                "scan job?"
                            ),
                            _("This cannot be undone."),
                            _("Delete"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.scan_jobs_url
                        )
                    )
                )
            )
        return result

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Scan jobs"), self.scan_jobs_url),
            Link(self.model.delivery_number, '#')
        ]


class AddScanJobLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Add scan job")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Scan jobs"), self.scan_jobs_url),
            Link(_("Add"), '#')
        ]

    @cached_property
    def cancel_url(self):
        return self.scan_jobs_url

    @cached_property
    def success_url(self):
        return self.scan_jobs_url


class EditScanJobLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Edit scan job")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Scan jobs"), self.scan_jobs_url),
            Link(self.model.delivery_number, self.request.link(self.model)),
            Link(_("Edit"), '#')
        ]

    @cached_property
    def cancel_url(self):
        return self.request.link(self.model)

    @cached_property
    def success_url(self):
        return self.request.link(self.model)


class DeliveryNoteLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Delivery note")

    @cached_property
    def editbar_links(self):
        result = []
        result.append(
            Link(
                text=_("Print"),
                url='#',
                attrs={
                    'class': 'print-icon',
                    'onclick': 'window.print();return false;'
                }
            )
        )
        return result

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Scan jobs"), self.scan_jobs_url),
            Link(self.model.delivery_number, self.request.link(self.model)),
            Link(self.title, '#')
        ]
