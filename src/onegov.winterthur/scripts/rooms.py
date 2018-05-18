import textwrap

from onegov.core.html import html_to_text

from .utils import as_choices
from .utils import build_metadata
from .utils import load_files_by_prefix
from .utils import store_in_zip


def transform_rooms(path, prefix, output_file):
    rooms = load_files_by_prefix(path, prefix, mapping=(
        ('room', (
            'room_name',
            'room_tags',
            'room_address',
            'size_max',
            'size_min',
            'zone',
            'categories',
            'room_images',
            'renter_address',
            'renter_present_time',
            'room_sponsorship',
            'room_ability',
            'room_description',
            'room_infrastructure',
            'room_tos',
            'district'
        )),
    ))

    data = []
    for r in rooms.lines:
        data.append({
            'Raum/Name': r.room_name,
            'Raum/Untertitel': r.room_tags,
            'Raum/Beschreibung': r.room_description,
            'Ort/Zone': [r.zone] if r.zone else [],
            'Ort/Kreis': [r.district] if r.district else [],
            'Details/Plätze': r.size_max,
            'Details/Kategorien': [
                r.strip() for r in r.categories.split(';') if r.strip()
            ],
            'Details/Funktionen': html_to_text(r.room_ability),
            'Details/Infrastruktur': (
                html_to_text(r.room_infrastructure).replace('\n\n', '\n')
            ),
            'Details/Vermieter': r.renter_address,
            'Details/Vermieter Präsenzzeit': r.renter_present_time,
            'Details/Sponsor': r.room_sponsorship,
            'Details/Nutzungsbedingungen': r.room_tos
        })

    zones = sorted(
        set(zone for d in data for zone in d['Ort/Zone']))
    districts = sorted(
        set(district for d in data for district in d['Ort/Kreis']))
    categories = sorted(
        set(cat for d in data for cat in d['Details/Kategorien']))

    metadata = build_metadata(
        title='Räume zum Mieten',
        lead=(
            'In Winterthur gibt es ein vielfältiges Angebot an Räumen, die '
            'gemietet werden können. Freizeitanlagen, Waldhütten, Räume für '
            'Feste, Sitzungen oder kulturelle Veranstaltungen sowie Kurs- und '
            'Seminarräume.'
        ),
        title_format='[Raum/Name]',
        lead_format='[Raum/Beschreibung]',
        content_fields=[
            'Raum/Untertitel',
            'Ort/Zone',
            'Ort/Kreis',
            'Details/Plätze',
            'Details/Kategorien',
            'Details/Funktionen',
            'Details/Infrastruktur',
            'Details/Vermieter',
            'Details/Vermieter Präsenzzeit',
            'Details/Sponsor',
            'Details/Nutzungsbedingungen'
        ],
        contact_fields=[
        ],
        keyword_fields=[
            'Details/Kategorien',
            'Ort/Zone',
            'Ort/Kreis'
        ],
        structure=textwrap.dedent(f"""\
            # Raum
            Name *= ___
            Untertitel = ___
            Beschreibung = ...

            # Ort
            Zone =
                {as_choices(zones)}

            Kreis =
                {as_choices(districts)}

            # Details
            Plätze = ___

            Kategorien =
                {as_choices(categories)}

            Funktionen = ...
            Infrastruktur = ...

            Vermieter = ___
            Vermieter Präsenzzeit = ___

            Sponsor = ___
            Nutzungsbedingungen = ...

        """))

    store_in_zip(output_file, {
        'metadata.json': metadata,
        'data.json': data
    })
