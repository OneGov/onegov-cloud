from __future__ import annotations

from cgi import FieldStorage
from io import BytesIO

from markupsafe import Markup
from wtforms import EmailField, TextAreaField

from onegov.agency import _
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.models import ExtendedAgency
from onegov.agency.utils import handle_empty_p_tags
from onegov.core.security import Private
from onegov.core.utils import linkify, ensure_scheme
from onegov.form import Form
from onegov.form.fields import ChosenSelectField, HtmlField
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit, MIME_TYPES_IMAGE
from onegov.gis import CoordinatesField
from sqlalchemy import func
from wtforms.fields import StringField
from wtforms.validators import InputRequired


from typing import cast
from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webob.request import _FieldStorageWithFile


class ExtendedAgencyForm(Form):
    """ Form to edit agencies. """

    title = StringField(
        label=_('Title'),
        validators=[
            InputRequired()
        ],
    )

    portrait = HtmlField(
        label=_('Portrait'),
        render_kw={'rows': 10}
    )

    location_address = TextAreaField(
        label=_('Location address'),
        render_kw={'rows': 2},
    )
    location_code_city = StringField(
        label=_('Location Code and City')
    )

    postal_address = TextAreaField(
        label=_('Postal address'),
        render_kw={'rows': 2},
    )
    postal_code_city = StringField(label=_('Postal Code and City'))

    phone = StringField(label=_('Phone'))
    phone_direct = StringField(label=_('Alternate Phone Number / Fax'))
    email = EmailField(label=_('E-Mail'))
    website = StringField(label=_('Website'), filters=(ensure_scheme, ))

    opening_hours = TextAreaField(
        label=_('Opening hours'),
        render_kw={'rows': 5},
    )

    organigram = UploadField(
        label=_('Organigram'),
        validators=[
            FileSizeLimit(1 * 1024 * 1024)
        ],
        allowed_mimetypes=MIME_TYPES_IMAGE,
    )

    coordinates = CoordinatesField(
        label=_('Location'),
        description=_(
            'Search for the exact address to set a marker. The zoom of '
            'the map will be saved as well.'
        ),
        fieldset=_('Map'),
        render_kw={'data-map-type': 'marker'},
    )

    export_fields = MultiCheckboxField(
        label=_('Fields to include for each membership'),
        choices=[
            ('membership.title', _('Membership: Title')),
            ('membership.since', _('Membership: Since')),
            ('membership.addition', _('Membership: Addition')),
            ('person.title', _('Person: Title')),
            ('person.function', _('Person: Function')),
            ('person.last_name', _('Person: Last Name')),
            ('person.first_name', _('Person: First Name')),
            ('person.born', _('Person: Born')),
            ('person.academic_title', _('Person: Academic Title')),
            ('person.profession', _('Person: Profession')),
            ('person.location_address', _('Person: Location address')),
            ('person.location_code_city', _('Person: Location Code and City')),
            ('person.postal_address', _('Person: Postal address')),
            ('person.postal_code_city', _('Person: Postal Code and City')),
            ('person.political_party', _('Person: Political Party')),
            ('person.parliamentary_group', _('Person: Parliamentary Group')),
            ('person.phone', _('Person: Phone')),
            ('person.phone_direct', _('Person: Direct Phone')),
        ],
        default=['membership.title', 'person.title'],
        fieldset=_('PDF Export'),
        render_kw={'class_': 'sortable-multi-checkbox'}
    )

    def on_request(self) -> None:
        self.request.include('sortable-multi-checkbox')

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data(exclude={'csrf_token', 'organigram'})
        if self.organigram.data:
            result['organigram_file'] = self.organigram.file
        if self.portrait.data:
            result['portrait'] = linkify(self.portrait.data)
        return result

    def update_model(self, model: ExtendedAgency) -> None:
        assert self.title.data is not None
        model.title = self.title.data
        model.portrait = handle_empty_p_tags(linkify(self.portrait.data))
        model.location_address = self.location_address.data
        model.location_code_city = self.location_code_city.data
        model.postal_address = self.postal_address.data
        model.postal_code_city = self.postal_code_city.data
        model.phone = self.phone.data
        model.phone_direct = self.phone_direct.data
        model.email = self.email.data
        model.website = self.website.data
        model.opening_hours = self.opening_hours.data
        model.export_fields = self.export_fields.data or []
        if self.organigram.action == 'delete':
            del model.organigram
        elif self.organigram.action == 'replace' and self.organigram.data:
            model.organigram_file = self.organigram.file  # type:ignore
        model.coordinates = self.coordinates.data
        if hasattr(self, 'access'):
            model.access = self.access.data
        if hasattr(self, 'publication_start'):
            model.publication_start = self.publication_start.data
        if hasattr(self, 'publication_end'):
            model.publication_end = self.publication_end.data

    def reorder_export_fields(self) -> None:
        titles: dict[str, str] = dict(
            self.export_fields.choices  # type:ignore[arg-type]
        )
        chosen = self.export_fields.data or []
        self.export_fields.choices = [
            (choice, titles[choice]) for choice in chosen
        ] + [
            choice for choice in self.export_fields.choices
            if choice[0] not in chosen
        ]

    def apply_model(self, model: ExtendedAgency) -> None:
        self.title.data = model.title
        self.portrait.data = model.portrait or Markup('')
        self.location_address.data = model.location_address
        self.location_code_city.data = model.location_code_city
        self.postal_address.data = model.postal_address
        self.postal_code_city.data = model.postal_code_city
        self.phone.data = model.phone
        self.phone_direct.data = model.phone_direct
        self.email.data = model.email
        self.website.data = model.website
        self.opening_hours.data = model.opening_hours
        self.export_fields.data = model.export_fields
        if model.organigram_file:
            fs = cast('_FieldStorageWithFile', FieldStorage())
            fs.file = BytesIO(model.organigram_file.read())
            fs.type = model.organigram_file.content_type
            fs.filename = model.organigram_file.filename
            self.organigram.data = self.organigram.process_fieldstorage(fs)
        self.coordinates.data = model.coordinates
        if hasattr(self, 'access'):
            self.access.data = model.access
        if hasattr(self, 'publication_start'):
            self.publication_start.process_data(model.publication_start)
        if hasattr(self, 'publication_end'):
            self.publication_end.process_data(model.publication_end)

        self.reorder_export_fields()


class MoveAgencyForm(Form):
    """ Form to move an agency. """

    parent_id = ChosenSelectField(
        label=_('Destination'),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    def on_request(self) -> None:
        self.request.include('common')
        self.request.include('chosen')

        agencies = ExtendedAgencyCollection(self.request.session)
        self.parent_id.choices = [
            (str(agency.id), agency.title)
            for agency in agencies.query().order_by(None).order_by(
                func.unaccent(ExtendedAgency.title)
            )
            if self.request.has_permission(agency, Private)
        ]
        if self.request.has_permission(agencies, Private):
            self.parent_id.choices.insert(
                0, ('root', self.request.translate(_('- Root -')))
            )

    def ensure_valid_parent(self) -> bool:
        """
        As a new destination (parent page) every menu item is valid except
        yourself. You cannot assign yourself as the new destination
        :return: bool
        """
        if self.parent_id.data and self.parent_id.data.isdigit():
            new_parent_id = int(self.parent_id.data)
            # prevent selecting yourself as new parent
            if self.model.id == new_parent_id:
                assert isinstance(self.parent_id.errors, list)
                self.parent_id.errors.append(
                    _('Invalid destination selected'))
                return False

        return True

    def update_model(self, model: ExtendedAgency) -> None:
        session = self.request.session
        agencies = ExtendedAgencyCollection(session)

        new_parent_id = None
        new_parent = None
        if self.parent_id.data and self.parent_id.data.isdigit():
            new_parent_id = int(self.parent_id.data)
            new_parent = agencies.by_id(new_parent_id)

        model.name = agencies.get_unique_child_name(model.title, new_parent)
        model.parent_id = new_parent_id

    def apply_model(self, model: ExtendedAgency) -> None:
        def remove(item: ExtendedAgency) -> None:
            choice = (str(item.id), item.title)
            if choice in self.parent_id.choices:
                assert isinstance(self.parent_id.choices, list)
                self.parent_id.choices.remove(choice)

        def remove_with_children(item: ExtendedAgency) -> None:
            remove(item)
            for child in item.children:
                remove_with_children(child)

        if model.parent:
            remove(model.parent)
        else:
            assert isinstance(self.parent_id.choices, list)
            self.parent_id.choices.pop(0)
        remove_with_children(model)
