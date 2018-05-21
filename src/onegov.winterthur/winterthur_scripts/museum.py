import textwrap

from itertools import chain

from .utils import build_metadata
from .utils import load_files_by_prefix
from .utils import store_in_zip
from .utils import as_choices


def transform_museum(path, prefix, output_file):
    columns = (
        'titel',
        'l18n_parent',
        'gesamtangebotid',
        'kultureinrichtungid',
        'beschreibung',
        'geeignet',
        'dauer',
        'datum',
        'kosten',
        'leitung',
        'besonderes',
        'anmeldung',
        'onlineanmeldung',
        'bild',
    )

    history, art = load_files_by_prefix(path, prefix, (
        ('Geschichte', columns),
        ('Kunst', columns)
    ))

    data = []

    for record in chain(history.lines, art.lines):
        data.append({
            'Angebot/Titel': record.titel,
            'Angebot/Beschreibung': record.beschreibung,
            'Angebot/Einrichtung': record.kultureinrichtungid,
            'Angebot/Dauer': record.dauer,
            'Angebot/Gesamtangebot': [record.gesamtangebotid],
            'Angebot/Zielgruppe': record.geeignet and [record.geeignet] or [],
            'Details/Datum': record.datum,
            'Details/Anmeldung': record.anmeldung,
            'Details/Kosten': record.kosten,
            'Details/Leitung': record.leitung,
            'Details/Besonderes': record.besonderes
        })

    types = sorted(set(
        d['Angebot/Gesamtangebot'][0]
        for d in data if d['Angebot/Gesamtangebot']
    ))
    targets = sorted(set(
        d['Angebot/Zielgruppe'][0]
        for d in data if d['Angebot/Zielgruppe']
    ))

    metadata = build_metadata(
        title="Angebote Museumspädagogik",
        lead=(
            "Angebote für Klassen aller Schulstufen und Gruppen "
            "der Schulergänzenden Betreuung"
        ),
        title_format='[Angebot/Titel]',
        lead_format='[Angebot/Beschreibung]',
        content_fields=[
            'Angebot/Einrichtung',
            'Angebot/Dauer',
            'Angebot/Gesamtangebot',
            'Angebot/Zielgruppe',
            'Angebot/Datum',
            'Angebot/Anmeldung',
            'Angebot/Kosten',
            'Angebot/Leitung',
            'Angebot/Besonderes',
        ],
        contact_fields=[''],
        keyword_fields=[
            'Angebot/Gesamtangebot',
            'Angebot/Zielgruppe'
        ],
        structure=textwrap.dedent(f"""\
            # Angebot
            Titel *= ___
            Beschreibung *= ...
            Einrichtung *= ___
            Dauer *= ___

            Gesamtangebot *=
                {as_choices(types)}

            Zielgruppe *=
                {as_choices(targets)}

            # Details
            Datum = ___
            Anmeldung = ___
            Kosten = ___
            Leitung = ___
            Besonderes = ...
        """))

    store_in_zip(output_file, {
        'metadata.json': metadata,
        'data.json': data
    })
