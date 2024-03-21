import os
import requests

from onegov.core.utils import module_path
from onegov.event import EventCollection
from onegov.winterthur import log
from onegov.winterthur.app import WinterthurApp
from onegov.winterthur.collections import AddressCollection


@WinterthurApp.cronjob(hour=15, minute=50, timezone='Europe/Zurich')
def update_streets_directory(request):
    AddressCollection(request.session).update()


@WinterthurApp.cronjob(hour='02', minute='00', timezone='Europe/Zurich')
def import_dws_vk(request):
    """
    Download ics file from DWS and import the events daily.
    https://dwswinterthur.ch/index.php/tipps-fuer-vereine/dws-sprtagenda

    NOTE: typo in website url is correct (June 2023)
    """
    ical_url = 'https://www.google.com/calendar/ical/dwskalender%40gmail.com' \
               '/public/basic.ics'
    try:
        response = requests.get(ical_url, timeout=30)
    except (requests.exceptions.RequestException,
            requests.exceptions.Timeout, Exception) as e:
        raise Exception(f'Failed to retrieve DWS events from {ical_url}') \
            from e

    if not response.status_code == 200:
        raise Exception(f'Failed to retrieve DWS events from {ical_url}. '
                        f'Status code: {response.status_code}')

    icon_name = 'Veranstaltung_breit.jpg'
    icon_path = module_path('onegov.winterthur', 'static') + os.sep + icon_name
    file = open(icon_path, 'rb')

    # import events from response
    collection = EventCollection(request.session)
    added, updated, purged = collection.from_ical(
        response.content,
        future_events_only=True,
        event_image=file,
        default_categories=[],
        default_filter_keywords={
            'kalender': 'Sport Veranstaltungskalender',
            'veranstaltungstyp': 'DWS'
        }
    )
    log.info(f"Events successfully imported "
             f"({len(added)} added, {len(updated)} updated, "
             f"{len(purged)} deleted)")
