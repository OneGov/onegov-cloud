import textwrap

from itertools import groupby
from .utils import as_choices
from .utils import build_metadata
from .utils import html_to_text
from .utils import load_files_by_prefix
from .utils import store_in_zip
from .utils import Geocoder


def transform_rooms(path, prefix, output_file):
    rooms = load_files_by_prefix(path, prefix, mapping=(
        ('Raumverzeichnis', (
            "uid",
            "categories",
            "room_name",
            "room_tags",
            "category",
            "size_max",
            "size_min",
            "zone",
            "room_images",
            "renter_present_time",
            "room_sponsorship",
            "room_ability",
            "room_description",
            "room_infrastructure",
            "room_tos",
            "district",
            "room_address",
            "room_zip",
            "room_city",
            "room_phone",
            "room_email",
            "hirer_name",
            "hirer_address",
            "hirer_zip",
            "hirer_city",
            "hirer_phone",
            "hirer_email"
        )),
    ))

    rooms = sorted((r for r in rooms.lines), key=lambda r: r.uid)
    data = []

    for uid, records in groupby(rooms, key=lambda r: r.uid):
        first, *rest = records

        data.append({
            'Raum/Name': first.room_name,
            'Raum/Untertitel': first.room_tags,
            'Raum/Beschreibung': html_to_text(first.room_description),
            'Raum/Plätze': first.size_max,
            'Raum/Adresse': '\n'.join(p.strip() for p in (
                first.room_address,
                f'{first.room_zip} {first.room_city}'
            ) if p.strip()),
            'Raum/Telefon': first.room_phone,
            'Raum/E-Mail': first.room_email,
            'Raum/Funktionen': html_to_text(first.room_ability),
            'Raum/Infrastruktur': html_to_text(first.room_infrastructure),
            'Raum/Kategorie': [first.category] + [r.category for r in rest],
            'Ort/Zone': [first.zone] if first.zone else [],
            'Ort/Kreis': [first.district] if first.district else [],
            'Vermieter/Name': first.hirer_name,
            'Vermieter/Adresse': '\n'.join(p.strip() for p in (
                first.hirer_address,
                f'{first.hirer_zip} {first.hirer_city}'
            ) if p.strip()),
            'Vermieter/Telefon': first.hirer_phone,
            'Vermieter/E-Mail': first.hirer_email,
            'Vermieter/Präsenzzeit': first.renter_present_time,
            'Details/Sponsor': first.room_sponsorship,
            'Details/Nutzungsbedingungen': html_to_text(first.room_tos)
        })

    zones = sorted(
        set(zone for d in data for zone in d['Ort/Zone']))
    districts = sorted(
        set(district for d in data for district in d['Ort/Kreis']))
    categories = sorted(
        set(cat for d in data for cat in d['Raum/Kategorie']))

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
            'Raum/Plätze',
            'Raum/Adresse',
            'Raum/Telefon',
            'Raum/E-Mail',
            'Raum/Funktionen',
            'Raum/Infrastruktur',
            'Raum/Kategorie',
            'Ort/Zone',
            'Ort/Kreis',
            'Details/Sponsor',
            'Details/Nutzungsbedingungen'
        ],
        contact_fields=[
            'Vermieter/Name',
            'Vermieter/Adresse',
            'Vermieter/Telefon',
            'Vermieter/E-Mail',
            'Vermieter/Präsenzzeit'
        ],
        keyword_fields=[
            'Raum/Kategorie',
            'Ort/Zone',
            'Ort/Kreis'
        ],
        structure=textwrap.dedent(f"""\
            # Raum
            Name *= ___
            Untertitel = ___
            Beschreibung = ...
            Plätze = ___

            Adresse = ...
            Telefon = ___
            E-Mail = ___

            Funktionen = ...
            Infrastruktur = ...

            Kategorie =
                {as_choices(categories)}

            # Ort
            Zone =
                {as_choices(zones)}

            Kreis =
                {as_choices(districts)}

            # Vermieter
            Name = ___
            Adresse = ...
            Telefon = ___
            E-Mail = ___
            Präsenzzeit = ___

            # Details
            Sponsor = ___
            Nutzungsbedingungen = ...

        """))

    geo = Geocoder()

    for entry in data:
        location = geo.geocode(entry['Raum/Adresse'])

        entry['Latitude'] = location.latitude
        entry['Longitude'] = location.longitude

    store_in_zip(output_file, {
        'metadata.json': metadata,
        'data.json': data
    })
