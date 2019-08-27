from onegov.chat import Message
from onegov.core.orm.mixins import meta_property


class Notification(Message):
    """ A changelog entry for an official notice. """

    __mapper_args__ = {'polymorphic_identity': 'wtfs_notification'}

    title = meta_property('title')

    @classmethod
    def create(cls, request, title='', text=''):

        return cls.bound_messages(request.session).add(
            channel_id=request.identity.application_id,
            owner=request.identity.userid,
            text=text,
            meta={'title': title}
        )
