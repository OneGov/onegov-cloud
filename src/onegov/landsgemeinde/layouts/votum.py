from functools import cached_property
from onegov.core.elements import Link
from onegov.landsgemeinde import _
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
            Link(
                _('Assemblies'),
                self.request.link(self.assembly_collection())
            ),
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
            Link(
                _('Assemblies'),
                self.request.link(self.assembly_collection())
            ),
            Link(
                self.assembly_title(self.model.agenda_item.assembly),
                self.request.link(self.model.agenda_item.assembly)
            ),
            Link(
                self.agenda_item_title(self.model.agenda_item, short=True),
                self.request.link(self.model.agenda_item)
            ),
            Link(self.title, '#')
        ]
