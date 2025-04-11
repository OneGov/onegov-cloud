from __future__ import annotations
import json
from typing import Any, get_type_hints, TYPE_CHECKING

from wtforms.fields import BooleanField
from wtforms.validators import ValidationError

from onegov.core.utils import dictionary_to_binary
from onegov.form import Form
from onegov.form.fields import UploadMultipleField
from onegov.pas import _

if TYPE_CHECKING:
    from collections.abc import Sequence
    from onegov.core.types import LaxFileDict
    from onegov.pas.importer.json_import import (
        MembershipData,
        OrganizationData,
        PersonData,
    )
    from wtforms import Field


def validate_json_structure(
    form: Form,
    field: Field,
    expected_type: type[PersonData] | type[OrganizationData] | type[MembershipData]
) -> None:
    """Validates that each item in the 'results' list of the JSON files
    contains the keys expected by the TypedDict."""
    if not field.data:
        return  # No files uploaded, nothing to validate

    required_keys = get_type_hints(expected_type).keys()
    sources: Sequence[LaxFileDict] = field.data

    for file_info in sources:
        filename = file_info.get('filename', 'unknown file')
        try:
            content_bytes = dictionary_to_binary(file_info)
            content_str = content_bytes.decode('utf-8')
            data = json.loads(content_str)

            results_list = data.get('results')
            if not isinstance(results_list, list):
                raise ValidationError(
                    _('File ${name} is missing the "results" list.',
                      mapping={'name': filename})
                )

            for index, item in enumerate(results_list):
                if not isinstance(item, dict):
                    raise ValidationError(
                        _('Item ${idx} in file ${name} is not an object.',
                          mapping={'idx': index + 1, 'name': filename})
                    )
                missing_keys = required_keys - item.keys()
                if missing_keys:
                    raise ValidationError(
                        _('Item ${idx} in file ${name} is missing keys: ${keys}',
                          mapping={
                              'idx': index + 1,
                              'name': filename,
                              'keys': ', '.join(sorted(missing_keys))
                          })
                    )
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValidationError(
                _('Error reading file ${name}: ${error}',
                  mapping={'name': filename, 'error': str(e)})
            ) from e
        except ValidationError:
            raise # Re-raise validation errors without losing context
        except Exception as e:
            # Catch unexpected errors during processing
            raise ValidationError(
                _('Unexpected error processing file ${name}: ${error}',
                  mapping={'name': filename, 'error': str(e)})
            ) from e


class DataImportForm(Form):

    clean = BooleanField(label=_('Delete data before import'), default=False)

    people_source = UploadMultipleField(
        label=_('People Data (JSON)'),
        description=_('JSON file containing parliamentarian data.'),
    )
    organizations_source = UploadMultipleField(
        label=_('Organizations Data (JSON)'),
        description=_(
            'JSON file containing organization data (commissions, '
            'parties, etc.).'
        ),
    )
    memberships_source = UploadMultipleField(
        label=_('Memberships Data (JSON)'),
        description=_(
            'JSON file containing membership data (who is member of '
            'what organization).'
        ),
    )

    def validate_people_source(self, field: UploadMultipleField) -> None:
        # Import here to avoid circular dependency at module level
        from onegov.pas.importer.json_import import PersonData
        validate_json_structure(self, field, PersonData)

    def validate_organizations_source(self, field: UploadMultipleField) -> None:
        # Import here to avoid circular dependency at module level
        from onegov.pas.importer.json_import import OrganizationData
        validate_json_structure(self, field, OrganizationData)

    def validate_memberships_source(self, field: UploadMultipleField) -> None:
        # Import here to avoid circular dependency at module level
        from onegov.pas.importer.json_import import MembershipData
        validate_json_structure(self, field, MembershipData)
