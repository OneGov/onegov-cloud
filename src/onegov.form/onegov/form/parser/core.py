from onegov.form.parser import grammar
from pyparsing import ParseException


class FieldSet(list):

    def __init__(self, *args, **kwargs):
        self.label = kwargs.pop('label', None)


class Field(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TextField(Field):
    pass


class TextAreaField(Field):
    pass


def parse(text):

    collection = FieldSet()

    for lineno, line in enumerate(text.split('\n')):
        line = line.strip()

        if not line:
            continue

        try:
            parsed = grammar.line.parseString(line)
        except ParseException as e:
            e.lineno = lineno
            raise e

        if parsed.type == 'fieldset':
            if collection:
                yield collection

            collection = FieldSet(label=parsed.label)

        else:
            collection.append(parsed)

    yield collection
