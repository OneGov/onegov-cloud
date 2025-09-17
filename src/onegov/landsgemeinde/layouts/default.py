from __future__ import annotations

from functools import cached_property
from onegov.core.static import StaticFile
from onegov.landsgemeinde import _
from onegov.landsgemeinde.collections import AssemblyCollection
from onegov.town6.layout import DefaultLayout as BaseDefaultLayout
from onegov.landsgemeinde.models import Assembly


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.landsgemeinde.models import AgendaItem
    from onegov.landsgemeinde.models import Votum
    from onegov.landsgemeinde.request import LandsgemeindeRequest


class DefaultLayout(BaseDefaultLayout):

    request: LandsgemeindeRequest

    def __init__(self, model: Any, request: LandsgemeindeRequest) -> None:
        super().__init__(model, request)

        self.custom_body_attributes['data-websocket-endpoint'] = ''
        self.custom_body_attributes['data-websocket-schema'] = ''
        self.custom_body_attributes['data-websocket-channel'] = ''

    def assembly_title(self, assembly: Assembly) -> str:

        if assembly.extraordinary:
            return _(
                'Extraodinary ${assembly_type} from ${date}',
                mapping={'assembly_type': self.assembly_type,
                         'date': self.format_date(assembly.date, 'date_long')}
            )
        return _(
            '${assembly_type} from ${date}',
            mapping={'assembly_type': self.assembly_type,
                     'date': self.format_date(assembly.date, 'date_long')}
        )

    def agenda_item_title(
        self,
        agenda_item: AgendaItem,
        short: bool = False
    ) -> str:
        if agenda_item.irrelevant:
            if agenda_item.title:
                return agenda_item.title
            return self.request.translate(_('Irrelevant motion'))
        if not agenda_item.title or short:
            return '{} {}'.format(
                self.request.translate(_('Agenda item')),
                agenda_item.number
            )
        return '{} {}: {}'.format(
            self.request.translate(_('Agenda item')),
            agenda_item.number,
            agenda_item.title
        )

    def votum_title(self, votum: Votum) -> str:
        return '{} {}'.format(
            self.request.translate(_('Votum')),
            votum.number
        )

    def assembly_collection(self) -> AssemblyCollection:
        return AssemblyCollection(self.request.session)

    def current_assembly(self) -> Assembly | None:
        return AssemblyCollection(self.request.session).query().filter(
            Assembly.state == 'ongoing').order_by(
            Assembly.date.desc()).first()

    @cached_property
    def terms_icon(self) -> str:
        static_file = StaticFile.from_application(
            self.app, 'terms_by.svg'
        )

        return self.request.link(static_file)

    @property
    def assembly_type(self) -> str:
        if self.org.assembly_title == 'general_assembly':
            return self.request.translate(_('General Assembly'))

        if self.org.assembly_title == 'town_hall_meeting':
            return self.request.translate(_('Town Hall Meeting'))
        return self.request.translate(_('Assembly'))

    @property
    def assembly_type_plural(self) -> str:
        if self.org.assembly_title == 'general_assembly':
            return self.request.translate(_('General Assemblies'))

        if self.org.assembly_title == 'town_hall_meeting':
            return self.request.translate(_('Town Hall Meetings'))
        return self.request.translate(_('Assemblies'))
