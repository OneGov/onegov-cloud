from onegov.chat import Message
from onegov.core.orm.mixins import dict_property, meta_property


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from typing_extensions import Self


class Notification(Message):
    """ A changelog entry for an official notice. """

    __mapper_args__ = {'polymorphic_identity': 'wtfs_notification'}

    title: dict_property[str | None] = meta_property('title')

    @classmethod
    def create(
        cls,
        request: 'CoreRequest',
        title: str = '',
        text: str = ''
    ) -> 'Self':

        return cls.bound_messages(request.session).add(
            channel_id=request.identity.application_id,  # type:ignore
            owner=request.identity.userid,
            text=text,
            meta={'title': title}
        )
