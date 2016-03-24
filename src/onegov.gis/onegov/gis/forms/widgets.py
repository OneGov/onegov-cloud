from wtforms.widgets import TextInput


class CoordinatesWidget(TextInput):
    """ Widget holding and showing the data behind the
    :class:`onegov.gis.forms.fields.CoordinatesField` class.

    Basically a textfield that stores json. Meant to be enhanced on the browser
    using javascript.

    """

    def __call__(self, field, **kwargs):
        kwargs['class_'] = (kwargs.get('class_', '') + ' coordinates').strip()
        return super().__call__(field, **kwargs)
