from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.widgets import ChosenSelectWidget
from onegov.swissvotes.models import PolicyArea


class PolicyAreaWidget(ChosenSelectWidget):
    """ The widget for the chosen field.

    Adds custom classes based on provided value.

    """

    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        kwargs['class'] = 'level-{}'.format(PolicyArea(value).level)
        return super(PolicyAreaWidget, cls).render_option(
            value, label, selected, **kwargs
        )


class PolicyAreaField(ChosenSelectMultipleField):
    """ A select field with chosen support. """

    widget = PolicyAreaWidget(multiple=True)
