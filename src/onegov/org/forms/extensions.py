from __future__ import annotations

from functools import cached_property
from sedate import utcnow, to_timezone

from onegov.core.html_diff import render_html_diff
from onegov.form.extensions import FormExtension
from onegov.form.fields import HoneyPotField
from onegov.form.fields import TimezoneDateTimeField
from onegov.form.fields import UploadField
from onegov.form.fields import MultiCheckboxField
from onegov.form.submissions import prepare_for_submission
from onegov.form.validators import StrictOptional, ValidPhoneNumber
from onegov.gis import CoordinatesField
from onegov.org import _
from wtforms.fields import BooleanField
from wtforms.fields import EmailField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import DataRequired, InputRequired, ValidationError


from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from markupsafe import Markup
    from onegov.form import Form
    from wtforms import Field


FormT = TypeVar('FormT', bound='Form')


class CoordinatesFormExtension(FormExtension[FormT], name='coordinates'):

    def create(self) -> type[FormT]:
        class CoordinatesForm(self.form_class):  # type:ignore
            coordinates = CoordinatesField(
                label=_('Coordinates'),
                description=_(
                    'The marker can be moved by dragging it with the mouse'
                ),
                fieldset=_('Map'),
                render_kw={'data-map-type': 'marker'}
            )

        return CoordinatesForm


class SubmitterFormExtension(FormExtension[FormT], name='submitter'):

    def create(self) -> type[FormT]:
        class SubmitterForm(self.form_class):  # type:ignore

            submitter = EmailField(
                label=_('E-Mail'),
                fieldset=_('Submitter'),
                validators=[DataRequired()]
            )

            submitter_name = StringField(
                label=_('Name'),
                fieldset=_('Submitter'),
                validators=[InputRequired()]
            )

            submitter_address = StringField(
                label=_('Address'),
                fieldset=_('Submitter'),
                validators=[InputRequired()]
            )

            submitter_phone = StringField(
                label=_('Phone'),
                fieldset=_('Submitter'),
                validators=[InputRequired(), ValidPhoneNumber()]
            )

            def on_request(self) -> None:
                # This is not an optimal solution defining this on a form
                # extension. However, this is the first of it's kind.
                # Don't forget to call super for the next one. =)
                if hasattr(super(), 'on_request'):
                    super().on_request()

                if not hasattr(self.model, 'directory'):
                    fields: Collection[str] = []
                else:
                    fields = self.model.directory.submitter_meta_fields or []
                for field in ('name', 'address', 'phone'):
                    if f'submitter_{field}' not in fields:
                        self.delete_field(f'submitter_{field}')

            @property
            def submitter_meta(self) -> dict[str, str | None]:

                def field_data(name: str) -> str | None:
                    field = getattr(self, name)
                    return field and field.data or None

                return {
                    'submitter_name': field_data('submitter_name'),
                    'submitter_phone': field_data('submitter_phone'),
                    'submitter_address': field_data('submitter_address')
                }

        return SubmitterForm


class CommentFormExtension(FormExtension[FormT], name='comment'):

    def create(self) -> type[FormT]:
        class CommentForm(self.form_class):  # type:ignore
            comment = TextAreaField(
                label=_('Comment'),
                fieldset=_('Submitter'),
                render_kw={'rows': 7}
            )

        return CommentForm


class ChangeRequestFormExtension(FormExtension[FormT], name='change-request'):

    def create(self) -> type[FormT]:

        # XXX circular import
        from onegov.org.models.directory import ExtendedDirectoryEntry
        prepare_for_submission(self.form_class, for_change_request=True)

        class ChangeRequestForm(self.form_class):  # type:ignore

            @cached_property
            def target(self) -> ExtendedDirectoryEntry | None:

                # not all steps have this information set, for example, towards
                # the end, the onegov.form submission code runs an extra
                # validation, which we ignore, trusting that it all worked
                # out earlier
                if not getattr(self, 'model', None):
                    return None

                return (
                    self.request.session.query(ExtendedDirectoryEntry)
                    .filter_by(id=self.model.meta['directory_entry'])
                    .first()
                )

            def is_different(self, field: Field) -> bool:
                # if the target has been removed, stop
                if not self.target:
                    return True

                # after the changes have been applied, use the list of changes
                if self.model.meta.get('changed'):
                    return field.id in self.model.meta['changed']

                # ignore CSRF token
                if field.id == 'csrf_token':
                    return False

                # coordinates fields are provided through extension
                if field.id == 'coordinates':
                    return field.data != self.target.coordinates

                # upload fields differ if they are not empty
                if isinstance(field, UploadField):
                    return field.data and True or False

                # like coordinates, provided through extension
                if field.id in ('publication_start', 'publication_end'):
                    if not field.data:
                        return False
                    return (
                        to_timezone(field.data, 'UTC')
                        != getattr(self.target, field.id)
                    )

                stored = self.target.values.get(field.id) or None
                field_data = field.data or None
                return stored != field_data

            def render_original(
                self,
                field: Field,
                from_model: bool = False
            ) -> Markup:

                prev = field.data

                try:
                    model = self.target
                    if model is not None:
                        field.data = (
                            model.values.get(field.id)
                            if not from_model
                            else getattr(model, field.id)
                        )
                    else:
                        field.data = None
                    return super().render_display(field)
                finally:
                    field.data = prev

            def render_display(self, field: Field) -> Markup | None:
                if self.is_different(field):
                    proposed = super().render_display(field)

                    if not self.target:
                        return proposed

                    if field.id in ('csrf_token', 'coordinates'):
                        return proposed

                    if field.id in ('publication_start', 'publication_end'):
                        original = self.render_original(field, from_model=True)
                        return render_html_diff(original, proposed)

                    if field.id not in self.target.values:
                        return proposed

                    if isinstance(field, UploadField):
                        return proposed

                    original = self.render_original(field)
                    return render_html_diff(original, proposed)
                return None

            def ensure_changes(self) -> bool | None:
                if not self.target:
                    return None

                for name, field in self._fields.items():
                    if self.is_different(field):
                        return None

                for name, field in self._fields.items():
                    if name == 'csrf_token':
                        continue
                    field.errors.append(
                        _('Please provide at least one change')
                    )

                return False

        return ChangeRequestForm


class PublicationFormExtension(FormExtension[FormT], name='publication'):
    """Can be used with TimezonePublicationMixin or UTCDateTime type decorator.
    """

    def create(self, timezone: str = 'Europe/Zurich') -> type[FormT]:
        tz = timezone

        class PublicationForm(self.form_class):  # type:ignore

            publication_start = TimezoneDateTimeField(
                label=_('Start'),
                timezone=tz,
                fieldset=_('Publication'),
                validators=[StrictOptional()]
            )

            publication_end = TimezoneDateTimeField(
                label=_('End'),
                timezone=tz,
                fieldset=_('Publication'),
                validators=[StrictOptional()]
            )

            def ensure_publication_start_end(self) -> bool | None:
                start = self.publication_start
                end = self.publication_end
                if not start or not end:
                    return None

                # Check if publication end is in the future
                if end.data and to_timezone(end.data, 'UTC') <= utcnow():
                    assert isinstance(self.publication_end.errors, list)
                    self.publication_end.errors.append(
                        _('Publication end must be in the future'))
                    return False

                # Check if start is before end
                if not start.data or not end.data:
                    return None
                if end.data <= start.data:
                    for field_name in ('publication_start', 'publication_end'):
                        field = getattr(self, field_name)
                        field.errors.append(
                            _('Publication start must be prior to end'))
                    return False

                return None

        return PublicationForm


class PushNotificationFormExtension(FormExtension[FormT], name='publish'):
    """ Assumes to be used in conjunction with PublicationFormExtension. """

    def create(self, timezone: str = 'Europe/Zurich') -> type[FormT]:

        class PublicationForm(self.form_class):  # type:ignore

            send_push_notifications_to_app = BooleanField(
                label=_('Send push notifications to app'),
                fieldset=_('Publication'),
                validators=[StrictOptional()],
                render_kw={'disabled': 'disabled'},
            )

            push_notifications = MultiCheckboxField(
                label=('Topics'),
                choices=[],
                fieldset=_('Publication'),
                depends_on=('send_push_notifications_to_app', 'y'),
                validators=[StrictOptional()],
                render_kw={'class_': 'indent-form-field'},
            )

            def on_request(self) -> None:
                # This is not an optimal solution defining this on a form
                # extension. However, this is the first of it's kind.
                # Don't forget to call super for the next one. =)
                if hasattr(super(), 'on_request'):
                    super().on_request()

                if not self.request.app.org.firebase_adminsdk_credential:
                    self.delete_field('send_push_notifications_to_app')
                    self.delete_field('push_notifications')
                    return None

                # Don't show any choices for this
                if not hasattr(self, 'send_push_notifications_to_app'):
                    return None

                default_topic = [[self.request.app.schema, 'News']]
                id_topic_pairs = self.request.app.org.meta.get(
                    'selectable_push_notification_options',
                    default_topic
                )
                # Format choices to show both ID and value
                self.push_notifications.choices = [
                    (id, f'{id} ↔ {value}') for id, value in id_topic_pairs
                ]

            def validate_send_push_notifications_to_app(
                self, field: BooleanField
            ) -> None:
                if not self.publication_start.data:
                    raise ValidationError(
                        _('You must set a publication start date first.')
                    )
                if field.data and not self.push_notifications.data:
                    raise ValidationError(
                        _('Please select at least one topic '
                          'for push notifications.'
                          )
                    )

        return PublicationForm


class HoneyPotFormExtension(FormExtension[FormT], name='honeypot'):

    def create(self) -> type[FormT]:

        class HoneyPotForm(self.form_class):  # type:ignore
            duplicate_of = HoneyPotField()

            def on_request(self) -> None:
                # This is not an optimal solution defining this on a form
                # extension.
                # Don't forget to call super for the next one. =)
                if hasattr(super(), 'on_request'):
                    super().on_request()
                if self.model and not getattr(self.model, 'honeypot', False):
                    self.delete_field('duplicate_of')

        return HoneyPotForm
