""" Contains renderers to display form fields. """

import humanize

from html import escape
from onegov.form import log


__all__ = ['render_field']


class Registry(object):
    """ Keeps track of all the renderers and the types they are registered for,
    making sure each renderer is only instantiated once.

    """
    def __init__(self):
        self.renderer_map = {}

    def register_for(self, *types):
        """ Decorator to register a renderer. """
        def wrapper(renderer):
            instance = renderer()

            for type in types:
                self.renderer_map[type] = instance

            return renderer
        return wrapper

    def render(self, field):
        """ Renders the given field with the correct renderer. """
        # no point rendering empty fields
        if not field.data:
            return ''

        renderer = self.renderer_map.get(field.type)

        if renderer is None:
            log.warning('No renderer found for {}'.format(field.type))
            return ''
        else:
            return renderer(field)


registry = Registry()

# public interface
render_field = registry.render


class BaseRenderer(object):
    """ Provides utility functions for all renderers. """

    def escape(self, text):
        return escape(text, quote=True)


@registry.register_for(
    'StringField',
    'TextField',
    'TextAreaField',
)
class StringFieldRenderer(BaseRenderer):
    def __call__(self, field):
        return self.escape(field.data).replace('\n', '<br>')


@registry.register_for('PasswordField')
class PasswordFieldRenderer(BaseRenderer):
    def __call__(self, field):
        return '*' * len(field.data)


@registry.register_for('EmailField')
class EmailFieldRenderer(BaseRenderer):
    def __call__(self, field):
        return '<a href="mailto:{mail}">{mail}</a>'.format(
            mail=self.escape(field.data))


@registry.register_for('URLField')
class URLFieldRenderer(BaseRenderer):
    def __call__(self, field):
        return '<a href="{url}">{url}</a>'.format(
            url=self.escape(field.data))


@registry.register_for('DateField')
class DateFieldRenderer(BaseRenderer):
    # XXX we assume German here currently - should this change we'd have
    # to add a date format to the request and pass it here - which should
    # be doable with little work (not necessary for now)
    date_format = '%d.%m.%Y'

    def __call__(self, field):
        return field.data.strftime(self.date_format)


@registry.register_for('DateTimeLocalField')
class DateTimeLocalFieldRenderer(DateFieldRenderer):
    date_format = '%d.%m.%Y %H:%M'


@registry.register_for('TimeField')
class TimeFieldRenderer(BaseRenderer):
    def __call__(self, field):
        return '{:02d}:{:02d}'.format(field.data.hour, field.data.minute)


@registry.register_for('UploadField')
class UploadFieldRenderer(BaseRenderer):

    def __call__(self, field):
        return '{filename} ({size})'.format(
            filename=self.escape(field.data['filename']),
            size=humanize.naturalsize(field.data['size'])
        )


@registry.register_for('RadioField')
class RadioFieldRenderer(BaseRenderer):

    def __call__(self, field):
        return "✓ " + self.escape(dict(field.choices)[field.data])


@registry.register_for('MultiCheckboxField')
class MultiCheckboxFieldRenderer(BaseRenderer):

    def __call__(self, field):
        return "".join(
            "✓ " + self.escape(dict(field.choices)[value]) + '<br>'
            for value in field.data
        )[:-4]


@registry.register_for('CSRFTokenField', 'HiddenField')
class NullRenderer(BaseRenderer):
    def __call__(self, field):
        return ''


@registry.register_for('DecimalField')
class DecimalRenderer(BaseRenderer):
    def __call__(self, field):
        return '{:.2f}'.format(field.data)


@registry.register_for('IntegerField')
class IntegerRenderer(BaseRenderer):
    def __call__(self, field):
        return '{}'.format(int(field.data))
