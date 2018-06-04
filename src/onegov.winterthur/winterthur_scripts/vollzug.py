import attr
import textwrap

from .utils import as_choices
from .utils import build_metadata
from .utils import contains_department
from .utils import contains_email
from .utils import contains_location
from .utils import contains_only_numbers
from .utils import contains_street
from .utils import contains_website
from .utils import Geocoder
from .utils import html_to_text
from .utils import load_files_by_prefix
from .utils import pop_matching
from .utils import store_in_zip


def transform_vollzug(path, prefix, output_file):
    institutions = get_institutions(path, prefix)

    def unique_values(values, attr):
        unique = set()

        for value in values:
            unique.update(getattr(value, attr))

        return sorted(list(unique))

    topics = as_choices(unique_values(institutions, 'topics'))

    metadata = build_metadata(
        title='Vollzugsbehörden',
        lead='Die Vollzugsbehörden der Stadt Winterthur',
        title_format='[Fachstelle/Name] [Fachstelle/Abteilung]',
        lead_format='[Fachstelle/Department]',
        content_fields=[
            'Kategorie/Themen',
            'Kategorie/Vollzugsbereiche',
            'Kategorie/Vollzugsaufgaben'
        ],
        contact_fields=[
            'Fachstelle/Name',
            'Fachstelle/Abteilung',
            'Fachstelle/Department',
            'Kontakt/Adresse',
            'Kontakt/E-Mail',
            'Kontakt/Telefon',
            'Kontakt/Webseite'
        ],
        keyword_fields=[
            'Kategorie/Themen'
        ],
        structure=textwrap.dedent(f"""\
            # Fachstelle
            Name *= ___
            Abteilung = ___
            Department *= ___

            # Kontakt
            Adresse = ...
            Telefon = ___
            E-Mail = ___
            Webseite = ___

            # Kategorie
            Themen =
                {topics}

            Vollzugsbereiche = ...[16]
            Vollzugsaufgaben = ...[16]

        """))

    geo = Geocoder()

    data = [
        {
            'Fachstelle/Name': i.name,
            'Fachstelle/Department': i.department,
            'Fachstelle/Abteilung': i.branch,
            'Kontakt/Adresse': i.address,
            'Kontakt/E-Mail': i.email,
            'Kontakt/Telefon': i.phone,
            'Kontakt/Webseite': i.website,
            'Kategorie/Themen': list(i.topics),
            'Kategorie/Vollzugsbereiche': '\n'.join(
                f'- {c.strip()}' for c in sorted(list(i.chapters))
            ),
            'Kategorie/Vollzugsaufgaben': '\n'.join(
                f'- {t.strip()}' for t in sorted(list(i.tasks))
            ),
            'Latitude': geo.geocode(i.address).latitude,
            'Longitude': geo.geocode(i.address).longitude,
        } for i in institutions
    ]

    store_in_zip(output_file, {
        'metadata.json': metadata,
        'data.json': data
    })


def load_files(path, prefix):
    return load_files_by_prefix(path, prefix, mapping=(
        ('chapter_theme', (
            'chapter_uid',
            'chapter',
            'topic',
            'topic_pid'
        )),
        ('chapter_mm', (
            'uid_local',
            'uid_foreign',
            'sorting'
        )),
        ('institution_vollzugsbehoerden', (
            'uid',
            'institution',
            'description'
        ))
    ))


def get_institutions(path, prefix):
    chapters, links, institutions = load_files(path, prefix)

    # topics by chapter
    topics = {c.chapter: c.topic for c in chapters.lines}

    # chapters by institution id
    chapters = {c.chapter_uid: c.chapter for c in chapters.lines}
    chapters = {l.uid_local: chapters.get(l.uid_foreign) for l in links.lines}

    # resulting institutions
    result = {}

    for r in institutions.lines:
        task = r.institution

        for i in Institution.from_description(r.uid, r.description):
            i = result[i.title] = result.get(i.title, i)
            i.tasks.add(task)

            if chapters[r.uid]:
                i.chapters.add(chapters[r.uid])

            if chapters[r.uid] in topics:
                i.topics.add(topics[chapters[r.uid]])

    return sorted([i for i in result.values()], key=lambda i: i.title)


@attr.s(auto_attribs=True)
class Institution(object):
    name: str
    branch: str
    department: str
    address: str
    phone: str = None
    email: str = None
    website: str = None

    topics: set = attr.Factory(set)
    chapters: set = attr.Factory(set)
    tasks: set = attr.Factory(set)

    @property
    def title(self):
        return ' '.join(part for part in (
            self.name,
            self.branch
        ) if part)

    @classmethod
    def from_description(cls, uid, description):

        def clean(description):
            return description.replace('Tel.:', '')

        def split(description):
            for desc in description.split('</td'):
                if html_to_text(desc).strip():
                    yield desc

        for desc in split(clean(description)):

            lines = html_to_text(desc).split('\n')

            if len(lines) < 6:
                print(f"Could not parse a description for {uid}:")
                print(desc)
                continue

            yield cls(**match_address(lines))


def match_address(lines):
    department = pop_matching(lines, contains_department) or ''
    phone = pop_matching(lines, contains_only_numbers) or ''
    street = pop_matching(lines, contains_street) or ''
    location = pop_matching(lines, contains_location) or ''
    website = pop_matching(lines, contains_website) or ''
    email = pop_matching(lines, contains_email) or ''

    name = lines.pop(0)
    branch = lines and lines.pop(0) or ''

    return {
        'name': name,
        'branch': branch,
        'department': department,
        'address': '\n'.join((p for p in (street, location) if p)),
        'phone': phone,
        'website': website and f'http://{website}' or '',
        'email': email,
    }
