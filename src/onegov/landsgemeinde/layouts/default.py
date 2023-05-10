from onegov.landsgemeinde import _
from onegov.landsgemeinde.collections import AgendaItemCollection
from onegov.landsgemeinde.collections import AssemblyCollection
from onegov.town6.layout import DefaultLayout as BaseDefaultLayout


class DefaultLayout(BaseDefaultLayout):

    def assembly_title(self, assembly):
        return _(
            'Assembly from ${date}',
            mapping={'date': self.format_date(assembly.date, 'date_long')}
        )

    def agenda_item_title(self, agenda_item):
        return '{} {}: {}'.format(
            self.request.translate(_('Agenda item')),
            agenda_item.number,
            agenda_item.title
        )

    def assembly_collection(self):
        return AssemblyCollection(self.request.session)

    def agenda_item_collection(self, agenda):
        return AgendaItemCollection(self.request.session, agenda.id)
