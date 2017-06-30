from onegov.chat import Message
from onegov.org import _


class TicketChangeMessage(Message):

    __mapper_args__ = {
        'polymorphic_identity': 'ticket_change'
    }

    def get(self, request):
        if self.meta['change'] == 'accepted':
            return request.translate(_("${ticket} was accepted", mapping={
                'ticket': self.channel_id
            }))
        elif self.meta['change'] == 'closed':
            return request.translate(_("${ticket} was closed", mapping={
                'ticket': self.channel_id
            }))
        elif self.meta['change'] == 'reopened':
            return request.translate(_("${ticket} was reopened", mapping={
                'ticket': self.channel_id
            }))
        else:
            raise NotImplementedError
