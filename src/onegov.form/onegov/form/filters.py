def as_float(value):
    return value and float(value) or 0.0


def strip_whitespace(value):
    return value and value.strip(' \r\n') or None


def yubikey_identifier(value):
    return value and value[:12] or ''
