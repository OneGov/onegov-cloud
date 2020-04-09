class FormError(Exception):
    pass


class DuplicateLabelError(FormError):

    def __init__(self, label):
        self.label = label

    def __repr__(self):
        return "DuplicateLabelError(label='{}')".format(self.label)


class InvalidMimeType(FormError):
    pass


class UnableToComplete(FormError):
    pass


class InvalidFormSyntax(FormError):
    def __init__(self, line):
        self.line = line


class FieldCompileError(FormError):
    def __init__(self, field_name):
        self.field_name = field_name
