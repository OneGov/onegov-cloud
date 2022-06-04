from cached_property import cached_property
from onegov.agency import _


class TranslatorMutation:

    def __init__(self, session, target_id, ticket_id):
        self.session = session
        self.target_id = target_id
        self.ticket_id = ticket_id

    @cached_property
    def collection(self):
        from onegov.translator_directory.collections.translator import \
            TranslatorCollection
        return TranslatorCollection(self.session, user_role='admin')

    @cached_property
    def target(self):
        return self.collection.by_id(self.target_id)

    @cached_property
    def ticket(self):
        from onegov.ticket import TicketCollection
        return TicketCollection(self.session).by_id(self.ticket_id)

    @cached_property
    def changes(self):
        handler_data = self.ticket.handler_data['handler_data']
        result = handler_data.get('proposed_changes', {})
        result = {k: v for k, v in result.items() if hasattr(self.target, k)}
        return result

    @property
    def labels(self):
        # todo:
        return {
            'first_name': _("First name"),
            'last_name': _("Last name"),
        }

    def apply(self, items):
        self.ticket.handler_data['state'] = 'applied'
        for item in items:
            if item in self.changes:
                setattr(self.target, item, self.changes[item])
