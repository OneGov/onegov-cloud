import sedate

from copy import copy
from datetime import timedelta
from functools import cached_property
from onegov.core.orm.mixins import meta_property, content_property
from onegov.core.utils import linkify
from onegov.directory import (
    Directory, DirectoryEntry, DirectoryEntryCollection)
from onegov.directory.errors import DuplicateEntryError, ValidationError
from onegov.directory.migration import DirectoryMigration
from onegov.form import as_internal_id, Extendable, FormSubmission
from onegov.form.submissions import prepare_for_submission
from onegov.org import _
from onegov.org.models.extensions import (
    CoordinatesExtension, PublicationExtension)
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.message import DirectoryMessage
from onegov.pay import Price
from onegov.ticket import Ticket
from sqlalchemy import and_
from sqlalchemy.orm import object_session


class DirectorySubmissionAction:

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

        # not stored in content but captured by form.is_different in order
        # to show the user the changes since he can modify them
        publication_properties = ('publication_start', 'publication_end')

        for name, field in form._fields.items():
            if form.is_different(field):
                if name in publication_properties and \
                        self.directory.enable_publication:
                    setattr(entry, name, data.get(name))
                    changed.append(name)
                    continue

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


class ExtendedDirectory(Directory, AccessExtension, Extendable):
    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_directories'

    enable_map = meta_property()
    enable_submissions = meta_property()
    enable_change_requests = meta_property()
    enable_publication = meta_property()
    required_publication = meta_property()
    submitter_meta_fields = meta_property()

    submissions_guideline = content_property()
    change_requests_guideline = content_property()

    text = content_property()
    title_further_information = content_property()
    position = content_property(default='below')
    price = content_property()
    price_per_submission = content_property()
    currency = content_property()

    minimum_price_total = meta_property()
    payment_method = meta_property()

    search_widget_config = content_property()

    marker_icon = content_property()
    marker_color = content_property()

    overview_two_columns = content_property()
    numbering = content_property()
    numbers = content_property()

    @property
    def entry_cls_name(self):
        return 'ExtendedDirectoryEntry'

    @property
    def es_public(self):
        return self.access == 'public'

    def form_class_for_submissions(self, change_request=False):
        """ Generates the form_class used for user submissions and change
        requests. The resulting form always includes a submitter field and all
        fields. When doing a change request, removes input required validators
        from UploadFields.

        """
        form_class = self.extend_form_class(self.form_class, self.extensions)
        form_class = prepare_for_submission(form_class, change_request)
        return form_class

    @property
    def extensions(self):
        extensions = ['coordinates', 'submitter', 'comment', 'publication']
        if self.enable_map == 'no':
            extensions.pop(extensions.index('coordinates'))
        if not self.enable_publication:
            extensions.pop(extensions.index('publication'))
        return tuple(extensions)

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


class ExtendedDirectoryEntry(DirectoryEntry, PublicationExtension,
                             CoordinatesExtension, AccessExtension):
    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_directory_entries'

    @property
    def es_public(self):
        return self.access == 'public' and self.published

    @property
    def display_config(self):
        return self.directory.configuration.display or {}

    @property
    def contact(self):
        contact_config = tuple(
            as_internal_id(name) for name in
            self.display_config.get('contact', ())
        )

        if contact_config:
            if self.directory.configuration.address_block_title:
                values = [self.directory.configuration.address_block_title]
            else:
                values = []

            for name in contact_config:
                values.append(self.values.get(name))

            result = '\n'.join(linkify(v) for v in values if v)

            return '<ul><li>{}</li></ul>'.format(
                '</li><li>'.join(result.splitlines())
            )

    @property
    def content_fields(self):
        content_config = {
            as_internal_id(k)
            for k in self.display_config.get('content', ())
        }

        if content_config:
            form = self.directory.form_class(data=self.values)

            return tuple(
                field for field in form._fields.values()
                if field.id in content_config and field.data
            )

    @property
    def hidden_label_fields(self):
        return {
            as_internal_id(k)
            for k in self.display_config.get('content_hide_labels', ())
        }


class ExtendedDirectoryEntryCollection(
    DirectoryEntryCollection[ExtendedDirectoryEntry]
):

    def __init__(
        self,
        directory,
        # FIXME: We should probably disallow the type argument here
        type='extended',
        keywords=None,
        page=0,
        search_widget=None,
        published_only=None,
        past_only=None,
        upcoming_only=None
    ):
        super().__init__(directory, type, keywords, page, search_widget)
        self.published_only = published_only
        self.past_only = past_only
        self.upcoming_only = upcoming_only

    def query(self):
        query = super().query()
        if self.published_only:
            query = query.filter(
                self.model_class.publication_started == True,
                self.model_class.publication_ended == False
            )
        elif self.past_only:
            query = query.filter(self.model_class.publication_ended == True)
        elif self.upcoming_only:
            query = query.filter(self.model_class.publication_started == False)
        return query
