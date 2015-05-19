import re

from unidecode import unidecode

_unwanted_characters = re.compile(r'[^a-zA-Z0-9]+')


def label_to_field_id(label):
    clean = unidecode(label).strip(' ').lower()
    clean = _unwanted_characters.sub('_', clean)

    return clean
