from bleach.sanitizer import Cleaner
from onegov.quill.widgets import QuillInput
from onegov.quill.widgets import TAGS
from wtforms import TextAreaField


class QuillField(TextAreaField):
    """ A textfield using the quill editor and with integrated sanitation.

    Allows to specifiy which tags to use in the editor and for sanitation.
    Available tags are: strong, em, ol and ul (p and br tags are always
    possible).

    Allows to provide a dictionary of placeholders/snippets.

    """

    def __init__(self, **kwargs):
        tags = list(set(kwargs.pop('tags', TAGS)) & set(TAGS))
        placeholders = kwargs.pop('placeholders', {})
        placeholder_label = kwargs.pop('placeholder_label', 'Snippets')
        super(TextAreaField, self).__init__(**kwargs)

        self.widget = QuillInput(
            tags=tags,
            placeholders=placeholders,
            placeholder_label=placeholder_label
        )

        tags = ['p', 'br'] + tags
        if 'ol' in tags or 'ul' in tags:
            tags.append('li')

        attributes = {}
        if 'a' in tags:
            attributes['a'] = ['href']

        self.cleaner = Cleaner(tags=tags, attributes=attributes, strip=True)

    def pre_validate(self, form):
        self.data = self.cleaner.clean(self.data or '')

    def translate(self, request):
        self.widget.placeholder_label = request.translate(
            self.widget.placeholder_label
        )
