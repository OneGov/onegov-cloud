from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy_utils.operators import CaseInsensitiveComparator


class LowercaseText(TypeDecorator):
    """ Text column that forces all text to be lowercase. """

    impl = TEXT
    omparator_factory = CaseInsensitiveComparator

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.lower()

        return value
