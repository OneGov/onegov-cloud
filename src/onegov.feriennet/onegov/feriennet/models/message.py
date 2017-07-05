from onegov.activity import Period
from onegov.org.models.message import TemplateRenderedMessage


class PeriodMessage(TemplateRenderedMessage):

    __mapper_args__ = {
        'polymorphic_identity': 'period'
    }

    def link(self, request):
        return request.class_link(Period, {'id': self.channel_id})

    @classmethod
    def create(cls, period, request, action):
        assert request.current_username, "reserved for logged-in users"

        return cls.bound_messages(request).add(
            channel_id=period.id.hex,
            owner=request.current_username,
            meta={
                'title': period.title,
                'action': action
            }
        )
