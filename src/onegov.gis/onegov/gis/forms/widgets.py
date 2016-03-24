from wtforms.widgets import TextInput


class MapPointWidget(TextInput):
    """ Widget containing the point for the
    :class:`onegov.gis.forms.fields.MapPointField` class.

    Basically a text input with a class. Meant to be enhanced on the browser
    using javascript.

    """

    def __call__(self, field, **kwargs):
        kwargs['class_'] = (kwargs.get('class_', '') + ' map-point').strip()
        return super().__call__(field, **kwargs)
