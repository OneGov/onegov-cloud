from wtforms.widgets import HiddenInput
from wtforms.widgets.core import HTMLString


class QuillInput(HiddenInput):
    """
    Renders the text content as hidden input and adds a container for the
    editor.


    """

    def __call__(self, field, **kwargs):
        kwargs['class_'] = (kwargs.get('class_', '') + ' quill').strip()

        input_html = super(QuillInput, self).__call__(field, **kwargs)
        return HTMLString("""
            <div class="quill-container"></div>
            {}
        """.format(input_html))
