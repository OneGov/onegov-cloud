class FormError(Exception):
    pass


class DuplicateLabelError(FormError):

    def __init__(self, label: str):
        self.label = label

    def __repr__(self) -> str:
        return f"DuplicateLabelError(label='{self.label}')"


class InvalidMimeType(FormError):
    pass


class UnableToComplete(FormError):
    pass


class InvalidFormSyntax(FormError):
    def __init__(self, line: int):
        self.line = line


class InvalidIndentSyntax(FormError):
    def __init__(self, line: int):
        self.line = line


class EmptyFieldsetError(FormError):
    def __init__(self, field_name: str):
        self.field_name = field_name


class FieldCompileError(FormError):
    def __init__(self, field_name: str):
        self.field_name = field_name


class MixedTypeError(FormError):
    def __init__(self, field_name: str):
        self.field_name = field_name
