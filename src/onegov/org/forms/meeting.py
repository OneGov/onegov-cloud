from __future__ import annotations

import json

from wtforms.validators import Optional, InputRequired
from wtforms import StringField, SelectMultipleField

from onegov.form import Form
from onegov.form.fields import TimezoneDateTimeField, MultiCheckboxField
from onegov.org.forms.fields import HtmlField
from onegov.org import _

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Collection
    from collections.abc import Sequence

    from onegov.org.models import Meeting
    from onegov.org.models import MeetingItem
    from onegov.org.models import PoliticalBusiness


class MeetingForm(Form):
    title = StringField(
        label=_('Title'),
        validators=[InputRequired()],
    )

    start_datetime = TimezoneDateTimeField(
        timezone='Europe/Zurich',
        label=_('Start'),
        validators=[Optional()],
    )

    end_datetime = TimezoneDateTimeField(
        timezone='Europe/Zurich',
        label=_('End'),
        validators=[Optional()],
    )

    address = HtmlField(
        label=_('Address'),
        validators=[InputRequired()],
        render_kw={'rows': 3}
    )

    description = HtmlField(
        label=_('Description'),
        validators=[Optional()],
        render_kw={'rows': 5}
    )

    meeting_items = StringField(
        label=_('New agenda item'),
        fieldset=_('Agenda items'),
        render_kw={'class_': 'many many-meeting-items'},
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.agenda_items_errors: dict[int, str] = {}

    def on_request(self) -> None:
        # prevent showing access field as all ris information is public
        if hasattr(self, 'access'):
            self.delete_field('access')

    def populate_obj(  # type:ignore[override]
        self,
        obj: Meeting,  # type:ignore[override]
        exclude: Collection[str] | None = None,
        include: Collection[str] | None = None
    ) -> None:
        from onegov.org.models import MeetingItem
        from onegov.org.models import MeetingItemCollection
        from onegov.org.models import PoliticalBusinessCollection

        super().populate_obj(
            obj,
            exclude={
                'meeting_items',
                *(exclude or ())
            },
            include=include
        )

        meeting: Meeting = obj
        collection = MeetingItemCollection(self.request.session)
        businesses = PoliticalBusinessCollection(self.request.session)

        # Somehow `meeting_items.data` is not set when the form is submitted,
        # so we use `meeting_items.raw_data[0]` instead.
        data = (self.meeting_items.raw_data[0]
                if self.meeting_items.raw_data else '')
        new_items = self.json_to_items(data)
        if not new_items:
            # clear all meeting items for this meeting
            for item in meeting.meeting_items:
                collection.delete(item)
            obj.meeting_items = []
            return

        current_items = {item.title: item for item in meeting.meeting_items}
        items = []
        for new in new_items:
            number = new.get('number')
            title = new.get('title', '')
            item_name = new.get('agenda_item', '')

            if number == '' and title == '' and item_name == '':
                # skip empty items
                continue

            if (number in [i.number for i in current_items.values()] and
                title in current_items and
                item_name in [i.display_name for i in current_items.values()]):
                # keep unchanged items
                items.append(current_items[title])
                continue

            business = businesses.by_display_name(item_name)
            if business is None:
                new_item = MeetingItem(
                    title=title,
                    number=number,
                    political_business_id=None,
                    political_business=None,
                    meeting_id=obj.id,
                    meeting=obj,
                )
            else:
                new_item = MeetingItem(
                    title=title if title != '' else business.title,
                    number=number,
                    political_business_id=business.id,
                    political_business=business,
                    meeting_id=obj.id,
                    meeting=obj,
                )
            self.request.session.add(new_item)
            items.append(new_item)

        meeting.meeting_items = items

        # update links from businesses to meeting
        for item in meeting.meeting_items:
            if item.political_business:
                item.political_business.meeting_items.append(item)

    def process_obj(self, obj: Meeting) -> None:  # type:ignore[override]
        from onegov.org.models import PoliticalBusiness

        super().process_obj(obj)

        meeting: Meeting = obj

        businesses = (
            self.meta.request.session.query(PoliticalBusiness)
            .with_entities(
                PoliticalBusiness.number,
                PoliticalBusiness.title,
                PoliticalBusiness.display_name
            )
            .order_by(PoliticalBusiness.number, PoliticalBusiness.title)
            .all()
        )

        if not meeting.meeting_items:
            self.meeting_items.data = self.items_to_json([], businesses)
        else:
            self.meeting_items.data = self.items_to_json(
                meeting.meeting_items, meeting.meeting_items + businesses
            )

    def json_to_items(self, text: str | None) -> list[dict[str, str]]:
        if not text:
            return []

        return list(json.loads(text).get('values', []))

    def items_to_json(
        self,
        values: Sequence[MeetingItem],
        options: Sequence[PoliticalBusiness],
    ) -> str:
        values = values or []
        options = options or []

        request = self.meta.request
        return json.dumps(
            {
                # labels for many-meeting-items
                'labels': {
                    'number': request.translate(_('Number')),
                    'title': request.translate(_('Title')),
                    'agenda_item': request.translate(_('Agenda item')),
                    'add': request.translate(_('Add')),
                    'remove': request.translate(_('Remove')),
                },
                # StringField: list of agenda items attached to this meeting
                'values': [
                    {
                        'number': agenda_item.number,
                        'title': agenda_item.title,
                        'agenda_item': (
                            agenda_item.political_business.display_name
                            if agenda_item.political_business else
                            agenda_item.display_name),
                        'error': '',
                        # 'error': self.agenda_items_errors.get(ix, ''),
                    }
                    for ix, agenda_item in enumerate(sorted(
                        values, key=lambda x: (x.number or '', x.title)))
                ],
                # SelectField: list of agenda items and businesses
                'agenda_items': {
                    option.display_name: option.display_name
                    for option in options
                },
            }
        )


class MeetingExportPoliticalBusinessForm(Form):

    meeting_documents = MultiCheckboxField(
        label=_('Meeting documents'),
        choices=[],
    )

    business_documents = MultiCheckboxField(
        label=_('Political business documents'),
        choices=[],
    )

    def process_obj(self, obj: Meeting) -> None:
        super().process_obj(obj)

        self.meeting_documents.choices = [
            (str(doc.id), doc.name)
            for doc in obj.files
        ]
        self.meeting_documents.data = [doc.id for doc in obj.files]
        self.meeting_documents.description = obj.display_name

        document_structure = {}
        for index, meeting_item in enumerate(obj.meeting_items, start=1):
            business = meeting_item.political_business
            if not business:
                continue

            document_structure[index] = {
                'name': business.title,
                'documents': [
                    {'id': doc.id, 'name': doc.name}
                    for doc in business.files
                ]
            }

        choices = []
        for value in document_structure.values():
            business_name = value['name']
            for doc in value['documents']:
                choices.append((str(doc['id']), f"{business_name} - {doc['name']}"))
        self.business_documents.choices = choices
        self.business_documents.data = [doc_id for doc_id, _ in choices]

    def get_selected_meeting_documents_ids(self) -> list[str]:
        return self.meeting_documents.data

    def get_selected_business_document_ids(self) -> list[str]:
        return self.business_documents.data



