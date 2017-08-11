from bleach.sanitizer import Cleaner
from onegov.form.fields import HtmlField as HtmlFieldBase
from wtforms import SelectField as SelectFieldBase


cleaner = Cleaner(
    tags=['br', 'em', 'p', 'strong'],
    attributes={},
    strip=True
)


class HtmlField(HtmlFieldBase):
    """ A textfield with html with integrated sanitation.

    We need a much stricter sanitation than the normal editor uses.

    """

    def pre_validate(self, form):
        self.data = cleaner.clean(self.data)


class SelectField(SelectFieldBase):
    """ A select field with chosen support. """

    def __init__(self, *args, **kwargs):
        if 'render_kw' not in kwargs or not kwargs['render_kw'].get('class_'):
            kwargs['render_kw'] = kwargs.get('render_kw', {})
            kwargs['render_kw']['class_'] = 'chosen-select'

        super().__init__(*args, **kwargs)
