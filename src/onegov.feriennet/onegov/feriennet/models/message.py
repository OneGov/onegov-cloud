from onegov.activity import Period
from onegov.chat import Message
from onegov.org.models.message import TicketMessageMixin


class PeriodMessage(Message):

    __mapper_args__ = {
        'polymorphic_identity': 'period'
    }

    def link(self, request):
        return request.class_link(Period, {'id': self.channel_id})

    @classmethod
    def create(cls, period, request, action):
        assert request.current_username, "reserved for logged-in users"

        return cls.bound_messages(request.session).add(
            channel_id=period.id.hex,
            owner=request.current_username,
            meta={
                'title': period.title,
                'action': action
            }
        )


class ActivityMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'activity'
    }

    @classmethod
    def create(cls, ticket, request, action, extra_meta=None):
        return super().create(
            ticket, request, action=action, extra_meta=extra_meta)
