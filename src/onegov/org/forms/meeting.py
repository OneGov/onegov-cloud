from __future__ import annotations

from wtforms.validators import Optional, InputRequired
from wtforms import StringField

from onegov.form import Form
from onegov.form.fields import TimezoneDateTimeField, ChosenSelectMultipleField
from onegov.org.forms.fields import HtmlField
from onegov.org import _

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.org.models import Meeting


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

    meeting_items = ChosenSelectMultipleField(
        label=_('Agenda Items'),
        choices=[],
        validators=[Optional()]
    )

    def on_request(self) -> None:
        from onegov.org.models import MeetingItem

        meetings = (
            self.request.session.query(MeetingItem)
            .order_by(MeetingItem.number, MeetingItem.title)
            .all()
        )
        self.meeting_items.choices = [
            (item.id.hex, item.display_name)
            for item in meetings
        ]

    def populate_obj(  # type:ignore[override]
        self,
        obj: Meeting,  # type:ignore[override]
        exclude: Collection[str] | None = None,
        include: Collection[str] | None = None
    ) -> None:
        from onegov.org.models import MeetingItem

        super().populate_obj(
            obj,
            exclude={
                'meeting_items',
                *(exclude or ())
            },
            include=include
        )

        meeting: Meeting = obj
        meeting_item_ids = {item.id.hex for item in meeting.meeting_items}
        new_item_ids = set(self.meeting_items.data or [])

        items_to_add = new_item_ids - meeting_item_ids
        for new_id in items_to_add:
            item = (
                self.request.session.query(MeetingItem)
                .filter(MeetingItem.id == new_id)
                .one()
            )
            if item is not None:
                meeting.meeting_items.append(item)

        items_to_remove = meeting_item_ids - new_item_ids
        for current_id in items_to_remove:
            item = (
                self.request.session.query(MeetingItem)
                .filter(MeetingItem.id == current_id)
                .one()
            )
            if item is not None:
                meeting.meeting_items.remove(item)

    def process_obj(self, obj: Meeting) -> None:  # type:ignore[override]
        super().process_obj(obj)

        meeting: Meeting = obj
        self.meeting_items.data = [
            item.id.hex for item in meeting.meeting_items
        ]
