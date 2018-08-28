from wtforms import SelectMultipleField
from wtforms.widgets import Select
from onegov.swissvotes.models import PolicyArea


class PolicyAreaWidget(Select):
    """ The widget for the chosen field.

    Adds custom classes based on provided value.

    """

    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        kwargs['class'] = 'level-{}'.format(PolicyArea(value).level)
        return super(PolicyAreaWidget, cls).render_option(
            value, label, selected, **kwargs
        )


class PolicyAreaField(SelectMultipleField):
    """ A select field with chosen support. """

    widget = PolicyAreaWidget(multiple=True)

    def __init__(self, *args, **kwargs):
        render_kw = kwargs.pop('render_kw', {})
        render_kw['class_'] = 'chosen-select'
        kwargs['render_kw'] = render_kw

        super().__init__(*args, **kwargs)
