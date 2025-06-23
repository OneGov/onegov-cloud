from __future__ import annotations
from uuid import UUID

from onegov.parliament.collections import RISPartyCollection, MeetingCollection
from onegov.parliament.models import RISParty, Party
from onegov.town6.app import TownApp


@TownApp.path(
    model=RISPartyCollection,
    path='/parties',
    # converters={'active': 'bool'}  # FIXME: converter not working yet
)
def get_parties(
    app: TownApp,
    active: bool = True,
) -> RISPartyCollection:
    return RISPartyCollection(app.session(), active)


@TownApp.path(
    model=RISParty,
    path='/party/{id}',
    converters={'id': UUID}
)
def get_party(
    app: TownApp,
    id: UUID
) -> Party | None:
    return RISPartyCollection(app.session()).by_id(id)


@TownApp.path(
    model=MeetingCollection,
    path='/meetings',
)
def get_meetings(
    app: TownApp,
) -> MeetingCollection:
    return MeetingCollection(app.session())
