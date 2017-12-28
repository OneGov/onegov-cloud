import sedate

from cached_property import cached_property
from datetime import timedelta
from morepath import reify
from onegov.core.orm.mixins import meta_property, content_property
from onegov.core.utils import linkify
from onegov.directory import Directory, DirectoryEntry
from onegov.form import as_internal_id, Extendable, FormSubmission
from onegov.ticket import Ticket
from onegov.org import _
from onegov.org.models.message import DirectoryMessage
from onegov.org.models.extensions import CoordinatesExtension
from onegov.org.models.extensions import HiddenFromPublicExtension
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

    @reify
    def send_html_mail(self, **kwargs):
        # XXX circular import
        from onegov.org.mail import send_html_mail
        return send_html_mail

    @property
    def valid(self):
        return self.action in ('adopt', 'reject') and\
            self.directory and\
            self.submission

    def execute(self, request):
        assert self.valid
        getattr(self, self.action)(request)

    def adopt(self, request):
        import pdb; pdb.set_trace()

    def reject(self, request):
        self.ticket.create_snapshot(request)
        self.ticket.handler_data['directory'] = self.directory.id.hex

        if self.ticket.ticket_email != request.current_username:
            self.send_html_mail(
                request=request,
                template='mail_directory_entry_rejected.pt',
                subject=_("Your directory submission has been rejected"),
                receivers=(self.ticket.ticket_email, ),
                content={
                    'model': self.directory,
                    'ticket': self.ticket,
                }
            )

        self.session.delete(self.submission)
        request.success(_("The submission was rejected"))

        DirectoryMessage.create(
            self.directory, self.ticket, request, 'rejected'
        )


class ExtendedDirectory(Directory, HiddenFromPublicExtension, Extendable):
    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_directories'

    enable_map = meta_property('enable_map')
    enable_submissions = meta_property('enable_submissions')

    guideline = content_property('guideline')
    price = content_property('price')
    price_per_submission = content_property('price_per_submission')
    currency = content_property('currency')

    payment_method = meta_property('payment_method')

    @property
    def form_class_for_submissions(self):
        return self.extend_form_class(self.form_class, self.extensions)

    @property
    def extensions(self):
        if self.enable_map:
            return ('coordinates', 'submitter')
        else:
            return ('submitter', )

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
