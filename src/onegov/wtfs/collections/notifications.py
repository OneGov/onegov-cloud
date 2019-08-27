from onegov.chat import MessageCollection


class NotificationCollection(MessageCollection):

    def __init__(self, session, **kwargs):
        kwargs.pop('type', None)
        super().__init__(session, type='wtfs_notification', **kwargs)
