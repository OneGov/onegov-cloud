from bleach.sanitizer import Cleaner
from onegov.form.fields import HtmlField as HtmlFieldBase
from onegov.form.fields import MultiCheckboxField as MultiCheckboxFieldBase
from wtforms import SelectField as SelectFieldBase
from onegov.gazette import _


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


class MultiCheckboxField(MultiCheckboxFieldBase):
    """ A multi checkbox field where only the first elements are display and
    the the rest can be shown when needed. """

    def __init__(self, *args, **kwargs):
        if 'render_kw' not in kwargs or not kwargs['render_kw'].get('class_'):
            kwargs['render_kw'] = kwargs.get('render_kw', {})
            kwargs['render_kw']['data-limit'] = str(kwargs.pop('limit', 10))
            kwargs['render_kw']['data-expand-title'] = _("Show all")

        super().__init__(*args, **kwargs)

    def translate(self, request):
        self.render_kw['data-expand-title'] = request.translate(
            self.render_kw['data-expand-title']
        )
