from __future__ import annotations

import os
import requests

from onegov.core.utils import module_path
from onegov.event import EventCollection
from onegov.winterthur import log
from onegov.winterthur.app import WinterthurApp
from onegov.winterthur.collections import AddressCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.winterthur.request import WinterthurRequest


@WinterthurApp.cronjob(hour=15, minute=50, timezone='Europe/Zurich')
def update_streets_directory(request: WinterthurRequest) -> None:
    AddressCollection(request.session).update()


@WinterthurApp.cronjob(hour='02', minute='00', timezone='Europe/Zurich')
def import_dws_vk(request: WinterthurRequest) -> None:
    """
    Download ics file from DWS and import the events daily.
    https://dwswinterthur.ch/index.php/tipps-fuer-vereine/dws-sprtagenda

    NOTE: typo in website url is correct (June 2023)
    """
    ical_url = ('https://www.google.com/calendar/ical/dwskalender%40gmail.com'
                '/public/basic.ics')
    try:
        response = requests.get(ical_url, timeout=30)
    except Exception:
        log.exception(f'Failed to retrieve DWS events from {ical_url}')
        return

    if response.status_code != 200:
        log.exception(f'Failed to retrieve DWS events from {ical_url}. '
                      f'Status code: {response.status_code}')
        return

    icon_name = 'Veranstaltung_breit.jpg'
    icon_path = module_path('onegov.winterthur', 'static') + os.sep + icon_name
    with open(icon_path, 'rb') as file:
        # import events from response
        collection = EventCollection(request.session)
        added, updated, purged = collection.from_ical(
            # TODO: the ical stubs claim this needs to be `str`, but `bytes
            #       seems to work as well, so we'll leave it unchanged for now
            #       but we may want to try just passing `response.text` here.
            response.content,  # type:ignore[arg-type]
            future_events_only=True,
            event_image=file,
            default_categories=[],
            # FIXME: I'm not super happy that we both allow a list of values
            #        and a single value, what is the difference in behavior? Is
            #        there even one? If not just make it always a list please.
            default_filter_keywords={
                'kalender': 'Sport Veranstaltungskalender',  # type:ignore
                'veranstaltungstyp': 'DWS'  # type:ignore
            }
        )
        log.info(f'Events successfully imported '
                 f'({len(added)} added, {len(updated)} updated, '
                 f'{len(purged)} deleted)')
