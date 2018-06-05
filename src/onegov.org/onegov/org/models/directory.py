import sedate

from cached_property import cached_property
from datetime import timedelta
from onegov.core.orm.mixins import meta_property, content_property
from onegov.core.utils import linkify
from onegov.directory import Directory, DirectoryEntry
from onegov.directory.errors import DuplicateEntryError, ValidationError
from onegov.directory.migration import DirectoryMigration
from onegov.form import as_internal_id, Extendable, FormSubmission
from onegov.org import _
from onegov.org.models.extensions import CoordinatesExtension
from onegov.org.models.extensions import HiddenFromPublicExtension
from onegov.org.models.message import DirectoryMessage
from onegov.pay import Price
from onegov.ticket import Ticket
from sqlalchemy import and_
from sqlalchemy.orm import object_session


class DirectorySubmissionAction(object):

    def __init__(self, session, directory_id, action, submission_id):
        self.session = session
        self.directory_id = directory_id
        self.action = action
        self.submission_id = submission_id

    @cached_property
    def submission(self):
        return self.session.query(FormSubmission)\
            .filter_by(id=self.submission_id)\
            .first()

    @cached_property
    def directory(self):
        return self.session.query(Directory)\
            .filter_by(id=self.directory_id)\
            .first()

    @cached_property
    def ticket(self):
        return self.session.query(Ticket)\
            .filter_by(handler_id=self.submission_id.hex)\
            .first()

    def send_html_mail(self, request, subject, template):
        # XXX circular import
        from onegov.org.mail import send_transactional_html_mail

        return send_transactional_html_mail(
            request=request,
            template=template,
            subject=subject,
            receivers=(self.ticket.ticket_email, ),
            content={
                'model': self.directory,
                'ticket': self.ticket
            }
        )

    @property
    def valid(self):
        return self.action in ('adopt', 'reject') and\
            self.directory and\
            self.submission

    def execute(self, request):
        assert self.valid

        self.ticket.create_snapshot(request)
        self.ticket.handler_data['directory'] = self.directory.id.hex

        return getattr(self, self.action)(request)

    def adopt(self, request):

        # be idempotent
        if self.ticket.handler_data.get('state') == 'adopted':
            request.success(_("The submission was adopted"))
            return

        # the directory might have changed -> migrate what we can
        migration = DirectoryMigration(
            directory=self.directory,
            old_structure=self.submission.definition
        )

        # whenever we try to adopt a submission, we update its structure
        # so we can edit the entry with the updated structure if the adoption
        # fails
        self.submission.definition = self.directory.structure

        # if the migration failes, update the form on the submission
        # and redirect to it so it can be fixed
        if not migration.possible:
            request.alert(_("The entry is not valid, please adjust it"))
            return

        data = self.submission.data.copy()
        migration.migrate_values(data)

        try:
            entry = self.directory.add(data)
        except DuplicateEntryError:
            request.alert(_("An entry with this name already exists"))
            return
        except ValidationError:
            request.alert(_("The entry is not valid, please adjust it"))
            return

        self.ticket.handler_data['entry_name'] = entry.name
        self.ticket.handler_data['state'] = 'adopted'

        entry.coordinates = self.submission.data.get('coordinates')

        if self.ticket.ticket_email != request.current_username:
            self.send_html_mail(
                request=request,
                template='mail_directory_entry_adopted.pt',
                subject=_("Your directory submission has been adopted"),
            )

        request.success(_("The submission was adopted"))
        DirectoryMessage.create(
            self.directory, self.ticket, request, 'adopted')

    def reject(self, request):

        # be idempotent
        if self.ticket.handler_data.get('state') == 'rejected':
            request.success(_("The submission was rejected"))
            return

        self.ticket.handler_data['state'] = 'rejected'

        if self.ticket.ticket_email != request.current_username:
            self.send_html_mail(
                request=request,
                template='mail_directory_entry_rejected.pt',
                subject=_("Your directory submission has been rejected"),
            )

        request.success(_("The submission was rejected"))
        DirectoryMessage.create(
            self.directory, self.ticket, request, 'rejected')


class ExtendedDirectory(Directory, HiddenFromPublicExtension, Extendable):
    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_directories'

    enable_map = meta_property()
    enable_submissions = meta_property()

    text = content_property()
    guideline = content_property()
    price = content_property()
    price_per_submission = content_property()
    currency = content_property()

    payment_method = meta_property()

    searchwidget_config = content_property()

    @property
    def es_public(self):
        return not self.is_hidden_from_public

    @property
    def form_class_for_submissions(self):
        return self.extend_form_class(self.form_class, self.extensions)

    @property
    def extensions(self):
        if self.enable_map:
            return ('coordinates', 'submitter')
        else:
            return ('submitter', )

    @property
    def actual_price(self):
        return self.price == 'paid' and Price(
            amount=self.price_per_submission,
            currency=self.currency
        )

    def submission_action(self, action, submission_id):
        return DirectorySubmissionAction(
            session=object_session(self),
            directory_id=self.id,
            action=action,
            submission_id=submission_id
        )

    def remove_old_pending_submissions(self):
        session = object_session(self)
        horizon = sedate.utcnow() - timedelta(hours=24)

        submissions = session.query(FormSubmission).filter(and_(
            FormSubmission.state == 'pending',
            FormSubmission.meta['directory'] == self.id.hex,
            FormSubmission.last_change < horizon
        ))

        for submission in submissions:
            session.delete(submission)


class ExtendedDirectoryEntry(DirectoryEntry, CoordinatesExtension,
                             HiddenFromPublicExtension):
    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_directory_entries'

    @property
    def es_public(self):
        return not self.is_hidden_from_public

    @property
    def display_config(self):
        return self.directory.configuration.display or {}

    @property
    def contact(self):
        contact_config = tuple(
            as_internal_id(name) for name in
            self.display_config.get('contact', tuple())
        )

        if contact_config:
            values = (self.values.get(name) for name in contact_config)
            value = '\n'.join(linkify(v) for v in values if v)

            return '<ul><li>{}</li></ul>'.format(
                '</li><li>'.join(linkify(value).splitlines())
            )

    @property
    def content_fields(self):
        content_config = {
            as_internal_id(k)
            for k in self.display_config.get('content', tuple())
        }

        if content_config:
            form = self.directory.form_class(data=self.values)

            return tuple(
                field for field in form._fields.values()
                if field.id in content_config and field.data
            )
