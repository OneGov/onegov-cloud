from onegov.core.html import sanitize_html
from onegov.org.utils import annotate_html
from wtforms.fields import TextAreaField


class HtmlField(TextAreaField):
    """ A textfield with html with integrated sanitation and annotation,
    cleaning the html and adding extra information including setting the
    image size by querying the database.

    """

    def __init__(self, *args, **kwargs):
        self.form = kwargs.get('_form')

        if 'render_kw' not in kwargs or not kwargs['render_kw'].get('class_'):
            kwargs['render_kw'] = kwargs.get('render_kw', {})
            kwargs['render_kw']['class_'] = 'editor'

        super().__init__(*args, **kwargs)

    def pre_validate(self, form):
        self.data = annotate_html(sanitize_html(self.data), form.request)
