from onegov.landsgemeinde import _
from onegov.landsgemeinde.collections import AssemblyCollection
from onegov.town6.layout import DefaultLayout as BaseDefaultLayout


class DefaultLayout(BaseDefaultLayout):

    def __init__(self, model, request):
        super().__init__(model, request)

        self.custom_body_attributes['data-websocket-endpoint'] = ''
        self.custom_body_attributes['data-websocket-schema'] = ''
        self.custom_body_attributes['data-websocket-channel'] = ''

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
            if agenda_item.title:
                return agenda_item.title
            return self.request.translate(_('Irrelevant motion'))
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
