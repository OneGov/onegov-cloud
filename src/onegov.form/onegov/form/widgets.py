import humanize

from cgi import escape
from onegov.form import _
from wtforms.widgets import ListWidget, FileInput, TextInput
from wtforms.widgets.core import HTMLString


class MultiCheckboxWidget(ListWidget):
    """ The default wtforms ListWidget, extended different default values. """

    def __init__(self, *args, **kwargs):
        kwargs['prefix_label'] = False
        super().__init__(*args, **kwargs)


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

        if force_simple or not field.data:
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
                            <label for="{name}-0">{keep_label}</label
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
