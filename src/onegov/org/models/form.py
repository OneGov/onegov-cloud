from onegov.file import MultiAssociatedFiles
from onegov.form.models import FormDefinition
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.extensions import ContactExtension
from onegov.org.models.extensions import CoordinatesExtension
from onegov.org.models.extensions import GeneralFileLinkExtension
from onegov.org.models.extensions import HoneyPotExtension
from onegov.org.models.extensions import PersonLinkExtension
from onegov.search import SearchableContent
from onegov.ticket import TicketCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form.models import FormSubmission
    from onegov.ticket import Ticket
    from sqlalchemy.orm import Session


class BuiltinFormDefinition(FormDefinition, AccessExtension,
                            ContactExtension, PersonLinkExtension,
                            CoordinatesExtension, SearchableContent,
                            HoneyPotExtension, MultiAssociatedFiles,
                            GeneralFileLinkExtension):
    __mapper_args__ = {'polymorphic_identity': 'builtin'}

    es_type_name = 'builtin_forms'
    es_id = 'name'

    # FIXME: should this have a setter?
    @property
    def extensions(self) -> tuple[str, ...]:  # type:ignore[override]
        return tuple(set(super().extensions + ['honeypot']))


class CustomFormDefinition(FormDefinition, AccessExtension,
                           ContactExtension, PersonLinkExtension,
                           CoordinatesExtension, SearchableContent,
                           HoneyPotExtension, MultiAssociatedFiles,
                           GeneralFileLinkExtension):
    __mapper_args__ = {'polymorphic_identity': 'custom'}

    es_type_name = 'custom_forms'
    es_id = 'name'
    default_extensions = ['honeypot']

    # FIXME: should this have a setter?
    @property
    def extensions(self) -> tuple[str, ...]:  # type:ignore[override]
        return tuple(set(super().extensions + ['honeypot']))


def submission_deletable(
    submission: 'FormSubmission',
    session: 'Session',
    payment_blocks: bool = True
) -> 'Ticket | bool':
    """ CustomFormDefinition's are normally linked to a ticket.

    Submissions without registration window do not require a decision. The
    ticket state decides, whether the form definition can be deleted to
    provide some safeguard.

    With registration window, we can check if the submission is decided and
    can close the ticket even if it is still pending.
    """
    tickets = TicketCollection(session)
    ticket = tickets.by_handler_id(submission.id.hex)
    if submission.registration_window_id:
        if payment_blocks and submission.payment:
            return False
        if not ticket:
            return True
        if ticket.state == 'open':
            return ticket
        if ticket.handler.undecided:
            return False
    elif ticket and ticket.state not in ('closed', 'archived'):
        return False
    if payment_blocks and submission.payment:
        return False
    if not ticket:
        return True
    return ticket
