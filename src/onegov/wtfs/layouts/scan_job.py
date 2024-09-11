from functools import cached_property
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.wtfs import _
from onegov.wtfs.layouts.default import DefaultLayout
from onegov.wtfs.security import AddModel
from onegov.wtfs.security import AddModelUnrestricted
from onegov.wtfs.security import DeleteModel
from onegov.wtfs.security import EditModel
from onegov.wtfs.security import EditModelUnrestricted


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.elements import Element


class ScanJobsLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Scan jobs')

    @cached_property
    def editbar_links(self) -> list['Element']:
        result: list[Element] = []
        if self.request.has_permission(self.model, AddModelUnrestricted):
            result.append(
                Link(
                    text=_('Add'),
                    url=self.request.link(
                        self.model,
                        name='add-unrestricted'
                    ),
                    attrs={'class': 'add-icon'}
                )
            )
        elif self.request.has_permission(self.model, AddModel):
            result.append(
                Link(
                    text=_('Add'),
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
            Link(_('Homepage'), self.homepage_url),
            Link(self.title, self.scan_jobs_url)
        ]


class ScanJobLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return self.model.title

    @cached_property
    def subtitle(self) -> str:
        return '{}, {}'.format(
            self.model.municipality.name,
            self.format_date(self.model.dispatch_date, 'date'),
        )

    @cached_property
    def editbar_links(self) -> list['Element']:
        result: list[Element] = [
            Link(
                text=_('Print delivery note'),
                url=self.request.link(self.model, 'delivery-note'),
                attrs={'class': 'print-icon'}
            )
        ]
        if self.request.has_permission(self.model, EditModelUnrestricted):
            result.append(
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit-unrestricted'),
                    attrs={'class': 'edit-icon'}
                )
            )
        elif self.request.has_permission(self.model, EditModel):
            result.append(
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-icon'}
                )
            )
        if self.request.has_permission(self.model, DeleteModel):
            result.append(
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-icon'},
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to delete this '
                                'scan job?'
                            ),
                            _('This cannot be undone.'),
                            _('Delete'),
                            _('Cancel')
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
    def breadcrumbs(self) -> list['Element']:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Scan jobs'), self.scan_jobs_url),
            Link(self.model.delivery_number, '#')
        ]


class AddScanJobLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Add scan job')

    @cached_property
    def breadcrumbs(self) -> list['Element']:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Scan jobs'), self.scan_jobs_url),
            Link(_('Add'), '#')
        ]

    @cached_property
    def cancel_url(self) -> str:
        return self.scan_jobs_url

    @cached_property
    def success_url(self) -> str:
        return self.scan_jobs_url


class EditScanJobLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Edit scan job')

    @cached_property
    def breadcrumbs(self) -> list['Element']:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Scan jobs'), self.scan_jobs_url),
            Link(self.model.delivery_number, self.request.link(self.model)),
            Link(_('Edit'), '#')
        ]

    @cached_property
    def cancel_url(self) -> str:
        return self.request.link(self.model)

    @cached_property
    def success_url(self) -> str:
        return self.request.link(self.model)


class DeliveryNoteLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Delivery note')

    @cached_property
    def editbar_links(self) -> list['Element']:
        return [
            Link(
                text=_('Print'),
                url='#',
                attrs={
                    'class': 'print-icon',
                }
            )
        ]

    @cached_property
    def breadcrumbs(self) -> list['Element']:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Scan jobs'), self.scan_jobs_url),
            Link(self.model.delivery_number, self.request.link(self.model)),
            Link(self.title, '#')
        ]
