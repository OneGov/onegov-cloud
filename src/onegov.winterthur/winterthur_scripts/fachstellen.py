import textwrap

from .utils import as_choices
from .utils import build_metadata
from .utils import load_files_by_prefix
from .utils import store_in_zip
from .utils import Geocoder


def transform_fachstellen(path, prefix, output_file):
    data = []

    for r in load_files(path, prefix).lines:
        data.append({
            'Fachstelle/Name': r.name,
            'Fachstelle/Beschreibung': r.description,
            'Fachstelle/Adresse': '\n'.join(
                l.strip() for l in r.company.split('</br>') if l.strip()
            ),
            'Fachstelle/Telefon': r.phone,
            'Fachstelle/E-Mail': r.email,
            'Fachstelle/Webseite': r.www and f'http://{r.www}' or '',
            'Fachstelle/Themen': [
                g.strip() for g in r.addressgroup.split(';')
            ]
        })

    topics = {g for d in data for g in d['Fachstelle/Themen']}
    topics = as_choices(sorted(list(topics)))

    geo = Geocoder()

    for entry in data:
        location = geo.geocode(
            '\n'.join(entry['Fachstelle/Adresse'].split('\n')[-2:]))

        entry['Latitude'] = location.latitude
        entry['Longitude'] = location.longitude

    metadata = build_metadata(
        title='Fachstellen A-Z',
        lead='Die Fachstellen der Stadt Winterthur',
        title_format='[Fachstelle/Name]',
        lead_format='[Fachstelle/Beschreibung]',
        content_fields=['Fachstelle/Themen'],
        contact_fields=[
            'Fachstelle/Adresse',
            'Fachstelle/Telefon',
            'Fachstelle/E-Mail',
            'Fachstelle/Webseite',
        ],
        keyword_fields=[
            'Fachstelle/Themen'
        ],
        structure=textwrap.dedent(f"""\
            # Fachstelle
            Name *= ___
            Beschreibung = ...

            Adresse = ...
            Telefon = ___
            E-Mail = @@@
            Webseite = ___

            Themen =
                {topics}
        """))

    store_in_zip(output_file, {
        'metadata.json': metadata,
        'data.json': data
    })


def load_files(path, prefix):
    return load_files_by_prefix(path, prefix, mapping=(
        ('address_fachstellen', (
            'last_name',
            'name',
            'phone',
            'www',
            'email',
            'company',
            'city',
            'zip',
            'description',
            'addressgroup'
        )),
    ))
