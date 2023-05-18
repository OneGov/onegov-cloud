from onegov.landsgemeinde import _
from onegov.landsgemeinde.collections import AgendaItemCollection
from onegov.landsgemeinde.collections import AssemblyCollection
from onegov.landsgemeinde.collections import VotumCollection
from onegov.town6.layout import DefaultLayout as BaseDefaultLayout


class DefaultLayout(BaseDefaultLayout):

    def assembly_title(self, assembly):
        if assembly.extraordinary:
            return _(
                'Extraodinary assembly from ${date}',
                mapping={'date': self.format_date(assembly.date, 'date_long')}
            )
        return _(
            'Assembly from ${date}',
            mapping={'date': self.format_date(assembly.date, 'date_long')}
        )

    def agenda_item_title(self, agenda_item, html=False, short=False):
        if agenda_item.irrelevant:
            return agenda_item.title
        if not agenda_item.title or short:
            return '{} {}'.format(
                self.request.translate(_('Agenda item')),
                agenda_item.number
            )
        if html:
            return '{} {}<br><small>{}</small>'.format(
                self.request.translate(_('Agenda item')),
                agenda_item.number,
                '<br>'.join(agenda_item.title_parts)
            )
        return '{} {}: {}'.format(
            self.request.translate(_('Agenda item')),
            agenda_item.number,
            agenda_item.title
        )

    def votum_title(self, votum):
        return '{} {}'.format(
            self.request.translate(_('Votum')),
            votum.number
        )

    def assembly_collection(self):
        return AssemblyCollection(self.request.session)

    def agenda_item_collection(self, assembly):
        return AgendaItemCollection(self.request.session, assembly.date)

    def votum_collection(self, agenda_item):
        return VotumCollection(
            self.request.session,
            agenda_item.date,
            agenda_item.number
        )
