from onegov.quill.widgets import QuillInput
from bleach.sanitizer import Cleaner
from wtforms import TextAreaField


cleaner = Cleaner(
    tags=['br', 'em', 'p', 'strong', 'ol', 'ul', 'li'],
    attributes={},
    strip=True
)


class QuillField(TextAreaField):
    """ A textfield with html with integrated sanitation. """

    widget = QuillInput()

    def pre_validate(self, form):
        self.data = cleaner.clean(self.data)
