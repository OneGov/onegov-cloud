import csv
import json
import re
import shutil
import tempfile
import textwrap

from collections import namedtuple
from geopy.geocoders import Nominatim
from onegov.core.cache import lru_cache
from onegov.core.csv import CSVFile
from onegov.core.html import html_to_text as core_html_to_text
from onegov.core.utils import normalize_for_url, safe_format_keys
from onegov.form import flatten_fieldsets, parse_formcode
from pathlib import Path


Point = namedtuple('Point', ('latitude', 'longitude'))


class Geocoder(object):

    def __init__(self):
        self.nominatim = Nominatim(user_agent='onegov-cloud-import')

    @lru_cache(maxsize=1024)
    def geocode(self, address):
        result = self.nominatim.geocode(address)
        return Point(
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


def build_metadata(title, lead, structure, title_format, lead_format,
                   content_fields, contact_fields, keyword_fields,
                   link_pattern=None, link_title=None, **extra):

    print(structure)

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
            'order': safe_format_keys(title_format),
            'link_pattern': link_pattern,
            'link_title': link_title
        },
        **extra
    }


def load_files_by_prefix(path, prefix, mapping):
    files = []

    dialect = csv.excel

    for name, fields in mapping:
        for p in Path(path).glob(f'{prefix}*'):
            if name in p.name:
                files.append(CSVFile(
                    csvfile=p.open('rb'),
                    expected_headers=fields,
                    dialect=dialect
                ))
                break

    assert all(files)
    assert len(files) == len(mapping)

    return files[0] if len(files) == 1 else files


def as_choices(values, indent=16):
    return textwrap.indent(
        '\n'.join(f'[ ] {v}' for v in values),
        ' ' * 16,
        lambda line: not values[0] == line.split(']')[-1].strip()
    )


def store_in_zip(output_file, data):
    with tempfile.TemporaryDirectory() as directory:

        for filename, data in data.items():
            with (Path(directory) / filename).open('w') as f:
                f.write(json.dumps(data))

        shutil.make_archive(output_file.split('.')[0], 'zip', directory)


def html_to_text(html):
    return core_html_to_text(
        html,
        ul_item_mark='•',
        strong_mark='',
        emphasis_mark=''
    ).replace('\n\n', '\n')
