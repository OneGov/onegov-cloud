from __future__ import annotations

import json

from wtforms.validators import Optional, InputRequired
from wtforms import StringField

from onegov.form import Form
from onegov.form.fields import TimezoneDateTimeField
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
        label=_('New Agenda Item'),
        fieldset=_('Agenda Items'),
        render_kw={'class_': 'many many-meeting-items'},
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.agenda_items_errors: dict[int, str] = {}

    def on_request(self) -> None:
        pass

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

        # new_items = self.json_to_items(self.meeting_items_neu.data)
        new_items = self.json_to_items(self.meeting_items.raw_data[0])
        if not new_items:
            # clear all meeting items for this meeting
            for item in meeting.meeting_items:
                collection.delete(item)
            obj.meeting_items = []
            return

        current_items = {item.title: item for item in meeting.meeting_items}
        new = []
        for item in new_items:
            title = item.get('title')
            item_name = item.get('agenda_item')

            if title == '' and item_name == '':
                # skip empty items
                continue

            if (title in current_items and item_name in
                    [i.display_name for i in current_items.values()]):
                # keep unchanged items
                new.append(current_items[title])
                continue

            business = next(
                (b for b in businesses.query().all()
                 if b.display_name == item_name), None)

            if business is None:
                new_item = MeetingItem(
                    title=title,
                    number=None,
                    political_business_id=None,
                    political_business=None,
                    meeting_id=obj.id,
                    meeting=obj,
                )
            else:
                new_item = MeetingItem(
                    title=title if title != '' else business.title,
                    number=business.number,
                    political_business_id=business.id,
                    political_business=business,
                    meeting_id=obj.id,
                    meeting=obj,
                )
            self.request.session.add(new_item)
            new.append(new_item)

        meeting.meeting_items = new

    def process_obj(self, obj: Meeting) -> None:  # type:ignore[override]
        from onegov.org.models import PoliticalBusiness

        super().process_obj(obj)

        meeting: Meeting = obj

        businesses = (
            self.meta.request.session.query(PoliticalBusiness)
            .order_by(PoliticalBusiness.number, PoliticalBusiness.title)
            .all()
        )

        if not meeting.meeting_items:
            self.meeting_items.data = self.items_to_json([], businesses)
        else:
            self.meeting_items.data = self.items_to_json(
                meeting.meeting_items, meeting.meeting_items + businesses
            )

    def json_to_items(self, text: str | None) -> list[str]:
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
                    'title': request.translate(_('Title')),
                    'agenda_item': request.translate(_('Agenda Item')),
                    'add': request.translate(_('Add')),
                    'remove': request.translate(_('Remove')),
                },
                # StringField: list of agenda items attached to this meeting
                'values': [
                    {
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
