from onegov.core.templates import render_macro
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import Votum
from re import sub


def update_ticker(request, assembly, agenda_item=None, action='refresh'):
    """ Updates the ticker.

    Sends either a 'refresh' event to reload the whole ticker (in case the
    assembly has been changed or an agenda item has been added/deleted) or
    and 'update' event with the changed content of the agenda item.

    Also sets the modified timestamp on the assembly used for the polling
    fallback.

    """
    assembly.stamp()
    request.app.pages_cache.flush()
    content = ''
    if action == 'update' and agenda_item:
        layout = DefaultLayout(request.app, request)
        content = render_macro(
            layout.macros['ticker_agenda_item'],
            request,
            {
                'agenda_item': agenda_item,
                'layout': layout,
            }
        )
        content = sub(r'\s+', ' ', content)
        content = content.replace('> ', '>').replace(' <', '<')
        request.app.send_websocket({
            'event': 'update',
            'assembly': assembly.date.isoformat(),
            'node': f'agenda-item-{agenda_item.number}',
            'content': content
        })
    elif action == 'refresh':
        request.app.send_websocket({
            'event': 'refresh',
            'assembly': assembly.date.isoformat(),
        })


def ensure_states(item):
    """ Ensure that all the states are meaningful when changing the state of
    an assembly, agenda item or votum.

    """

    def set_by_children(parent, children):
        if all(x.state == 'scheduled' for x in children):
            parent.state = 'scheduled'
        elif all(x.state == 'completed' for x in children):
            parent.state = 'completed'
        else:
            parent.state = 'ongoing'

    def set_vota(vota, state):
        for votum in vota:
            votum.state = state

    def set_agenda_items(agenda_items, state):
        for agenda_item in agenda_items:
            agenda_item.state = state
            set_vota(agenda_item.vota, state)

    if isinstance(item, Assembly):
        if item.state in ('scheduled', 'completed'):
            set_agenda_items(item.agenda_items, item.state)
        if item.state == 'ongoing':
            pass

    if isinstance(item, AgendaItem):
        assembly = item.assembly
        prev = [x for x in assembly.agenda_items if x.number < item.number]
        next = [x for x in assembly.agenda_items if x.number > item.number]
        if item.state == 'scheduled':
            set_vota(item.vota, 'scheduled')
            set_agenda_items(next, 'scheduled')
            set_by_children(assembly, assembly.agenda_items)
        if item.state == 'ongoing':
            set_agenda_items(prev, 'completed')
            set_agenda_items(next, 'scheduled')
            assembly.state = 'ongoing'
        if item.state == 'completed':
            set_vota(item.vota, 'completed')
            set_agenda_items(prev, 'completed')
            set_by_children(assembly, assembly.agenda_items)

    if isinstance(item, Votum):
        agenda_item = item.agenda_item
        assembly = agenda_item.assembly
        prev_v = [x for x in agenda_item.vota if x.number < item.number]
        next_v = [x for x in agenda_item.vota if x.number > item.number]
        prev_a = [
            x for x in assembly.agenda_items if x.number < agenda_item.number
        ]
        next_a = [
            x for x in assembly.agenda_items if x.number > agenda_item.number
        ]
        if item.state == 'scheduled':
            set_vota(next_v, 'scheduled')
            set_agenda_items(next_a, 'scheduled')
            set_by_children(agenda_item, agenda_item.vota)
            set_by_children(assembly, assembly.agenda_items)
        if item.state == 'ongoing':
            set_vota(prev_v, 'completed')
            set_vota(next_v, 'scheduled')
            set_agenda_items(prev_a, 'completed')
            set_agenda_items(next_a, 'scheduled')
            agenda_item.state = 'ongoing'
            assembly.state = 'ongoing'
        if item.state == 'completed':
            set_vota(prev_v, 'completed')
            set_agenda_items(prev_a, 'completed')
            set_by_children(agenda_item, agenda_item.vota)
            set_by_children(assembly, assembly.agenda_items)
