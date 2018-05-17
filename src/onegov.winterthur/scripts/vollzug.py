import attr
import json
import re
import shutil
import tempfile
import textwrap

from onegov.core.csv import CSVFile
from onegov.core.html import html_to_text
from onegov.core.utils import normalize_for_url
from onegov.form import flatten_fieldsets, parse_formcode
from pathlib import Path


@attr.s(auto_attribs=True)
class Institution(object):
    name: str
    department: str
    branch: str
    chapter: str
    address: str
    phone: str = None
    email: str = None
    website: str = None
    tasks: set = attr.Factory(set)

    @property
    def title(self):
        return ' - '.join(part for part in (
            self.department,
            self.name,
            self.branch
        ) if part)


def get_metadata(title, structure):
    fieldnames = tuple(
        f.human_id for f in flatten_fieldsets(parse_formcode(structure))
    )

    return {
        'type': 'extended',
        'name': normalize_for_url(title),
        'title': title,
        'lead': '',
        'structure': structure,
        'configuration': {
            'title': f'[{fieldnames[0]}]',
            'display': {
                'contact': [],
                'content': fieldnames
            },
            'keywords': [],
            'searchable': fieldnames,
            'order': [
                fieldnames[0]
            ],
        }
    }


def load_files(path, prefix):
    chapters, links, institutions = None, None, None

    for p in Path(path).glob(f'{prefix}*'):
        if 'chapter_vollzugsbehoerden' in p.name:
            chapters = CSVFile(p.open('rb'), (
                'uid',
                'chapter'
            ))
            continue

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


def parse_description(uid, description):
    description = description.replace('Tel.:', '')

    for desc in description.split('</td>'):
        lines = html_to_text(desc).split('\n\n')

        if len(lines) <= 1:
            continue

        if len(lines) < 6:
            print(f"Could not parse a description for {uid}:")
            print(desc)
            continue

        department = lines.pop(0).strip()
        name = lines.pop(0).strip()
        branch = lines.pop(0).strip()
        website = lines.pop(-1).strip()
        email = lines.pop(-1).strip()
        phone = lines.pop(-1).strip()
        address = '\n'.join(lines)

        if re.search(r'[0-9]+', branch):
            address = branch + '\n' + address
            branch = ''

        yield {
            'department': department,
            'name': name,
            'branch': branch,
            'website': website,
            'email': email,
            'phone': phone,
            'address': address
        }


def get_institutions(path, prefix):
    chapters, links, institutions = load_files(path, prefix)

    chapters = {c.uid: c.chapter for c in chapters.lines}
    chapters = {l.uid_local: chapters.get(l.uid_foreign) for l in links.lines}

    result = {}

    for record in institutions.lines:
        task = record.institution

        for data in parse_description(record.uid, record.description):
            data['chapter'] = chapters[record.uid]

            institution = Institution(**data)

            if institution.title in result:
                institution = result[institution.title]
            else:
                result[institution.title] = institution

            institution.tasks.add(task)

    return list(result.values())


def transform_vollzug(path, prefix, output_file='vollzug.zip'):
    institutions = get_institutions(path, prefix)

    chapters = sorted(list({i.chapter for i in institutions}))
    chapters = textwrap.indent(
        '\n'.join(f'[ ] {chapter}' for chapter in chapters),
        ' ' * 16,
        lambda line: not chapters[0].endswith(line.split(']')[-1].strip())
    )

    metadata = get_metadata(
        title='Vollzugsbehörden',
        structure=textwrap.dedent(f"""\
            # Fachstelle
            Titel *= ___
            Name *= ___
            Department *= ___
            Abteilung = ___

            # Kontakt
            Adresse = ...
            E-Mail = ___
            Telefon = ___
            Webseite = ___

            # Kategorie
            Vollzugsbereich =
                {chapters}

            Vollzugsaufgaben = ...[16]
        """))

    data = [
        {
            'Fachstelle/Titel': i.title,
            'Fachstelle/Name': i.name,
            'Fachstelle/Department': i.department,
            'Fachstelle/Abteilung': i.branch,
            'Kontakt/Adresse': i.address,
            'Kontakt/E-Mail': i.email,
            'Kontakt/Telefon': i.phone,
            'Kontakt/Webseite': i.website,
            'Kategorie/Vollzugsbereich': [i.chapter],
            'Kategorie/Vollzugsaufgaben': '\n'.join(
                f'- {t}' for t in sorted(list(i.tasks))
            )
        } for i in institutions
    ]

    with tempfile.TemporaryDirectory() as directory:

        with (Path(directory) / 'metadata.json').open('w') as f:
            f.write(json.dumps(metadata))

        with (Path(directory) / 'data.json').open('w') as f:
            f.write(json.dumps(data))

        shutil.make_archive(output_file.split('.')[0], 'zip', directory)
