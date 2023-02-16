import humanize

from contextlib import suppress
from markupsafe import Markup
from morepath.error import LinkError
from onegov.chat import TextModuleCollection
from onegov.core.templates import PageTemplate
from onegov.file.utils import IMAGE_MIME_TYPES_AND_SVG
from onegov.form import _
from wtforms.widgets import FileInput
from wtforms.widgets import ListWidget
from wtforms.widgets import Select
from wtforms.widgets import TextArea
from wtforms.widgets import TextInput
from wtforms.widgets.core import html_params


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

        class FakeField:

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

    def image_source(self, field):
        """ Returns the image source url if the field points to an image and
        if it can be done (it looks like it's possible, but I'm not super
        sure this is always possible).

        """

        if not hasattr(field.meta, 'request'):
            return

        if not field.data:
            return

        if not field.data.get('mimetype', None) in IMAGE_MIME_TYPES_AND_SVG:
            return

        if not hasattr(field, 'object_data'):
            return

        if not field.object_data:
            return

        with suppress(LinkError, AttributeError):
            return field.meta.request.link(field.object_data)

    def __call__(self, field, **kwargs):
        force_simple = kwargs.pop('force_simple', False)
        resend_upload = kwargs.pop('resend_upload', False)
        wrapper_css_class = kwargs.pop('wrapper_css_class', '')
        if wrapper_css_class:
            wrapper_css_class = ' ' + wrapper_css_class
        input_html = super().__call__(field, **kwargs)

        if force_simple or field.errors or not field.data:
            return Markup("""
                <div class="upload-widget without-data{}">
                    {}
                </div>
            """).format(wrapper_css_class, input_html)
        else:
            preview = ''
            src = self.image_source(field)
            if src:
                preview = Markup("""
                    <div class="uploaded-image"><img src="{src}"></div>
                """).format(src=src)

            previous = ''
            if field.data and resend_upload:
                previous = Markup("""
                    <input type="hidden" name="{name}" value="{filename}">
                    <input type="hidden" name="{name}" value="{data}">
                """).format(
                    name=field.id,
                    filename=field.data.get('filename', ''),
                    data=field.data.get('data', ''),
                )

            return Markup("""
                <div class="upload-widget with-data{wrapper_css_class}">
                    <p>{existing_file_label}: {filename} ({filesize}) ✓</p>

                    {preview}

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

                    {previous}
                </div>
            """).format(
                filesize=humanize.naturalsize(field.data['size']),
                filename=field.data['filename'],
                wrapper_css_class=wrapper_css_class,
                name=field.id,
                input_html=input_html,
                existing_file_label=field.gettext(_('Uploaded file')),
                keep_label=field.gettext(_('Keep file')),
                delete_label=field.gettext(_('Delete file')),
                replace_label=field.gettext(_('Replace file')),
                preview=preview,
                previous=previous
            )


class UploadMultipleWidget(FileInput):
    """ A widget for the :class:`onegov.form.fields.UploadMultipleField` class,
    which supports keeping, removing and replacing already uploaded files.

    This is necessary as file inputs are read-only on the client and it's
    therefore rather easy for users to lose their input otherwise (e.g. a
    form with a file is rejected because of some mistake - the file disappears
    once the response is rendered on the client).

    We deviate slightly from the norm by rendering the errors ourselves
    since we're essentially a list of fields and not a single field most
    of the time.

    """

    def __init__(self):
        self.multiple = True

    def __call__(self, field, **kwargs):
        force_simple = kwargs.pop('force_simple', False)
        resend_upload = kwargs.pop('resend_upload', False)
        input_html = super().__call__(field, **kwargs)
        simple_template = Markup("""
            <div class="upload-widget without-data">
                {}
            </div>
        """)

        if force_simple or len(field) == 0:
            return simple_template.format(input_html)
        else:
            existing_html = Markup('').join(
                subfield(
                    force_simple=force_simple,
                    resend_upload=resend_upload,
                    wrapper_css_class='error' if subfield.errors else '',
                    **kwargs
                ) + Markup('\n').join(
                    Markup('<small class="error">{}</small>').format(error)
                    for error in subfield.errors
                ) for subfield in field
            )
            additional_html = Markup('{label}: {input_html}').format(
                label=field.gettext(_('Upload additional files')),
                input_html=input_html
            )
            return existing_html + simple_template.format(additional_html)


class TextAreaWithTextModules(TextArea):
    """An extension of a regular textarea with a button that lets
       you select and insert text modules. If no text modules have
       been defined this will be no different from textarea.
    """
    template = PageTemplate("""
        <div class="textarea-widget">
            <div class="text-module-picker">
                <span class="text-module-picker-label"
                      title="Ctrl+i"
                      role="button"
                      aria-expanded="false"
                      aria-controls="text-module-options_${id}">
                    ${label}
                </span>
                <ul id="text-module-options_${id}"
                    class="text-module-options"
                    aria-hidden="true"
                    tabindex="-1">
                    <li tal:repeat="text_module text_modules"
                        class="text-module-option"
                        tabindex="0"
                        role="button"
                        data-value="${text_module.text}">
                        ${text_module.name}
                    </li>
                </ul>
            </div>
            <textarea tal:replace="structure input_html"/>
        </div>
    """)

    def text_modules(self, field):
        if not hasattr(field.meta, 'request'):
            # we depend on the field containing a reference to
            # the current request, which should be passed from
            # the form via the meta class
            return {}

        request = field.meta.request
        collection = TextModuleCollection(request.session)
        return collection.query().all()

    def __call__(self, field, **kwargs):
        input_html = super().__call__(field, **kwargs)
        text_modules = self.text_modules(field)
        if not text_modules:
            return input_html

        field.meta.request.include('text-module-picker')
        return Markup(self.template.render(
            id=field.id,
            label=field.gettext(_('Text modules')),
            text_modules=text_modules,
            input_html=input_html
        ))


class TagsWidget(TextInput):
    # for use with https://github.com/developit/tags-input
    input_type = 'tags'


class IconWidget(TextInput):

    iconfont = 'FontAwesome'
    icons = {
        'FontAwesome': (
            ('&#xf111', 'fa fa-circle'),
            ('&#xf005', 'fa fa-star'),
            ('&#xf06a', 'fa fa-exclamation-circle'),
            ('&#xf059', 'fa fa-question-circle'),
            ('&#xf05e', 'fa fa-ban'),
            ('&#xf1b9', 'fa fa-car'),
            ('&#xf238', 'fa fa-train'),
            ('&#xf206', 'fa fa-bicycle'),
            ('&#xf291', 'fa fa-shopping-basket'),
            ('&#xf1b0', 'fa fa-paw'),
            ('&#xf1ae', 'fa fa-child'),
            ('&#xf06d', 'fa fa-fire'),
            ('&#xf1f8', 'fa fa-trash'),
            ('&#xf236', 'fa fa-hotel'),
            ('&#xf0f4', 'fa fa-coffee'),
            ('&#xf017', 'fa fa-clock'),
        ),
        'Font Awesome 5 Free': (
            ('&#xf111', 'fas fa-circle'),
            ('&#xf005', 'fas fa-star'),
            ('&#xf06a', 'fas fa-exclamation-circle'),
            ('&#xf059', 'fas fa-question-circle'),
            ('&#xf05e', 'fas fa-ban'),
            ('&#xf1b9', 'fas fa-car'),
            ('&#xf238', 'fas fa-train'),
            ('&#xf206', 'fas fa-bicycle'),
            ('&#xf291', 'fas fa-shopping-basket'),
            ('&#xf1b0', 'fas fa-paw'),
            ('&#xf1ae', 'fas fa-child'),
            ('&#xf06d', 'fas fa-fire'),
            ('&#xf1f8', 'fas fa-trash'),
            ('&#xf594', 'fas fa-hotel'),
            ('&#xf0f4', 'fas fa-coffee'),
            ('&#xf017', 'fas fa-clock')
        )
    }

    @property
    def template(self):
        return PageTemplate("""
        <div class="icon-widget" tal:attributes="depends_on">
            <ul style="font-family: ${iconfont}">
                <li
                    tal:repeat="icon icons"
                    tal:content="structure icon[0]"
                    style="font-weight: ${font_weight(icon)}"
                />
            </ul>
            <input type="hidden" name="${id}" value="${structure: value}">
        </div>
    """)

    def __call__(self, field, **kwargs):
        iconfont = kwargs.pop('iconfont', self.iconfont)
        icons = kwargs.pop('icons', self.icons[iconfont])

        if ' ' in iconfont:
            iconfont = f"'{iconfont}'"

        def font_weight(icon):
            if icon[1].startswith('fas'):
                return '900'
            return 'regular'

        depends_on = field.render_kw.get(
            'data-depends-on', False) if field.render_kw else False
        depends_on = {'data-depends-on': depends_on} if depends_on else {}

        return Markup(self.template.render(
            iconfont=iconfont,
            icons=icons,
            id=field.id,
            depends_on=depends_on,
            value=field.data or icons[0][0],
            font_weight=font_weight
        ))


class ChosenSelectWidget(Select):

    def __call__(self, field, **kwargs):
        kwargs['class_'] = '{} chosen-select'.format(
            kwargs.get('class_', '')
        ).strip()
        kwargs['data-placeholder'] = field.gettext(_("Select an Option"))
        kwargs['data-no_results_text'] = field.gettext(_("No results match"))
        if self.multiple:
            kwargs['data-placeholder'] = field.gettext(
                _("Select Some Options")
            )

        return super(ChosenSelectWidget, self).__call__(field, **kwargs)


class PreviewWidget:
    """ A widget that displays the html of a specific view whenver there's
    a change in other fields. JavaScript is used to facilitate this.

    """

    template = PageTemplate("""
        <div class="form-preview-widget"
             data-url="${url or ''}"
             data-fields="${','.join(fields)}"
             data-events="${','.join(events)}"
             data-display="${display}">
        </div>
    """)

    def __call__(self, field, **kwargs):
        field.meta.request.include('preview-widget-handler')

        return Markup(self.template.render(
            url=callable(field.url) and field.url(field.meta) or field.url,
            fields=field.fields,
            events=field.events,
            display=field.display,
        ))


class PanelWidget:
    """ A widget that displays the field's text as panel (no input). """

    template = PageTemplate(
        """<div class="panel ${kind}">${text}</div>"""
    )

    def __call__(self, field, **kwargs):
        text = self.template.render(
            kind=field.kind,
            text=field.meta.request.translate(field.text),
        )
        text = text.replace('">', '" ' + html_params(**kwargs) + '>')
        text = text.replace('\n', '<br>')
        return Markup(text)


class HoneyPotWidget(TextInput):
    """ A widget that displays the input normally not visible to the user. """

    def __call__(self, field, **kwargs):
        field.meta.request.include('lazy-wolves')
        kwargs['class_'] = (kwargs.get('class_', '') + ' lazy-wolves').strip()
        return super().__call__(field, **kwargs)
