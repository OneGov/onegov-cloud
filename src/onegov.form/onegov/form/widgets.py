import chameleon
import humanize

from cgi import escape
from onegov.form import _
from wtforms.widgets import ListWidget, FileInput, TextInput
from wtforms.widgets.core import HTMLString


class OrderedListWidget(ListWidget):
    """ Extends the default list widget with automated ordering using the
    translated text of each element.

    """

    def __call__(self, field, **kwargs):

        # ListWidget expects a field internally, but it will only use
        # its id property and __iter__ method, so we can get away
        # with passing a fake field with an id and an iterator.
        #
        # It's not great, since we have to assume internal knowledge,
        # but builting a new field or changing the existing one would
        # require even more knowledge, so this is the better approach
        #
        # We also need to call each field once so it gets hooked up with
        # our translation machinary
        ordered = [subfield for subfield in field]
        ordered.sort(key=lambda f: (f(), str(f.label.text))[1])

        class FakeField(object):

            id = field.id

            def __iter__(self):
                return iter(ordered)

        return super().__call__(FakeField(), **kwargs)


class MultiCheckboxWidget(ListWidget):
    """ The default list widget with the label behind the checkbox. """

    def __init__(self, *args, **kwargs):
        kwargs['prefix_label'] = False
        super().__init__(*args, **kwargs)


class OrderedMultiCheckboxWidget(MultiCheckboxWidget, OrderedListWidget):
    """ The sorted list widget with the label behind the checkbox. """
    pass


class CoordinateWidget(TextInput):
    """ Widget containing the coordinates for the
    :class:`onegov.form.fields.CoordinateField` class.

    Basically a text input with a class. Meant to be enhanced on the browser
    using javascript.

    """

    def __call__(self, field, **kwargs):
        kwargs['class_'] = (kwargs.get('class_', '') + ' coordinate').strip()
        return super().__call__(field, **kwargs)


class UploadWidget(FileInput):
    """ An upload widget for the :class:`onegov.form.fields.UploadField` class,
    which supports keeping, removing and replacing already uploaded files.

    This is necessary as file inputs are read-only on the client and it's
    therefore rather easy for users to lose their input otherwise (e.g. a
    form with a file is rejected because of some mistake - the file disappears
    once the response is rendered on the client).

    """

    def __call__(self, field, **kwargs):
        force_simple = kwargs.pop('force_simple', False)
        input_html = super().__call__(field, **kwargs)

        if force_simple or field.errors or not field.data:
            return HTMLString("""
                <div class="upload-widget without-data">
                    {}
                </div>
            """.format(input_html))
        else:
            return HTMLString("""
                <div class="upload-widget with-data">
                    <p>{existing_file_label}: {filename} ({filesize}) ✓</p>
                    <ul>
                        <li>
                            <input type="radio" id="{name}-0" name="{name}"
                                   value="keep" checked="">
                            <label for="{name}-0">{keep_label}</label>
                        </li>
                        <li>
                            <input type="radio" id="{name}-1" name="{name}"
                                   value="delete">
                            <label for="{name}-1">{delete_label}</label>
                        </li>
                        <li>
                            <input type="radio" id="{name}-2" name="{name}"
                                   value="replace">
                            <label for="{name}-2">{replace_label}</label>
                            <div>
                                <label>
                                    <div data-depends-on="{name}/replace"
                                         data-hide-label="false">
                                        {input_html}
                                    </div>
                                </label>
                            </div>
                        </li>
                    </ul>
                </div>
            """.format(
                # be careful, we do our own html generation here without any
                # safety harness - we need to carefully escape values the user
                # might supply
                filesize=humanize.naturalsize(field.data['size']),
                filename=escape(field.data['filename'], quote=True),
                name=field.id,
                input_html=input_html,
                existing_file_label=field.gettext(_('Uploaded file')),
                keep_label=field.gettext(_('Keep file')),
                delete_label=field.gettext(_('Delete file')),
                replace_label=field.gettext(_('Replace file'))
            ))


class TagsWidget(TextInput):
    # for use with https://github.com/developit/tags-input
    input_type = 'tags'


class IconWidget(TextInput):

    iconfont = 'FontAwesome'
    icons = (
        '&#xf111',  # fa-circle
        '&#xf005',  # fa-star
        '&#xf06a',  # fa-exclamation-circle
        '&#xf059',  # fa-question-circle
        '&#xf05e',  # fa-ban
        '&#xf1b9',  # fa-car
        '&#xf238',  # fa-train
        '&#xf206',  # fa-bicycle
        '&#xf291',  # fa-shopping-basket
        '&#xf1b0',  # fa-paw
        '&#xf1ae',  # fa-child
        '&#xf06d',  # fa-fire
        '&#xf1f8',  # fa-trash
        '&#xf236',  # fa-hotel
        '&#xf0f4',  # fa-coffee
        '&#xf017',  # fa-click
    )

    template = chameleon.PageTemplate("""
        <div class="icon-widget">
            <ul style="font-family: ${iconfont}">
                <li
                    tal:repeat="icon icons"
                    tal:content="structure icon"
                />
            </ul>

            <input type="hidden" name="${id}" value="${structure: value}">
        </div>
    """)

    def __call__(self, field, **kwargs):
        iconfont = kwargs.pop('iconfont', self.iconfont)
        icons = kwargs.pop('icons', self.icons)

        return HTMLString(self.template.render(
            iconfont=iconfont,
            icons=icons,
            id=field.id,
            value=field.data or icons[0]
        ))
