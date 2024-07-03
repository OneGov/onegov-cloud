from onegov.chat import MessageCollection


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.wtfs.models import Notification  # noqa:F401
    from sqlalchemy.orm import Session


class NotificationCollection(MessageCollection['Notification']):

    def __init__(
        self,
        session: 'Session',
        # FIXME: this argument exists only for backwards compatibility
        #        we should probably get rid of it entirely
        type: None = None,
        channel_id: str = '*',
        newer_than: str | None = None,
        older_than: str | None = None,
        limit: int | None = None,
        load: Literal['older-first', 'newer-first'] = 'older-first'
    ):
        super().__init__(
            session,
            type='wtfs_notification',
            channel_id=channel_id,
            newer_than=newer_than,
            older_than=older_than,
            limit=limit,
            load=load
        )
