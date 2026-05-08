from __future__ import annotations

from onegov.core.orm.mixins import content_property, dict_property
from onegov.recipient import GenericRecipient, GenericRecipientCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ResourceRecipient(GenericRecipient):
    __mapper_args__ = {'polymorphic_identity': 'resource'}

    daily_reservations: dict_property[bool | None] = content_property()
    new_reservations: dict_property[bool | None] = content_property()
    customer_messages: dict_property[bool | None] = content_property()
    internal_notes: dict_property[bool | None] = content_property()
    send_on: dict_property[list[str] | None] = content_property()
    rejected_reservations: dict_property[bool | None] = content_property()
    resources: dict_property[list[str] | None] = content_property()


class ResourceRecipientCollection(
    GenericRecipientCollection[ResourceRecipient]
):
    def __init__(self, session: Session) -> None:
        super().__init__(session, type='resource')
