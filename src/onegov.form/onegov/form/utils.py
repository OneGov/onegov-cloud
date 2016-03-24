import re

from unidecode import unidecode

_unwanted_characters = re.compile(r'[^a-zA-Z0-9]+')


def label_to_field_id(label):
    clean = unidecode(label).strip(' ').lower()
    clean = _unwanted_characters.sub('_', clean)

    return clean


def get_fields_from_class(cls):
    fields = []

    for name in dir(cls):
        if not name.startswith('_'):
            field = getattr(cls, name)

            if hasattr(field, '_formfield'):
                fields.append((name, field))

    fields.sort(key=lambda x: (x[1].creation_counter, x[0]))

    return fields
