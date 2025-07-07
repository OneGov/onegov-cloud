from __future__ import annotations

from wtforms import StringField
from wtforms.validators import Optional, InputRequired

from onegov.form import Form
from onegov.form.fields import TimezoneDateTimeField, ChosenSelectMultipleField
from onegov.org.forms.fields import HtmlField
from onegov.parliament import _
from onegov.parliament.models import Meeting, MeetingItem

from typing import TYPE_CHECKING
from collections.abc import Collection
if TYPE_CHECKING:
    from collections.abc import Collection


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

    agenda_items = ChosenSelectMultipleField(
        label=_('Agenda Items'),
        validators=[Optional()],
        choices=[],
    )

    def on_request(self) -> None:

        meetings = (self.request.session.query(MeetingItem)
                    .order_by(MeetingItem.number, MeetingItem.title)
                    .all())

        self.agenda_items.choices = [
            (item.id.hex, item.display_name())
            for item in meetings
        ]

    def populate_obj(
            self,
            obj: object,
            exclude: Collection[str] | None = None,
            include: Collection[str] | None = None
    ) -> None:
        if not isinstance(obj, Meeting):
            raise TypeError('Object must be a MeetingItem')

        meeting: Meeting = obj
        item: MeetingItem | None
        super().populate_obj(obj, exclude=exclude, include=include)

        meeting_item_ids = {item.id.hex for item in meeting.meeting_items}
        new_item_ids = set(self.agenda_items.data or [])

        items_to_add = new_item_ids - meeting_item_ids
        for new_id in items_to_add:
            item = (self.request.session.query(MeetingItem)
                    .filter(MeetingItem.id == new_id).one())
            if item is not None:
                meeting.meeting_items.append(item)

        items_to_remove = meeting_item_ids - new_item_ids
        for current_id in items_to_remove:
            item = self.request.session.query(MeetingItem).get(current_id)
            if item is not None:
                meeting.meeting_items.remove(item)

    def process_obj(self, obj: MeetingItem) -> None:  # type: ignore[override]
        if not isinstance(obj, Meeting):
            raise TypeError('Object must be a MeetingItem')

        super().process_obj(obj)

        self.agenda_items.data = [
            item.id.hex for item in obj.meeting_items
        ]
