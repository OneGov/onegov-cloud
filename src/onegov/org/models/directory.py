import sedate

from copy import copy
from datetime import timedelta
from functools import cached_property
from markupsafe import Markup
from sqlalchemy.ext.hybrid import hybrid_property

from onegov.core.orm.mixins import (
    content_property, dict_markup_property, dict_property, meta_property)
from onegov.core.utils import linkify
from onegov.directory import (
    Directory, DirectoryEntry, DirectoryEntryCollection)
from onegov.directory.errors import DuplicateEntryError, ValidationError
from onegov.directory.migration import DirectoryMigration
from onegov.form import as_internal_id, Extendable, FormSubmission
from onegov.form.submissions import prepare_for_submission
from onegov.org import _
from onegov.org.models.extensions import (
    CoordinatesExtension, GeneralFileLinkExtension, PublicationExtension,
    DeletableContentExtension)
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.message import DirectoryMessage
from onegov.pay import Price
from onegov.ticket import Ticket
from sqlalchemy import and_
from sqlalchemy.orm import object_session


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from onegov.directory.models.directory import DirectoryEntryForm
    from onegov.directory.collections.directory_entry import (
        DirectorySearchWidget)
    from onegov.form.fields import TimezoneDateTimeField
    from onegov.gis import CoordinatesField
    from onegov.org.request import OrgRequest
    from onegov.pay.types import PaymentMethod
    from sqlalchemy.orm import Query, Session, relationship
    from typing import type_check_only
    from typing_extensions import TypeAlias
    from uuid import UUID
    from wtforms import EmailField, Field, StringField, TextAreaField

    ExtendedDirectorySearchWidget: TypeAlias = DirectorySearchWidget[
        'ExtendedDirectoryEntry'
    ]

    # we extend this manually with all the form extensions
    # even though some of them may be disabled
    # FIXME: We should refactor this into some mixins probably
    @type_check_only
    class ExtendedDirectoryEntryForm(DirectoryEntryForm):
        submitter: EmailField
        submitter_name: StringField
        submitter_address: StringField
        submitter_phone: StringField
        comment: TextAreaField
        coordinates: CoordinatesField
        publication_start: TimezoneDateTimeField
        publication_end: TimezoneDateTimeField

        @property
        def submitter_meta(self) -> Mapping[str, str | None]: ...
        @property
        def target(self) -> 'ExtendedDirectoryEntry | None': ...
        def is_different(self, field: Field) -> bool: ...
        def ensure_changes(self) -> bool | None: ...
        def ensure_publication_start_end(self) -> bool | None: ...

        def render_original(
            self,
            field: Field,
            from_model: bool = False
        ) -> Markup: ...


class DirectorySubmissionAction:

    def __init__(
        self,
        session: 'Session',
        directory_id: 'UUID',
        action: str,
        submission_id: 'UUID'
    ) -> None:

        self.session = session
        self.directory_id = directory_id
        self.action = action
        self.submission_id = submission_id

    @cached_property
    def submission(self) -> FormSubmission | None:
        return (
            self.session.query(FormSubmission)
            .filter_by(id=self.submission_id)
            .first()
        )

    @cached_property
    def directory(self) -> Directory | None:
        return (
            self.session.query(Directory)
            .filter_by(id=self.directory_id)
            .first()
        )

    @cached_property
    def ticket(self) -> Ticket | None:
        return (
            self.session.query(Ticket)
            .filter_by(handler_id=self.submission_id.hex)
            .first()
        )

    def send_mail_if_enabled(
        self,
        request: 'OrgRequest',
        subject: str,
        template: str
    ) -> None:

        # XXX circular import
        from onegov.org.mail import send_ticket_mail

        assert self.ticket is not None and self.ticket.ticket_email
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
    def valid(self) -> bool:
        return True if (
            self.action in ('adopt', 'reject')
            and self.directory
            and self.submission
        ) else False

    def execute(self, request: 'OrgRequest') -> None:
        assert self.valid
        assert self.directory is not None
        assert self.ticket is not None

        self.ticket.create_snapshot(request)
        self.ticket.handler_data['directory'] = self.directory.id.hex

        return getattr(self, self.action)(request)

    def adopt(self, request: 'OrgRequest') -> None:
        assert self.directory is not None
        assert self.submission is not None
        assert self.ticket is not None

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

    def create_new_entry(
        self,
        request: 'OrgRequest',
        data: dict[str, Any]
    ) -> DirectoryEntry:

        assert self.directory is not None
        entry = self.directory.add(data)
        entry.coordinates = data.get('coordinates')  # type:ignore[assignment]

        self.send_mail_if_enabled(
            request=request,
            template='mail_directory_entry_adopted.pt',
            subject=_("Your directory submission has been adopted"),
        )

        request.success(_("The submission was adopted"))

        assert self.ticket is not None
        DirectoryMessage.create(
            self.directory, self.ticket, request, 'adopted')

        return entry

    def apply_change_request(
        self,
        request: 'OrgRequest',
        data: dict[str, Any]
    ) -> DirectoryEntry:

        assert isinstance(self.directory, ExtendedDirectory)
        assert self.submission is not None

        entry = (
            request.session.query(ExtendedDirectoryEntry)
            .filter_by(id=self.submission.meta['directory_entry'])
            .one()
        )

        changed = []
        values = copy(entry.values)
        form = self.submission.form_class(data=data)
        form.request = request
        form.model = self.submission

        # not stored in content but captured by form.is_different in order
        # to show the user the changes since he can modify them
        publication_properties = ('publication_start', 'publication_end')

        for name, field in form._fields.items():
            # FIXME: Form extensions are tricky
            if form.is_different(field):  # type:ignore[attr-defined]
                if (
                    name in publication_properties
                    and self.directory.enable_publication
                ):
                    setattr(entry, name, data.get(name))
                    changed.append(name)
                    continue

                values[name] = form.data[name]
                changed.append(name)

        self.directory.update(entry, values)

        # coordinates can only be set, not deleted at this point
        if entry.coordinates != (coordinates := data.get('coordinates')):
            if coordinates:
                entry.coordinates = coordinates

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

        assert self.ticket is not None
        DirectoryMessage.create(
            self.directory, self.ticket, request, 'applied')

        return entry

    def reject(self, request: 'OrgRequest') -> None:
        assert self.ticket is not None

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

        assert self.directory is not None
        request.success(_("The submission was rejected"))
        DirectoryMessage.create(
            self.directory, self.ticket, request, 'rejected')


class ExtendedDirectory(Directory, AccessExtension, Extendable,
                        GeneralFileLinkExtension):
    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_directories'

    content_fields_containing_links_to_files = {
        'text',
        'submissions_guideline',
        'change_requests_guideline'
    }

    enable_map: dict_property[str | None] = meta_property()
    enable_submissions: dict_property[bool | None] = meta_property()
    enable_change_requests: dict_property[bool | None] = meta_property()
    enable_publication: dict_property[bool | None] = meta_property()
    enable_update_notifications: dict_property[bool | None] = meta_property()
    required_publication: dict_property[bool | None] = meta_property()
    submitter_meta_fields: dict_property[list[str] | None] = meta_property()

    submissions_guideline = dict_markup_property('content')
    change_requests_guideline = dict_markup_property('content')

    text = dict_markup_property('content')
    title_further_information: dict_property[str | None] = content_property()
    position: dict_property[str] = content_property(default='below')
    price: dict_property[Literal['free', 'paid'] | None] = content_property()
    price_per_submission: dict_property[float | None] = content_property()
    currency: dict_property[str | None] = content_property()

    minimum_price_total: dict_property[float | None] = meta_property()
    payment_method: dict_property['PaymentMethod | None'] = meta_property()

    search_widget_config: dict_property[dict[str, Any] | None]
    search_widget_config = content_property()

    marker_icon: dict_property[str | None] = content_property()
    marker_color: dict_property[str | None] = content_property()

    overview_two_columns: dict_property[bool | None] = content_property()
    numbering: dict_property[str | None] = content_property()
    numbers: dict_property[str | None] = content_property()

    layout: dict_property[str | None] = content_property(default='default')

    @property
    def entry_cls_name(self) -> str:
        return 'ExtendedDirectoryEntry'

    @hybrid_property
    def es_public(self) -> bool:
        return self.access == 'public'

    if TYPE_CHECKING:
        def extend_form_class(  # type:ignore[override]
            self,
            form_class: type['DirectoryEntryForm'],  # type:ignore[override]
            extensions: Collection[str]
        ) -> type['ExtendedDirectoryEntryForm']: ...

    def form_class_for_submissions(
        self,
        change_request: bool = False
    ) -> type['ExtendedDirectoryEntryForm']:
        """ Generates the form_class used for user submissions and change
        requests. The resulting form always includes a submitter field and all
        fields. When doing a change request, removes input required validators
        from UploadFields.

        """
        form_class = self.extend_form_class(self.form_class, self.extensions)
        form_class = prepare_for_submission(form_class, change_request)
        return form_class

    @property
    def extensions(self) -> tuple[str, ...]:
        extensions = ['coordinates', 'submitter', 'comment', 'publication']
        if self.enable_map == 'no':
            extensions.remove('coordinates')
        if not self.enable_publication:
            extensions.remove('publication')
        return tuple(extensions)

    @property
    def actual_price(self) -> Price | None:
        return Price(
            # we assume there was a price if it was paid
            amount=self.price_per_submission,  # type:ignore
            currency=self.currency
        ) if self.price == 'paid' else None

    def submission_action(
        self,
        action: Literal['adopt', 'reject'],
        submission_id: 'UUID'
    ) -> DirectorySubmissionAction:

        return DirectorySubmissionAction(
            session=object_session(self),
            directory_id=self.id,
            action=action,
            submission_id=submission_id
        )

    def remove_old_pending_submissions(self) -> None:
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
                             CoordinatesExtension, AccessExtension,
                             DeletableContentExtension):
    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_directory_entries'

    internal_notes: dict_property[str | None] = content_property()

    if TYPE_CHECKING:
        # technically not enforced, but it should be a given
        directory: relationship[ExtendedDirectory]

    @hybrid_property
    def es_public(self) -> bool:
        return self.access == 'public' and self.published

    @property
    def display_config(self) -> dict[str, Any]:
        return self.directory.configuration.display or {}

    @property
    def contact(self) -> Markup | None:
        contact_config = tuple(
            as_internal_id(name) for name in
            self.display_config.get('contact', ())
        )

        if contact_config:
            values: list[str | None]
            if self.directory.configuration.address_block_title:
                values = [self.directory.configuration.address_block_title]
            else:
                values = []

            for name in contact_config:
                values.append(self.values.get(name))

            result = Markup('\n').join(linkify(v) for v in values if v)

            return Markup('<ul><li>{}</li></ul>').format(
                Markup('</li><li>').join(result.splitlines())
            )
        return None

    @property
    def content_fields(self) -> tuple['Field', ...] | None:
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
        return None

    @property
    def hidden_label_fields(self) -> set[str]:
        return {
            as_internal_id(k)
            for k in self.display_config.get('content_hide_labels', ())
        }


class ExtendedDirectoryEntryCollection(
    DirectoryEntryCollection[ExtendedDirectoryEntry]
):

    def __init__(
        self,
        directory: ExtendedDirectory,
        # FIXME: We should probably disallow the type argument here
        type: Literal['extended'] = 'extended',
        keywords: 'Mapping[str, list[str]] | None' = None,
        page: int = 0,
        search_widget: 'ExtendedDirectorySearchWidget | None' = None,
        published_only: bool = False,
        past_only: bool = False,
        upcoming_only: bool = False
    ) -> None:

        super().__init__(directory, type, keywords, page, search_widget)
        self.published_only = published_only
        self.past_only = past_only
        self.upcoming_only = upcoming_only

    if TYPE_CHECKING:
        directory: ExtendedDirectory

    def query(self) -> 'Query[ExtendedDirectoryEntry]':
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
