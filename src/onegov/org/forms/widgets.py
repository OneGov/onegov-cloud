from __future__ import annotations

from markupsafe import Markup
from onegov.form.widgets import UploadWidget, UploadMultipleWidget
from onegov.org import _
from wtforms import Form, SelectField, SelectMultipleField


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from .fields import UploadOrSelectExistingFileField
    from .fields import UploadOrSelectExistingMultipleFilesField


class UploadOrLinkExistingFileWidget(UploadWidget):

    file_details_template = Markup("""
        <div ic-trigger-from="#button-{file_id}"
             ic-trigger-on="click once"
             ic-get-from="{details_url}"
             class="file-preview-wrapper"></div>
    """)
    file_details_icon_template = Markup("""
        <a id="button-{file_id}" class="file-edit">
            <i class="fa fa-edit" aria-hidden="true"></i>
        </a>
    """)

    def template_data(
        self,
        field: UploadOrSelectExistingFileField,  # type:ignore[override]
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
        data['existing_file_label'] = field.gettext(_('Linked file'))
        data['keep_label'] = field.gettext(_('Keep link'))
        data['delete_label'] = field.gettext(_('Delete link'))
        data['replace_label'] = field.gettext(_('Replace link'))
        if is_simple is True:
            return is_simple, data

        # existing_file takes precedent over object_data, but most
        # of the time it will just be object_data
        file = getattr(field, 'existing_file', field.object_data)
        if file is not None:
            # interactive preview widget
            request = field.meta.request
            request.include('prompt')
            # FIXME: Make file-details work without ic-on-success
            request.require_unsafe_eval()
            data['preview'] = self.file_details_template.format(
                file_id=file.id,
                details_url=request.link(file, 'details')
            )
            data['icon'] = self.file_details_icon_template.format(
                file_id=file.id
            )
        return is_simple, data


class UploadOrSelectExistingFileWidget(UploadOrLinkExistingFileWidget):

    simple_template = Markup("""
        <div class="upload-widget without-data{wrapper_css_class}">
            {input_html}
            {select_html}
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
        field: UploadOrSelectExistingFileField,  # type:ignore[override]
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
                choices=field.choices,
                render_kw={
                    'id': f'{field.name}-select',
                    'data_placeholder': field.gettext(
                        _('Choose existing file')
                    ),
                    'class_': 'chosen-select'
                }
            )

        form = DummyForm(existing=getattr(field, 'existing', None))
        data['select_html'] = form.existing(**kwargs)
        return is_simple, data


class UploadOrSelectExistingMultipleFilesWidget(UploadMultipleWidget):

    additional_label = _('Link additional files')

    def render_input(
        self,
        field: UploadOrSelectExistingMultipleFilesField,  # type:ignore
        **kwargs: Any
    ) -> Markup:

        upload_html = super().render_input(field, **kwargs)

        class DummyForm(Form):
            selected = SelectMultipleField(
                name=field.name,  # we need to use our name
                choices=field.choices,
                render_kw={
                    'id': f'{field.name}-select',
                    'data_placeholder': field.gettext(
                        _('Choose existing file')
                    ),
                    'class_': 'chosen-select'
                }
            )

        selected = [
            value
            for value in (field.raw_data or ())
            if isinstance(value, str)
        ]
        form = DummyForm(selected=selected)
        # FIXME: Don't hardcode the multi-select size
        select_html = form.selected(size=5, **kwargs)
        return Markup('{}</label><br/><label>{}: {}').format(
            select_html,
            field.gettext(super().additional_label),
            upload_html
        )
