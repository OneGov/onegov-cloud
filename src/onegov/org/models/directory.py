import inspect
import sedate

from cached_property import cached_property
from copy import copy
from datetime import timedelta
from onegov.core.orm.mixins import meta_property, content_property
from onegov.core.utils import linkify
from onegov.directory import Directory, DirectoryEntry
from onegov.directory.errors import DuplicateEntryError, ValidationError
from onegov.directory.migration import DirectoryMigration
from onegov.form import as_internal_id, Extendable, FormSubmission
from onegov.form.fields import UploadField
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

    def send_mail_if_enabled(self, request, subject, template):

        # XXX circular import
        from onegov.org.mail import send_ticket_mail

        return send_ticket_mail(
            request=request,
            template=template,
            subject=subject,
            receivers=(self.ticket.ticket_email, ),
            ticket=self.ticket,
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

        # if the migration fails, update the form on the submission
        # and redirect to it so it can be fixed
        if not migration.possible:
            request.alert(_("The entry is not valid, please adjust it"))
            return

        data = self.submission.data.copy()
        migration.migrate_values(data)

        try:
            if 'change-request' in self.submission.meta['extensions']:
                entry = self.apply_change_request(request, data)
            else:
                entry = self.create_new_entry(request, data)

        except DuplicateEntryError:
            request.alert(_("An entry with this name already exists"))
            return
        except ValidationError:
            request.alert(_("The entry is not valid, please adjust it"))
            return

        self.ticket.handler_data['entry_name'] = entry.name
        self.ticket.handler_data['state'] = 'adopted'

    def create_new_entry(self, request, data):
        entry = self.directory.add(data)
        entry.coordinates = data.get('coordinates')

        self.send_mail_if_enabled(
            request=request,
            template='mail_directory_entry_adopted.pt',
            subject=_("Your directory submission has been adopted"),
        )

        request.success(_("The submission was adopted"))

        DirectoryMessage.create(
            self.directory, self.ticket, request, 'adopted')

        return entry

    def apply_change_request(self, request, data):
        entry = request.session.query(ExtendedDirectoryEntry)\
            .filter_by(id=self.submission.meta['directory_entry'])\
            .one()

        changed = []
        values = copy(entry.values)
        form = self.submission.form_class(data=data)
        form.request = request
        form.model = self.submission

        for name, field in form._fields.items():
            if form.is_different(field):
                values[name] = form.data[name]
                changed.append(name)

        self.directory.update(entry, values)

        # coordinates can only be set, not deleted at this point
        if entry.coordinates != data.get('coordinates'):
            if data.get('coordinates'):
                entry.coordinates = data.get('coordinates')

            changed.append('coordinates')

        # keep a list of changes so the change request extension can
        # still show the changes (the change detection no longer works once
        # the changes have been applied)
        self.submission.meta['changed'] = changed

        self.send_mail_if_enabled(
            request=request,
            template='mail_directory_entry_applied.pt',
            subject=_("Your change request has been applied"),
        )

        request.success(_("The change request was applied"))

        DirectoryMessage.create(
            self.directory, self.ticket, request, 'applied')

        return entry

    def reject(self, request):

        # be idempotent
        if self.ticket.handler_data.get('state') == 'rejected':
            request.success(_("The submission was rejected"))
            return

        self.ticket.handler_data['state'] = 'rejected'

        self.send_mail_if_enabled(
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
    enable_change_requests = meta_property()

    submissions_guideline = content_property()
    change_requests_guideline = content_property()

    text = content_property()
    price = content_property()
    price_per_submission = content_property()
    currency = content_property()

    payment_method = meta_property()

    searchwidget_config = content_property()

    marker_icon = content_property()
    marker_color = content_property()

    @property
    def es_public(self):
        return not self.is_hidden_from_public

    def form_class_for_submissions(self, include_private):
        """ Generates the form_class used for user submissions and change
        requests. The resulting form always includes a submitter field and all
        fields (when submitting) or only public fields (when requesting a
        change).

        """

        form_class = self.extend_form_class(self.form_class, self.extensions)

        # force all upload fields to be simple, we do not support the more
        # complex add/keep/replace widget, which is hard to properly support
        # and is not super useful in submissions
        def is_upload(attribute):
            if not hasattr(attribute, 'field_class'):
                return None

            return issubclass(attribute.field_class, UploadField)

        for name, field in inspect.getmembers(form_class, predicate=is_upload):
            if 'render_kw' not in field.kwargs:
                field.kwargs['render_kw'] = {}

            field.kwargs['render_kw']['force_simple'] = True

        return form_class

    @property
    def extensions(self):
        if self.enable_map == 'no':
            return ('submitter', 'comment')
        else:
            return ('coordinates', 'submitter', 'comment')

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
