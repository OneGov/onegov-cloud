from __future__ import annotations

from onegov.core.templates import render_macro
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import Votum
from re import fullmatch
from re import sub


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from collections.abc import Iterable
    from onegov.landsgemeinde.models.agenda import AgendaItemState
    from onegov.landsgemeinde.models.assembly import AssemblyState
    from onegov.landsgemeinde.models.votum import VotumState
    from onegov.landsgemeinde.request import LandsgemeindeRequest


def update_ticker(
    request: LandsgemeindeRequest,
    updated: Collection[Assembly | AgendaItem | Votum]
) -> None:
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


def ensure_states(
    item: Assembly | AgendaItem | Votum
) -> set[Assembly | AgendaItem | Votum]:
    """ Ensure that all the states are meaningful when changing the state of
    an assembly, agenda item or votum.

    Also sets and clears the start time of agenda items.

    Returns a set with updated assemblies, agenda items and vota.

    """

    updated: set[Assembly | AgendaItem | Votum] = set()

    def set_state(
        item: Assembly | AgendaItem | Votum,
        state: AssemblyState | AgendaItemState | VotumState
    ) -> None:
        if item.state != state:
            item.state = state
            updated.add(item)

    def set_by_children(
        parent: Assembly | AgendaItem,
        children: Iterable[AgendaItem] | Iterable[Votum]
    ) -> None:
        if all(x.state == 'draft' for x in children):
            set_state(parent, 'draft')
        elif all(x.state == 'scheduled' for x in children):
            if not isinstance(parent, Assembly):
                set_state(parent, 'scheduled')
        elif all(x.state == 'completed' for x in children):
            set_state(parent, 'completed')
        elif any(x.state in ('ongoing', 'completed') for x in children):
            set_state(parent, 'ongoing')
            if isinstance(parent, AgendaItem):
                parent.start()

    def set_vota(vota: Iterable[Votum], state: VotumState) -> None:
        for votum in vota:
            if votum.state != 'draft':
                set_state(votum, state)

    def clear_start_time(agenda_item: AgendaItem) -> None:
        if agenda_item.start_time:
            agenda_item.start_time = None
            updated.add(agenda_item)

    def set_start_time(item: AgendaItem | Votum) -> None:
        if not item.start_time:
            item.start()
            updated.add(item)

    def set_agenda_items(
        agenda_items: Iterable[AgendaItem],
        state: AgendaItemState
    ) -> None:

        for agenda_item in agenda_items:
            if agenda_item.state != 'draft':
                set_state(agenda_item, state)
                set_vota(agenda_item.vota, state)
                if state == 'scheduled' or state == 'draft':
                    clear_start_time(agenda_item)

    if isinstance(item, Assembly):
        if item.state in ('draft', 'scheduled', 'completed'):
            set_agenda_items(item.agenda_items, item.state)
        elif item.state == 'ongoing':
            pass

    elif isinstance(item, AgendaItem):
        assembly = item.assembly
        prev = [x for x in assembly.agenda_items if x.number < item.number]
        next = [x for x in assembly.agenda_items if x.number > item.number]
        if item.state == 'draft':
            set_vota(item.vota, 'draft')
            set_agenda_items(next, 'draft')
            set_by_children(assembly, assembly.agenda_items)
            clear_start_time(item)
        if item.state == 'scheduled':
            set_vota(item.vota, 'scheduled')
            set_agenda_items(next, 'scheduled')
            set_by_children(assembly, assembly.agenda_items)
            clear_start_time(item)
        elif item.state == 'ongoing':
            set_agenda_items(prev, 'completed')
            set_agenda_items(next, 'scheduled')
            set_state(assembly, 'ongoing')
            set_start_time(item)
        elif item.state == 'completed':
            set_vota(item.vota, 'completed')
            set_agenda_items(prev, 'completed')
            set_by_children(assembly, assembly.agenda_items)

    elif isinstance(item, Votum):
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
        if item.state == 'draft':
            set_vota(next_v, 'draft')
            set_agenda_items(next_a, 'draft')
            set_by_children(agenda_item, agenda_item.vota)
            set_by_children(assembly, assembly.agenda_items)
        if item.state == 'scheduled':
            set_vota(next_v, 'scheduled')
            set_agenda_items(next_a, 'scheduled')
            set_by_children(agenda_item, agenda_item.vota)
            set_by_children(assembly, assembly.agenda_items)
        elif item.state == 'ongoing':
            set_vota(prev_v, 'completed')
            set_vota(next_v, 'scheduled')
            set_agenda_items(prev_a, 'completed')
            set_agenda_items(next_a, 'scheduled')
            set_state(agenda_item, 'ongoing')
            set_state(assembly, 'ongoing')
            set_start_time(item)
            set_start_time(agenda_item)
        elif item.state == 'completed':
            set_vota(prev_v, 'completed')
            set_agenda_items(prev_a, 'completed')
            set_by_children(agenda_item, agenda_item.vota)
            set_by_children(assembly, assembly.agenda_items)

    return updated


def timestamp_to_seconds(timestamp: str | None) -> int | None:
    """Convert a timestamp to seconds.

    Examples:
    '1m30s' -> 90
    '30s' -> 30
    '1h2m30s' -> 3750
    """

    if not timestamp:
        return None

    matches = fullmatch(r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?', timestamp)
    if matches:
        hours = int(matches.group(1) or 0)
        minutes = int(matches.group(2) or 0)
        seconds = int(matches.group(3) or 0)
        if (hours or minutes or seconds):
            if minutes <= 60 and seconds <= 60:
                return 3600 * hours + 60 * minutes + seconds

    return None


def seconds_to_timestamp(seconds: int | None) -> str | None:
    """Convert seconds to a timestamp.

    Examples:
    90 -> '1m30s'
    30 -> '30s'
    3750 -> '1h2m30s'
    """

    if not seconds or seconds < 0:
        return '0s'

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return (
        (f'{hours}h' if hours else '')
        + (f'{minutes}m' if minutes else '')
        + (f'{seconds}s' if seconds else '')
    )
