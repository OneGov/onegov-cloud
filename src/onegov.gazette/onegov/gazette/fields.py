from onegov.form.fields import MultiCheckboxField as MultiCheckboxFieldBase
from wtforms import SelectField as SelectFieldBase
from onegov.gazette import _


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
            kwargs['render_kw']['data-fold-title'] = _("Show less")

        super().__init__(*args, **kwargs)

    def translate(self, request):
        self.render_kw['data-expand-title'] = request.translate(
            self.render_kw['data-expand-title']
        )
        self.render_kw['data-fold-title'] = request.translate(
            self.render_kw['data-fold-title']
        )
