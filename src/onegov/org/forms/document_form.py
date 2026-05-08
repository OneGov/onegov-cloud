from __future__ import annotations

from onegov.core.utils import normalize_for_url
from onegov.form import Form
from onegov.form.core import DataRequired
from onegov.form.fields import HtmlField, UploadFileWithORMSupport
from onegov.org.models.document_form import DocumentFormFile
from onegov.form.validators import FileSizeLimit
from onegov.org import _
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired

from typing import Any, TYPE_CHECKING

from onegov.swissvotes.forms.attachments import PDF_MIME_TYPES

if TYPE_CHECKING:
    from collections.abc import Collection


class DocumentForm(Form):

    title = StringField(
        label=_('Title'),
        validators=[InputRequired()])

    lead = TextAreaField(
        label=_('Lead'),
        description=_('Describes briefly what this form is about'),
        validators=[],
        render_kw={'rows': 4})

    text = HtmlField(
        label=_('Detailed Explanation'),
        description=_('Describes in detail how this form is to be filled'))

    pdf = UploadFileWithORMSupport(
        label=_('Form PDF'),
        file_class=DocumentFormFile,
        validators=[
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired()
        ],
        allowed_mimetypes=PDF_MIME_TYPES,
    )

    group = StringField(
        label=_('Group'),
        description=_('Used to group this form in the overview'))

    def get_useful_data(
            self,
        exclude: Collection[str] | None = None
    ) -> dict[str, Any]:

        data = super().get_useful_data(exclude)
        data['pdf'] = self.pdf.create()
        data['name'] = normalize_for_url(self.title.data)  # type: ignore

        return data
