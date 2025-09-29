from __future__ import annotations

import re
import zipfile
import os
import base64
import gzip
import pytz

from bs4 import BeautifulSoup
from datetime import datetime
from markupsafe import Markup
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from onegov.form import Form
from onegov.form.fields import TagsField
from onegov.form.fields import TimeField
from onegov.form.fields import UploadField
from onegov.form.forms import NamedFileForm
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.landsgemeinde import _
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import AgendaItem, LandsgemeindeFile
from onegov.landsgemeinde.models.agenda import STATES
from onegov.landsgemeinde.utils import timestamp_to_seconds
from onegov.org.forms.fields import HtmlField
from onegov.org.forms.fields import UploadMultipleFilesWithORMSupport
from sqlalchemy import func
from wtforms.fields import BooleanField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional
from wtforms.validators import ValidationError

from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.landsgemeinde.request import LandsgemeindeRequest
    from onegov.landsgemeinde.collections import AgendaItemCollection


class AgendaItemForm(NamedFileForm):

    request: LandsgemeindeRequest

    number = IntegerField(
        label=_('Number'),
        fieldset=_('General'),
    )

    state = RadioField(
        _('State'),
        fieldset=_('General'),
        choices=list(STATES.items()),
        validators=[
            InputRequired()
        ],
        default=next(iter(STATES.keys()))
    )

    title = TextAreaField(
        label=_('Title'),
        fieldset=_('General'),
        render_kw={'rows': 5}
    )

    irrelevant = BooleanField(
        label=_('Irrelevant'),
        fieldset=_('General'),
    )

    memorial_pdf = UploadField(
        label=_('Excerpt from the Memorial (PDF)'),
        fieldset=_('Memorial'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ]
    )

    memorial_page = IntegerField(
        description=_(
            'Links to the whole memorial (if there is one linked to the '
            'assembly), but opens it on the chosen page number'
        ),
        label=_('Alternatively: Page from the Memorial'),
        fieldset=_('Memorial'),
        validators=[
            NumberRange(min=1),
            Optional()
        ],
    )

    more_files = UploadMultipleFilesWithORMSupport(
        label=_('Additional documents'),
        fieldset=_('Documents'),
        file_class=LandsgemeindeFile,
    )

    start_time = TimeField(
        label=_('Start'),
        fieldset=_('Progress'),
        render_kw={
            'long_description': _(
                'Automatically updated when agenda item changed to ongoing.'
            ),
            'step': 1
        },
        format='%H:%M:%S',
        validators=[
            Optional()
        ],
    )

    calculated_timestamp = StringField(
        label=_('Calculated video timestamp'),
        fieldset=_('Progress'),
        render_kw={
            'long_description': _(
                'Calculated automatically based on the start time of the '
                'agenda item and the start time of of the livestream of the '
                'assembly .'
            ),
            'readonly': True,
            'step': 1
        },
        validators=[
            Optional()
        ],
    )

    video_timestamp = StringField(
        label=_('Manual video timestamp'),
        fieldset=_('Progress'),
        description='1h2m1s',
        render_kw={
            'long_description': _('Overrides the calculated video timestamp.'),
            'step': 1
        },
        validators=[
            Optional()
        ],
    )

    overview = HtmlField(
        label=_('Text'),
        fieldset=_('Overview'),
    )

    text = HtmlField(
        label=_('Text'),
        fieldset=_('Content'),
    )

    resolution = HtmlField(
        label=_('Text'),
        fieldset=_('Resolution'),
    )

    tacitly_accepted = BooleanField(
        label=_('Tacitly accepted'),
        fieldset=_('Resolution'),
    )

    resolution_tags = TagsField(
        label=_('Tags'),
        fieldset=_('Resolution')
    )

    @property
    def next_number(self) -> int:
        query = self.request.session.query(func.max(AgendaItem.number))
        query = query.filter(AgendaItem.assembly_id == self.model.assembly.id)
        return (query.scalar() or 0) + 1

    def on_request(self) -> None:
        DefaultLayout(self.model, self.request)
        self.request.include('redactor')
        self.request.include('editor')
        self.request.include('tags-input')

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        data = super().get_useful_data(exclude={'calculated_timestamp'})
        data['assembly_id'] = self.model.assembly.id
        return data

    def validate_number(self, field: IntegerField) -> None:
        if field.data:
            session = self.request.session
            query = session.query(AgendaItem)
            query = query.filter(
                AgendaItem.assembly_id == self.model.assembly.id,
                AgendaItem.number == field.data
            )
            if isinstance(self.model, AgendaItem):
                query = query.filter(AgendaItem.id != self.model.id)
            if session.query(query.exists()).scalar():
                raise ValidationError(_('Number already used.'))

    def validate_video_timestamp(self, field: StringField) -> None:
        if field.data and timestamp_to_seconds(field.data) is None:
            raise ValidationError(_('Invalid timestamp.'))

    def populate_obj(self, obj: AgendaItem) -> None:  # type:ignore[override]
        super().populate_obj(obj, exclude={'calculated_timestamp'})
        if not obj.start_time and self.state.data == 'ongoing':
            tz = pytz.timezone('Europe/Zurich')
            now = datetime.now(tz=tz).time()
            obj.start_time = now


class AgendaItemUploadForm(Form):

    request: LandsgemeindeRequest

    agenda_item_zip = UploadField(
        label=_('Agenda Item ZIP'),
        fieldset=_('Import'),
        validators=[
            WhitelistedMimeType({'application/zip'}),
            FileSizeLimit(100 * 1024 * 1024)
        ]
    )

    def get_html_dir(self,
                     temp: TemporaryDirectory[str],
                     field: UploadField) -> str | None:

        temp_path = Path(temp.name)
        zip_content = None

        if isinstance(field.data, dict) and 'data' in field.data:
            encoded_data = field.data['data']
            decoded_data = base64.b64decode(encoded_data)

            if decoded_data[:2] == b'\x1f\x8b':
                decompressed_data = gzip.decompress(decoded_data)
                zip_content = BytesIO(decompressed_data)
            else:
                zip_content = BytesIO(decoded_data)

        with zipfile.ZipFile(
            zip_content, 'r') as zip_ref:  # type:ignore
            zip_ref.extractall(temp_path)

        html_dir = None
        for root, dirs, files in os.walk(temp_path):
            if 'html' in dirs:
                html_dir = os.path.join(root, 'html')
                break

        return html_dir

    def import_agenda_item(
            self, collection: AgendaItemCollection) -> AgendaItem:

        temp = TemporaryDirectory()
        html_dir = self.get_html_dir(temp, self.agenda_item_zip)
        html_path = Path(html_dir)  # type:ignore
        html_files = sorted(
            [f for f in html_path.glob('*.html')
             if f.name != 'combined_clean.html'],
            key=lambda f: [int(s) if s.isdigit() else -1
                           for s in re.findall(r'\d+|\D+', f.name)]
        )

        combined_html = BeautifulSoup(
            '<html><head><meta charset="utf-8"></head><body></body></html>',
            'html.parser')
        title = ''

        for file_path in html_files:
            with open(file_path, encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')

            all_paragraphs = []

            if soup.body is None:
                continue
            textframes = soup.body.find_all('div', recursive=False)
            for textframe in textframes[1:] if textframes else []:
                for p_tag in textframe.find_all('p'):
                    p_class = ' '.join(p_tag.get('class', []))
                    spans_text = []
                    parent = p_tag.find_parent()

                    parent_inline_style = parent.get('style', ''
                                                     ) if parent else ''
                    if not parent_inline_style:
                        p_class = 'table'

                    regex = re.compile(r'^_idTextSpan\d+')
                    for span in p_tag.find_all('span', id=regex):
                        text = span.get_text().strip()
                        if text:
                            spans_text.append(text)

                    if spans_text:
                        all_paragraphs.append({
                            'class': p_class,
                            'text': ' '.join(spans_text),
                            'is_list_item': 'Aufz-hlung' in p_class
                        })

            i = 0
            while i < len(all_paragraphs):
                para = all_paragraphs[i]
                if combined_html.body is None:
                    break

                # Check if this is the start of a list
                if para['is_list_item']:
                    ul_element = combined_html.new_tag('ul')

                    # Add this and all consecutive list items to the <ul>
                    while (i < len(all_paragraphs)
                           and all_paragraphs[i]['is_list_item']):
                        li_element = combined_html.new_tag('li')
                        li_element.string = all_paragraphs[
                            i]['text'].strip()  # type:ignore
                        ul_element.append(li_element)
                        i += 1
                    combined_html.body.append(ul_element)

                else:
                    # Regular paragraph or heading
                    p_class = str(para['class'])
                    p_text = para['text']

                    # Determine heading level based on class
                    tag_type = 'p'
                    if '_01-Titel' in p_class:
                        title = p_text.strip()  # type:ignore
                        i += 1
                        continue
                    elif '_02-Titel' in p_class:
                        tag_type = 'h2'
                    elif '03-Titel' in p_class in p_class:
                        tag_type = 'h3'
                    elif '04-' in p_class in p_class:
                        tag_type = 'h4'
                    elif 'Vorlage_Vorlage-Titel' in p_class:
                        tag_type = 'h2'
                    elif p_class == 'table':
                        if i > 0 and all_paragraphs[i-1]['class'] != 'table':
                            element = combined_html.new_tag('p')
                            element.string = '--- TABELLE HIER EINFÜGEN ---'
                            combined_html.body.append(element)
                        i += 1
                        continue

                    element = combined_html.new_tag(tag_type)
                    element.string = p_text.strip()  # type:ignore
                    combined_html.body.append(element)
                    i += 1

        cleaned_html = Markup(combined_html.prettify())  # nosec: B704

        query = self.request.session.query(func.max(AgendaItem.number))
        query = query.filter(AgendaItem.assembly_id == self.model.assembly.id)
        next_number = (query.scalar() or 0) + 1

        agenda_item = collection.add(
            text=cleaned_html,
            number=next_number,
            state='draft',
            title=title,
            assembly_id=self.model.assembly.id
        )

        temp.cleanup()
        return agenda_item

    def validate_agenda_item_zip(
            self,
            field: UploadField) -> None:
        if not field.data:
            raise ValidationError(_('No file uploaded.'))

        temp = TemporaryDirectory()
        html_dir = self.get_html_dir(temp, field)
        if not html_dir:
            raise ValidationError(
                _('No html directory found in the zip file.'))
        temp.cleanup()
