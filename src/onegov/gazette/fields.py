from onegov.form.fields import MultiCheckboxField as MultiCheckboxFieldBase
from onegov.form.widgets import MultiCheckboxWidget as MultiCheckboxWidgetBase
from onegov.gazette import _


class MultiCheckboxWidget(MultiCheckboxWidgetBase):

    def __call__(self, field, **kwargs):
        kwargs['data-expand-title'] = field.gettext(_("Show all"))
        kwargs['data-fold-title'] = field.gettext(_("Show less"))

        return super(MultiCheckboxWidgetBase, self).__call__(field, **kwargs)


class MultiCheckboxField(MultiCheckboxFieldBase):
    """ A multi checkbox field where only the first elements are display and
    the the rest can be shown when needed.

    """

    widget = MultiCheckboxWidget()

    def __init__(self, *args, **kwargs):
        render_kw = kwargs.pop('render_kw', {})
        render_kw['data-limit'] = str(kwargs.pop('limit', 5))
        kwargs['render_kw'] = render_kw

        super().__init__(*args, **kwargs)
