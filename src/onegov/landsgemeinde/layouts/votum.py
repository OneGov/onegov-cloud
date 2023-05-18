from cached_property import cached_property
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.landsgemeinde import _
from onegov.landsgemeinde.collections import VotumCollection
from onegov.landsgemeinde.layouts.default import DefaultLayout


class VotumCollectionLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _(
            'Vota of agenda items ${number} of assembly from ${date}',
            mapping={
                'number': self.model.agenda_item_number,
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
            Link(_('Archive'), self.request.link(self.assembly_collection())),
            Link(
                self.assembly_title(self.model.assembly),
                self.request.link(self.model.assembly)
            ),
            Link(
                self.agenda_item_title(self.model.agenda_item, short=True),
                self.request.link(self.model.agenda_item)
            ),
            Link(_('Vota'), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return (
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Votum'),
                            url=self.request.link(self.model, 'new'),
                            attrs={'class': 'new-form'}
                        ),
                    ]
                ),
            )


class VotumLayout(DefaultLayout):

    @cached_property
    def title(self):
        return self.votum_title(self.model)

    @cached_property
    def og_description(self):
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Archive'), self.request.link(self.assembly_collection())),
            Link(
                self.assembly_title(self.model.agenda_item.assembly),
                self.request.link(self.model.agenda_item.assembly)
            ),
            Link(
                self.agenda_item_title(self.model.agenda_item, short=True),
                self.request.link(self.model.agenda_item)
            ),
            Link(
                _('Vota'),
                self.request.link(
                    self.votum_collection(self.model.agenda_item)
                )
            ),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            parent = VotumCollection(
                self.app.session(),
                self.model.date,
                self.model.agenda_item_number
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
                            redirect_after=self.request.link(parent)
                        )
                    )
                )
            )
