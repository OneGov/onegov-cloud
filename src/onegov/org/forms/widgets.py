from markupsafe import Markup
from onegov.form.widgets import UploadWidget, UploadMultipleWidget
from wtforms import Form, SelectField, SelectMultipleField


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from .fields import UploadOrSelectExistingFileField
    from .fields import UploadOrSelectExistingMultipleFilesField


class UploadOrSelectExistingFileWidget(UploadWidget):

    simple_template = Markup("""
        <div class="upload-widget without-data{wrapper_css_class}">
            {input_html}
            {select_html}
        </div>
    """)
    template = Markup("""
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
                <li>
                    <input type="radio" id="{name}-3" name="{name}"
                           value="select">
                    <label for="{name}-3">{replace_label}</label>
                    <div>
                        <label>
                            <div data-depends-on="{name}/select"
                                 data-hide-label="false">
                                {select_html}
                            </div>
                        </label>
                    </div>
                </li>
            </ul>

            {previous}
        </div>
    """)

    def template_data(
        self,
        field: 'UploadOrSelectExistingFileField',  # type:ignore[override]
        force_simple: bool,
        resend_upload: bool,
        wrapper_css_class: str,
        input_html: Markup,
        **kwargs: Any
    ) -> tuple[bool, dict[str, Any]]:

        is_simple, data = super().template_data(
            field,
            force_simple=force_simple,
            resend_upload=resend_upload,
            wrapper_css_class=wrapper_css_class,
            input_html=input_html,
            **kwargs
        )

        # this is pretty ugly, but implementing iter_choices on the file
        # field would not clean up things significantly
        class DummyForm(Form):
            existing = SelectField(
                name=field.name,  # we need to use our name
                choices=field.choices
            )

        form = DummyForm(existing=getattr(field, 'existing', None))
        data['select_html'] = form.existing(**kwargs)
        return is_simple, data


class UploadOrSelectExistingMultipleFilesWidget(UploadMultipleWidget):

    def render_input(
        self,
        field: 'UploadOrSelectExistingMultipleFilesField',  # type:ignore
        **kwargs: Any
    ) -> Markup:

        upload_html = super().render_input(field, **kwargs)

        class DummyForm(Form):
            selected = SelectMultipleField(
                name=field.name,  # we need to use our name
                choices=field.choices
            )

        selected = [
            value
            for value in (field.raw_data or ())
            if isinstance(value, str)
        ]
        form = DummyForm(selected=selected)
        # FIXME: Don't hardcode the multi-select size
        select_html = form.selected(size=5, **kwargs)
        return Markup('{}<br/>{}').format(upload_html, select_html)
