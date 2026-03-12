from __future__ import annotations

import humanize

from contextlib import suppress
from datetime import date
from dateutil.relativedelta import relativedelta
from markupsafe import escape, Markup
from morepath.error import LinkError
from onegov.chat import TextModuleCollection
from onegov.core.templates import PageTemplate
from onegov.file.utils import IMAGE_MIME_TYPES_AND_SVG
from onegov.form import _
from wtforms.widgets import DateInput
from wtforms.widgets import DateTimeLocalInput
from wtforms.widgets import FileInput
from wtforms.widgets import ListWidget
from wtforms.widgets import NumberInput
from wtforms.widgets import Select
from wtforms.widgets import TextArea
from wtforms.widgets import TextInput
from wtforms.widgets.core import html_params


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.chat import TextModule
    from onegov.form.fields import (
        DurationField, PanelField, PreviewField, UploadField,
        UploadMultipleField, TypeAheadField
    )
    from wtforms import Field, StringField
    from wtforms.fields.choices import SelectFieldBase


class OrderedListWidget(ListWidget):
    """ Extends the default list widget with automated ordering using the
    translated text of each element.

    """

    def __call__(self, field: Field, **kwargs: Any) -> Markup:

        # ListWidget expects a field internally, but it will only use
        # its id property and __iter__ method, so we can get away
        # with passing a fake field with an id and an iterator.
        #
        # It's not great, since we have to assume internal knowledge,
        # but builting a new field or changing the existing one would
        # require even more knowledge, so this is the better approach

        assert hasattr(field, '__iter__')
        ordered: list[Field] = list(field)
        ordered.sort(key=lambda f: field.gettext(f.label.text))

        class FakeField:

            id = field.id

            def __iter__(self) -> Iterator[Field]:
                return iter(ordered)

        return super().__call__(FakeField(), **kwargs)  # type:ignore[arg-type]


class MultiCheckboxWidget(ListWidget):
    """ The default list widget with the label behind the checkbox. """

    def __init__(self, html_tag: Literal['ul', 'ol'] = 'ul'):
        super().__init__(html_tag=html_tag, prefix_label=False)

    def __call__(self, field: Field, **kwargs: Any) -> Markup:
        if hasattr(field.meta, 'request'):
            field.meta.request.include('multicheckbox')
        return super().__call__(field, **kwargs)


class OrderedMultiCheckboxWidget(MultiCheckboxWidget, OrderedListWidget):
    """ The sorted list widget with the label behind the checkbox. """

    def __call__(self, field: Field, **kwargs: Any) -> Markup:
        if hasattr(field.meta, 'request'):
            field.meta.request.include('multicheckbox')
        return super().__call__(field, **kwargs)


class CoordinateWidget(TextInput):
    """ Widget containing the coordinates for the
    :class:`onegov.form.fields.CoordinateField` class.

    Basically a text input with a class. Meant to be enhanced on the browser
    using javascript.

    """

    def __call__(self, field: Field, **kwargs: Any) -> Markup:
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

    simple_template = Markup("""
        <div class="upload-widget without-data{wrapper_css_class}">
            {input_html}
        </div>
    """)
    template = Markup("""
        <div class="upload-widget with-data{wrapper_css_class}">
                <p class="file-title">
                    <b>
                        {existing_file_label}: {filename}{filesize} {icon}
                    </b>
                </p>

            {preview}

            <ul class="upload-options">
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
    """)

    def image_source(self, field: UploadField) -> str | None:
        """ Returns the image source url if the field points to an image and
        if it can be done (it looks like it's possible, but I'm not super
        sure this is always possible).

        """

        if not hasattr(field.meta, 'request'):
            return None

        if not field.data:
            return None

        if field.data.get('mimetype', None) not in IMAGE_MIME_TYPES_AND_SVG:
            return None

        if not hasattr(field, 'object_data'):
            return None

        if not field.object_data:
            return None

        with suppress(LinkError, AttributeError):
            return field.meta.request.link(field.object_data)
        return None

    def template_data(
        self,
        field: UploadField,
        force_simple: bool,
        resend_upload: bool,
        wrapper_css_class: str,
        input_html: Markup,
        **kwargs: Any
    ) -> tuple[bool, dict[str, Any]]:

        if force_simple or field.errors or not field.data:
            return True, {
                'wrapper_css_class': wrapper_css_class,
                'input_html': input_html,
            }

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

        size = field.data['size']
        if size < 0:
            display_size = ''
        else:
            display_size = f' ({humanize.naturalsize(size)})'

        return False, {
            'wrapper_css_class': wrapper_css_class,
            'input_html': input_html,
            'icon': '✓',
            'preview': preview,
            'previous': previous,
            'filesize': display_size,
            'filename': field.data['filename'],
            'name': field.id,
            'existing_file_label': field.gettext(_('Uploaded file')),
            'keep_label': field.gettext(_('Keep file')),
            'delete_label': field.gettext(_('Delete file')),
            'replace_label': field.gettext(_('Replace file')),
        }

    def __call__(
        self,
        field: UploadField,  # type:ignore[override]
        **kwargs: Any
    ) -> Markup:

        force_simple = kwargs.pop('force_simple', False)
        resend_upload = kwargs.pop('resend_upload', False)
        wrapper_css_class = kwargs.pop('wrapper_css_class', '')
        if wrapper_css_class:
            wrapper_css_class = ' ' + wrapper_css_class
        input_html = super().__call__(field, **kwargs)

        is_simple, data = self.template_data(
            field,
            force_simple=force_simple,
            resend_upload=resend_upload,
            wrapper_css_class=wrapper_css_class,
            input_html=input_html,
            **kwargs
        )
        if is_simple:
            return self.simple_template.format(**data)
        return self.template.format(**data)


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

    additional_label = _('Upload additional files')

    def __init__(self) -> None:
        self.multiple = True

    def render_input(
        self,
        field: UploadMultipleField,
        **kwargs: Any
    ) -> Markup:
        return super().__call__(field, **kwargs)

    def __call__(
        self,
        field: UploadMultipleField,  # type:ignore[override]
        **kwargs: Any
    ) -> Markup:

        force_simple = kwargs.pop('force_simple', False)
        resend_upload = kwargs.pop('resend_upload', False)
        input_html = self.render_input(field, **kwargs)
        simple_template = Markup("""
            <div class="upload-widget without-data">
                {}
            </div>
        """)

        if force_simple or len(field) == 0:
            return simple_template.format(input_html) + Markup('\n').join(
                Markup('<small class="error">{}</small>').format(error)
                for error in field.errors
            )
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
            additional_html = Markup(
                '<label>{label}: {input_html}</label>'
            ).format(
                label=field.gettext(self.additional_label),
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
            <textarea tal:replace="input_html"/>
        </div>
    """)

    def text_modules(self, field: StringField) -> list[TextModule]:
        if not hasattr(field.meta, 'request'):
            # we depend on the field containing a reference to
            # the current request, which should be passed from
            # the form via the meta class
            return []

        request = field.meta.request
        collection = TextModuleCollection(request.session)
        return collection.query().all()

    def __call__(self, field: StringField, **kwargs: Any) -> Markup:
        input_html = super().__call__(field, **kwargs)
        text_modules = self.text_modules(field)
        if not text_modules:
            return input_html

        field.meta.request.include('text-module-picker')
        return Markup(self.template.render(  # nosec: B704
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

    template = PageTemplate("""
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

    def __call__(self, field: Field, **kwargs: Any) -> Markup:
        iconfont = kwargs.pop('iconfont', self.iconfont)
        icons = kwargs.pop('icons', self.icons[iconfont])

        if ' ' in iconfont:
            iconfont = f"'{iconfont}'"

        def font_weight(icon: str) -> str:
            if icon[1].startswith('fas'):
                return '900'
            return 'regular'

        depends_on = field.render_kw.get(
            'data-depends-on', False) if field.render_kw else False
        depends_on = {'data-depends-on': depends_on} if depends_on else {}

        return Markup(self.template.render(  # nosec: B704
            iconfont=iconfont,
            icons=icons,
            id=field.id,
            depends_on=depends_on,
            value=field.data or icons[0][0],
            font_weight=font_weight
        ))


class ChosenSelectWidget(Select):

    def __call__(self, field: SelectFieldBase, **kwargs: Any) -> Markup:
        kwargs['class_'] = '{} chosen-select'.format(
            kwargs.get('class_', '')
        ).strip()
        kwargs['data-placeholder'] = field.gettext(_('Select an Option'))
        kwargs['data-no_results_text'] = field.gettext(_('No results match'))
        if self.multiple:
            kwargs['data-placeholder'] = field.gettext(
                _('Select Some Options')
            )

        return super().__call__(field, **kwargs)


class TreeSelectWidget(Select):

    def __call__(self, field: SelectFieldBase, **kwargs: Any) -> Markup:
        field.meta.request.include('treeselect')

        kwargs['class_'] = '{} treeselect'.format(
            kwargs.get('class_', '')
        ).strip()
        kwargs['data-placeholder'] = field.gettext(_('Select an Option'))
        kwargs['data-no_results_text'] = field.gettext(_('No results match'))
        if self.multiple:
            kwargs['data-placeholder'] = field.gettext(
                _('Select Some Options')
            )

        return super().__call__(field, **kwargs)


class PreviewWidget:
    """ A widget that displays the html of a specific view whenever there's
    a change in other fields. JavaScript is used to facilitate this.

    """

    template = Markup("""
        <div class="form-preview-widget"
             data-url="{url}"
             data-fields="{fields}"
             data-events="{events}"
             data-display="{display}">
        </div>
    """)

    def __call__(self, field: PreviewField, **kwargs: Any) -> Markup:
        field.meta.request.include('preview-widget-handler')

        if callable(field.url):
            url = field.url(field.meta)
        else:
            url = field.url

        return self.template.format(
            url=url or '',
            fields=','.join(field.fields),
            events=','.join(field.events),
            display=','.join(field.display)
        )


class PanelWidget:
    """ A widget that displays the field's text as panel (no input). """

    def __call__(self, field: PanelField, **kwargs: Any) -> Markup:
        text = escape(field.meta.request.translate(field.text))
        return Markup(  # nosec: B704
            f'<div class="panel {{kind}}" {html_params(**kwargs)}>'
            '{text}</div>'
        ).format(
            kind=field.kind,
            text=text.replace('\n', Markup('<br>'))
        )


class LinkPanelWidget(PanelWidget):
    """ A widget that displays a clickable link as panel (no input). """

    def __call__(self, field: PanelField, **kwargs: Any) -> Markup:
        text = escape(field.meta.request.translate(field.text))
        return Markup(  # nosec: B704
            f'<div class="panel {{kind}}" {html_params(**kwargs)}>'
            '<a href="{link}">{text}</a></div>'
        ).format(
            kind=field.kind,
            text=text.replace('\n', Markup('<br>')),
            link=field.text
        )


class HoneyPotWidget(TextInput):
    """ A widget that displays the input normally not visible to the user. """

    def __call__(self, field: Field, **kwargs: Any) -> Markup:
        field.meta.request.include('lazy-wolves')
        kwargs['class_'] = (kwargs.get('class_', '') + ' lazy-wolves').strip()
        return super().__call__(field, **kwargs)


class DateRangeMixin:

    def __init__(
        self,
        min: date | relativedelta | None = None,
        max: date | relativedelta | None = None
    ):
        self.min = min
        self.max = max

    @property
    def min_date(self) -> date | None:
        if isinstance(self.min, relativedelta):
            return date.today() + self.min
        return self.min

    @property
    def max_date(self) -> date | None:
        if isinstance(self.max, relativedelta):
            return date.today() + self.max
        return self.max


class DateRangeInput(DateRangeMixin, DateInput):
    """ A date widget which set the min and max values that are
    supported in some browsers based on a date or relativedelta.
    """

    def __call__(self, field: Field, **kwargs: Any) -> Markup:
        min_date = self.min_date
        if min_date is not None:
            kwargs.setdefault('min', min_date.isoformat())

        max_date = self.max_date
        if max_date is not None:
            kwargs.setdefault('max', max_date.isoformat())

        return super().__call__(field, **kwargs)


class DateTimeLocalRangeInput(DateRangeMixin, DateTimeLocalInput):
    """ A datetime-local widget which set the min and max values that
    are supported in some browsers based on a date or relativedelta.
    """

    def __call__(self, field: Field, **kwargs: Any) -> Markup:
        min_date = self.min_date
        if min_date is not None:
            kwargs.setdefault('min', min_date.isoformat() + 'T00:00')

        max_date = self.max_date
        if max_date is not None:
            kwargs.setdefault('max', max_date.isoformat() + 'T23:59')

        return super().__call__(field, **kwargs)


class DurationInput:

    minutes_widget = NumberInput(step=5, min=0, max=60)
    hours_widget = NumberInput(step=1, min=0, max=24)

    def __call__(self, field: DurationField, **kwargs: Any) -> Markup:
        if field.data is None:
            hours = '0'
            minutes = '0'
        else:
            _minutes, _seconds = divmod(int(field.data.total_seconds()), 60)
            _hours, _minutes = divmod(_minutes, 60)
            hours = str(_hours)
            minutes = str(_minutes)
        return Markup("""
            <div class="duration-widget">
            <label>{hours_input} {hours_label}</label>
            <label>{minutes_input} {minutes_label}</label>
            </div>
        """).format(
            hours_label=field.gettext(_('hours')),
            minutes_label=field.gettext(_('minutes')),
            hours_input=self.hours_widget(
                field, value=hours, size=2, **kwargs
            ),
            minutes_input=self.minutes_widget(
                field, value=minutes, size=2, **kwargs
            ),
        )


class TypeAheadInput(TextInput):
    """ A widget with typeahead. """

    def __call__(
        self,
        field: TypeAheadField,  # type:ignore[override]
        **kwargs: Any
    ) -> Markup:
        field.meta.request.include('typeahead-standalone')

        kwargs['class_'] = (
            kwargs.get('class_', '') + ' typeahead-standalone-field'
        ).strip()
        kwargs['data-url'] = (
            field.url(field.meta) if callable(field.url) else field.url
        )

        return super().__call__(field, **kwargs)
