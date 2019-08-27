from contextlib import suppress

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


def parse_donation_amounts(text):
    lines = (l.strip() for l in text.splitlines())
    lines = (l for l in lines if l)

    def amounts():
        for line in lines:
            with suppress(ValueError):
                amount = float(line)
                amount = round(.05 * round(amount / .05), 2)

                yield amount

    return tuple(amounts())


def format_donation_amounts(amounts):
    def lines():
        for amount in amounts:
            if float(amount).is_integer():
                yield f'{int(amount):d}'
            else:
                yield f'{amount:.2f}'

    return '\n'.join(lines())
