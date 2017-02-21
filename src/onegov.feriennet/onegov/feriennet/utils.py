NAME_SEPARATOR = '\u00A0'  # non-breaking space


def encode_name(first_name, last_name):
    names = (first_name, last_name)
    names = (n.replace(NAME_SEPARATOR, ' ') for n in names)
    return NAME_SEPARATOR.join(names)


def decode_name(fullname):
    if fullname:
        names = fullname.split(NAME_SEPARATOR)
    else:
        names = None

    if not names:
        return None, None
    if len(names) <= 1:
        return names[0], None
    else:
        return names
