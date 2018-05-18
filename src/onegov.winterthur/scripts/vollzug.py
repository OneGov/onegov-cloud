import attr
import geopy
import json
import re
import shutil
import tempfile
import textwrap

from onegov.core.cache import lru_cache
from onegov.core.csv import CSVFile
from onegov.core.html import html_to_text
from onegov.core.utils import normalize_for_url, safe_format_keys
from onegov.form import flatten_fieldsets, parse_formcode
from pathlib import Path


@lru_cache(maxsize=1)
def geocoder():
    return geopy.geocoders.Nominatim(user_agent='onegov-cloud-import')


@lru_cache(maxsize=64)
def geocode(address):
    result = geocoder().geocode(address)
    return (
        getattr(result, 'latitude', None),
        getattr(result, 'longitude', None)
    )


def contains_number(text):
    return re.search(r'[0-9]+', text) and True or False


def contains_only_numbers(text):
    return re.match(r'^[0-9\s]+$', text) and True or False


def contains_department(text):
    return 'depart' in text.lower()


def contains_street(text):
    return re.match(r'^[a-zA-Zöäü\s]+ [0-9]+', text) and True or False


def contains_location(text):
    return re.match(r'^[0-9]+ [a-zA-Zöäü\s]+', text) and True or False


def contains_website(text):
    return not contains_email(text) and '.ch' in text or 'www.' in text


def contains_email(text):
    return '@' in text


def pop_matching(lines, predicate):
    for ix, line in enumerate(lines):
        if predicate(line):
            break
    else:
        return None

    return lines.pop(ix)


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

            lines = html_to_text(desc).split('\n\n')

            if len(lines) < 6:
                print(f"Could not parse a description for {uid}:")
                print(desc)
                continue

            yield cls(**match_address(lines))


def get_metadata(title, lead, structure, title_format, lead_format,
                 content_fields, contact_fields, keyword_fields):

    fieldnames = tuple(
        f.human_id for f in flatten_fieldsets(parse_formcode(structure))
    )

    return {
        'type': 'extended',
        'name': normalize_for_url(title),
        'title': title,
        'lead': lead,
        'structure': structure,
        'configuration': {
            'title': title_format,
            'lead': lead_format,
            'display': {
                'contact': contact_fields,
                'content': content_fields,
            },
            'keywords': keyword_fields,
            'searchable': fieldnames,
            'order': safe_format_keys(title_format)
        }
    }


def load_files(path, prefix):
    chapters, links, institutions = None, None, None

    for p in Path(path).glob(f'{prefix}*'):
        if 'chapter_theme' in p.name:
            chapters = CSVFile(p.open('rb'), (
                'chapter_uid',
                'chapter',
                'topic',
                'topic_pid'
            ))

        if 'chapter_mm_vollzugsbehoerden' in p.name:
            links = CSVFile(p.open('rb'), (
                'uid_local',
                'uid_foreign',
                'sorting'
            ))
            continue

        if 'institution_vollzugsbehoerden' in p.name:
            institutions = CSVFile(p.open('rb'), (
                'uid',
                'institution',
                'description'
            ))
            continue

    assert None not in (chapters, links, institutions)

    return chapters, links, institutions


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

    # hierarchy of categories
    hierarchy = []

    for i in institutions.lines:
        task = i.institution
        chapter = chapters[i.uid]

        if task and chapter and chapter in topics:
            topic = topics[chapter]
            hierarchy.append(f'{topic} :: {chapter} :: {task}')

    institutions = sorted([i for i in result.values()], key=lambda i: i.title)
    return sorted(hierarchy), institutions


def transform_vollzug(path, prefix, output_file):
    hierarchy, institutions = get_institutions(path, prefix)

    def unique_values(values, attr):
        unique = set()

        for value in values:
            unique.update(getattr(value, attr))

        return sorted(list(unique))

    def as_choices(values, indent=16):
        return textwrap.indent(
            '\n'.join(f'[ ] {v}' for v in values),
            ' ' * 16,
            lambda line: not values[0].endswith(line.split(']')[-1].strip())
        )

    topics = as_choices(unique_values(institutions, 'topics'))
    chapters = as_choices(unique_values(institutions, 'chapters'))

    metadata = get_metadata(
        title='Vollzugsbehörden',
        lead='Die Volzugsbehörden der Stadt Winterthur',
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

            Vollzugsbereiche =
                {chapters}

            Vollzugsaufgaben = ...[16]
        """))

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
            'Kategorie/Vollzugsbereiche': list(i.chapters),
            'Kategorie/Vollzugsaufgaben': '\n'.join(
                f'- {t}' for t in sorted(list(i.tasks))
            ),
            'Latitude': geocode(i.address)[0],
            'Longitude': geocode(i.address)[1],
        } for i in institutions
    ]

    with tempfile.TemporaryDirectory() as directory:

        with (Path(directory) / 'metadata.json').open('w') as f:
            f.write(json.dumps(metadata))

        with (Path(directory) / 'data.json').open('w') as f:
            f.write(json.dumps(data))

        with (Path(directory) / 'hierarchy.json').open('w') as f:
            f.write(json.dumps(hierarchy))

        shutil.make_archive(output_file.split('.')[0], 'zip', directory)
