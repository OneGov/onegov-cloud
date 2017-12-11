from onegov.form.fields import MultiCheckboxField as MultiCheckboxFieldBase
from onegov.gazette import _
from wtforms import SelectField as SelectFieldBase
from wtforms.fields.html5 import DateTimeLocalField as DateTimeLocalFieldBase


class SelectField(SelectFieldBase):
    """ A select field with chosen support. """

    def __init__(self, *args, **kwargs):
        render_kw = kwargs.pop('render_kw', {})
        render_kw['class_'] = 'chosen-select'
        kwargs['render_kw'] = render_kw

        super().__init__(*args, **kwargs)


class MultiCheckboxField(MultiCheckboxFieldBase):
    """ A multi checkbox field where only the first elements are display and
    the the rest can be shown when needed.

    Also, disables all the options if the whole field is disabled.
    """

    def __init__(self, *args, **kwargs):
        render_kw = kwargs.pop('render_kw', {})
        render_kw['data-limit'] = str(kwargs.pop('limit', 10))
        render_kw['data-expand-title'] = _("Show all")
        render_kw['data-fold-title'] = _("Show less")
        kwargs['render_kw'] = render_kw

        super().__init__(*args, **kwargs)

    def translate(self, request):
        self.render_kw['data-expand-title'] = request.translate(
            self.render_kw['data-expand-title']
        )
        self.render_kw['data-fold-title'] = request.translate(
            self.render_kw['data-fold-title']
        )

    def __iter__(self):
        for opt in super(MultiCheckboxField, self).__iter__():
            if 'disabled' in self.render_kw:
                opt.render_kw = opt.render_kw or {}
                opt.render_kw['disabled'] = self.render_kw['disabled']
            yield opt


class DateTimeLocalField(DateTimeLocalFieldBase):
    """ A custom implementation of the DateTimeLocalField to fix issues with
    the format and the datetimepicker plugin.

    """

    def __init__(self, **kwargs):
        kwargs['format'] = '%Y-%m-%dT%H:%M'
        super(DateTimeLocalField, self).__init__(**kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            valuelist = [' '.join(valuelist).replace(' ', 'T')]
        super(DateTimeLocalField, self).process_formdata(valuelist)
