import textwrap

from .utils import as_choices
from .utils import build_metadata
from .utils import load_files_by_prefix
from .utils import store_in_zip
from .utils import html_to_text


def transform_theater(path, prefix, output_file):
    columns = (
        'type',
        'category',
        'uid',
        'titel',
        'organizer',
        'beschreibung',
        'geeignet',
        'dauer',
        'datum',
        'kosten',
        'leitung',
        'besonderes',
        'anmeldung',
        'onlineanmeldung',
    )

    records = load_files_by_prefix(path, prefix, (('Theater', columns),))
    data = []

    for record in records.lines:
        data.append({
            'Angebot/Titel': record.titel,
            'Angebot/Beschreibung': html_to_text(record.beschreibung),
            'Angebot/Dauer': record.dauer,
            'Angebot/Kategorie': [record.category],
            'Angebot/Zielgruppe': record.geeignet and [
                record.geeignet.replace(
                    '1.-  5. Klasse',
                    '1. - 5. Klasse'
                ).replace(
                    '6. -  9. Klasse',
                    '6. - 9. Klasse'
                )
            ] or [],
            'Details/Datum': record.datum,
            'Details/Anmeldung': record.anmeldung,
            'Details/Kosten': record.kosten,
            'Details/Leitung': record.leitung,
            'Details/Besonderes': record.besonderes
        })

    categories = sorted(set(
        d['Angebot/Kategorie'][0]
        for d in data if d['Angebot/Kategorie']
    ))
    targets = sorted(set(
        d['Angebot/Zielgruppe'][0]
        for d in data if d['Angebot/Zielgruppe']
    ))

    metadata = build_metadata(
        title="Angebote Theaterpädagogik",
        lead=(
            "Allen Schulklassen werden faszinierende, an- und aufregende, "
            "lehrreiche und berührende Erlebnisse in den Museen, Theatern "
            "und Konzertsälen dieser Stadt angeboten. "
        ),
        title_format='[Angebot/Titel]',
        lead_format='[Angebot/Beschreibung]',
        content_fields=[
            'Angebot/Dauer',
            'Angebot/Kategorie',
            'Angebot/Zielgruppe',
            'Details/Datum',
            'Details/Anmeldung',
            'Details/Kosten',
            'Details/Leitung',
            'Details/Besonderes',
        ],
        contact_fields=[],
        keyword_fields=[
            'Angebot/Kategorie',
            'Angebot/Zielgruppe'
        ],
        structure=textwrap.dedent(f"""\
            # Angebot
            Titel *= ___
            Beschreibung *= ...
            Dauer = ___

            Kategorie *=
                {as_choices(categories)}

            Zielgruppe =
                {as_choices(targets)}

            # Details
            Datum = ___
            Anmeldung = ___
            Kosten = ___
            Leitung = ___
            Besonderes = ...
        """)
    )

    store_in_zip(output_file, {
        'metadata.json': metadata,
        'data.json': data
    })
