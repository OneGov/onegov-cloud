from functools import cached_property
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.landsgemeinde import _
from onegov.landsgemeinde.collections import VotumCollection
from onegov.landsgemeinde.layouts.default import DefaultLayout


class AgendaItemCollectionLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _(
            'Agenda items of assembly from ${date}',
            mapping={
                'date': self.format_date(self.model.date, 'date_long')
            }
        )

    @cached_property
    def og_description(self):
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Assemblies'),
                self.request.link(self.assembly_collection())
            ),
            Link(
                self.assembly_title(self.model.assembly),
                self.request.link(self.model.assembly)
            ),
            Link(_('Agenda items'), '#')
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return (
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Agenda item'),
                            url=self.request.link(self.model, 'new'),
                            attrs={'class': 'new-form'}
                        ),
                    ]
                ),
            )


class AgendaItemLayout(DefaultLayout):

    @cached_property
    def title(self):
        return self.agenda_item_title(self.model)

    @cached_property
    def og_description(self):
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Assemblies'),
                self.request.link(self.assembly_collection())
            ),
            Link(
                self.assembly_title(self.model.assembly),
                self.request.link(self.model.assembly)
            ),
            Link(
                self.agenda_item_title(self.model, short=True),
                self.request.link(self.model)
            )
        ]

    def __init__(self, model, request):
        super().__init__(model, request)

        self.request.include('agenda_items')

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            vota = VotumCollection(
                self.app.session(), self.model.date, self.model.number
            )
            return (
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete this agenda '
                              'item?'),
                            _('This cannot be undone.'),
                            _('Delete agenda item'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(
                                self.model.assembly
                            )
                        )
                    )
                ),
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Votum'),
                            url=self.request.link(vota, 'new'),
                            attrs={'class': 'new-form'}
                        ),
                    ]
                )
            )

    def editbar_links_for_votum(self, votum):
        if self.request.is_manager:
            return (
                Link(
                    text=_('Edit'),
                    url=self.request.link(votum, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(votum)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete this votum?'),
                            _('This cannot be undone.'),
                            _('Delete votum'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(
                                self.model
                            )
                        )
                    )
                )
            )
