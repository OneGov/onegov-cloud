from onegov.core.templates import render_macro
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import Votum
from re import sub


def update_ticker(request, updated):
    """ Updates the ticker by a set of updated assemblies, agenda items or
    vota.

    Sends either a 'refresh' event to reload the whole ticker (in case the
    assembly has been changed or an agenda item has been added/deleted) or
    and 'update' event with the changed content of the agenda item.

    Provide an assembly to ensure, that the whole ticker is reloaded.

    Also sets the modified timestamp on the assembly used for the polling
    fallback.

    """

    # collapse vota to agenda items
    vota = {item for item in updated if isinstance(item, Votum)}
    agenda_items = {item for item in updated if isinstance(item, AgendaItem)}
    agenda_items.update({votum.agenda_item for votum in vota})

    # distinguish between directly given assemblies which will trigger a reload
    # and assemblies given indirectly by agenda items or vota
    given_assemblies = {item for item in updated if isinstance(item, Assembly)}
    other_assemblies = {agenda_item.assembly for agenda_item in agenda_items}
    assemblies = given_assemblies | other_assemblies

    if assemblies:
        request.app.pages_cache.flush()

    for assembly in assemblies:
        assembly.stamp()
        if assembly in given_assemblies:
            request.app.send_websocket({
                'event': 'refresh',
                'assembly': assembly.date.isoformat(),
            })
        else:
            content = ''
            for agenda_item in agenda_items:
                agenda_item.stamp()
                if agenda_item.assembly == assembly:
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
                        'content': content,
                        'state': agenda_item.state
                    })


def ensure_states(item):
    """ Ensure that all the states are meaningful when changing the state of
    an assembly, agenda item or votum.

    Also sets and clears the start time of agenda items.

    Returns a set with updated assemblies, agenda items and vota.

    """

    def set_state(item, state, updated):
        if item.state != state:
            item.state = state
            updated.add(item)

    def set_by_children(parent, children, updated):
        if all(x.state == 'scheduled' for x in children):
            if parent.state != 'ongoing':
                set_state(parent, 'scheduled', updated)
        elif all(x.state == 'completed' for x in children):
            set_state(parent, 'completed', updated)
        else:
            set_state(parent, 'ongoing', updated)
            if isinstance(parent, AgendaItem):
                parent.start()

    def set_vota(vota, state, updated):

        for votum in vota:
            set_state(votum, state, updated)

    def clear_start_time(agenda_item, state, updated):
        if agenda_item.start_time:
            agenda_item.start_time = None
            updated.add(agenda_item)

    def set_start_time(agenda_item, updated):
        if not agenda_item.start_time:
            agenda_item.start()
            updated.add(agenda_item)

    def set_agenda_items(agenda_items, state, updated):

        for agenda_item in agenda_items:
            set_state(agenda_item, state, updated)
            set_vota(agenda_item.vota, state, updated)
            if state == 'scheduled':
                clear_start_time(agenda_item, state, updated)

        return updated

    updated = set()

    if isinstance(item, Assembly):
        if item.state in ('scheduled', 'completed'):
            set_agenda_items(item.agenda_items, item.state, updated)
        if item.state == 'ongoing':
            pass

    if isinstance(item, AgendaItem):
        assembly = item.assembly
        prev = [x for x in assembly.agenda_items if x.number < item.number]
        next = [x for x in assembly.agenda_items if x.number > item.number]
        if item.state == 'scheduled':
            set_vota(item.vota, 'scheduled', updated)
            set_agenda_items(next, 'scheduled', updated)
            set_by_children(assembly, assembly.agenda_items, updated)
            clear_start_time(item, item.state, updated)
        if item.state == 'ongoing':
            set_agenda_items(prev, 'completed', updated)
            set_agenda_items(next, 'scheduled', updated)
            set_state(assembly, 'ongoing', updated)
            set_start_time(item, updated)
        if item.state == 'completed':
            set_vota(item.vota, 'completed', updated)
            set_agenda_items(prev, 'completed', updated)
            set_by_children(assembly, assembly.agenda_items, updated)

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
            set_vota(next_v, 'scheduled', updated)
            set_agenda_items(next_a, 'scheduled', updated)
            set_by_children(agenda_item, agenda_item.vota, updated)
            set_by_children(assembly, assembly.agenda_items, updated)
        if item.state == 'ongoing':
            set_vota(prev_v, 'completed', updated)
            set_vota(next_v, 'scheduled', updated)
            set_agenda_items(prev_a, 'completed', updated)
            set_agenda_items(next_a, 'scheduled', updated)
            set_state(agenda_item, 'ongoing', updated)
            set_state(assembly, 'ongoing', updated)
            set_start_time(agenda_item, updated)
        if item.state == 'completed':
            set_vota(prev_v, 'completed', updated)
            set_agenda_items(prev_a, 'completed', updated)
            set_by_children(agenda_item, agenda_item.vota, updated)
            set_by_children(assembly, assembly.agenda_items, updated)

    return updated
