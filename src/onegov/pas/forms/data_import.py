from __future__ import annotations

import json
from onegov.core.utils import dictionary_to_binary
from onegov.form import Form
from onegov.form.fields import UploadMultipleField
from onegov.pas import _
from onegov.pas.importer.json_import import (
    MembershipData,
    OrganizationData,
    PersonData
)
from wtforms.fields import BooleanField


from typing import get_type_hints, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from onegov.core.types import LaxFileDict


class DataImportForm(Form):

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

    validate_schema = BooleanField(
        label=_('Validate JSON Schema'),
        description=_(
            'Check if the uploaded JSON files match the expected structure.'
        ),
        default=True,
    )

    def validate_people_source(self, field: UploadMultipleField) -> None:
        if self.validate_schema.data:
            self._validate_json_results_against_type(
                field, PersonData
            )

    def validate_organizations_source(
            self, field: UploadMultipleField
    ) -> None:
        if self.validate_schema.data:
            self._validate_json_results_against_type(
                field, OrganizationData
            )

    def validate_memberships_source(self, field: UploadMultipleField) -> None:
        if self.validate_schema.data:
            self._validate_json_results_against_type(
                field, MembershipData
            )

    def _validate_json_results_against_type(
        self,
        field: UploadMultipleField,
        expected_type: type[PersonData | OrganizationData | MembershipData]
    ) -> None:
        """Validates that each item in the 'results' list of the JSON files
        contains the keys expected by the TypedDict."""
        # Import here to avoid circular dependency at module level
        if not field.data:
            return  # No files uploaded, nothing to validate

        required_keys = get_type_hints(expected_type).keys()
        sources: Sequence[LaxFileDict] = field.data

        for file_info in sources:
            filename = file_info.get('filename', 'unknown file')
            try:
                data = json.loads(
                    dictionary_to_binary(file_info).decode('utf-8')
                )
                results_list = data.get('results')

                if not isinstance(results_list, list):
                    field.errors.append(  # type: ignore[attr-defined]
                        _('File ${name} is missing the "results" list.',
                          mapping={'name': filename})
                    )
                    return

                for index, item in enumerate(results_list):
                    if not isinstance(item, dict):
                        field.errors.append(  # type: ignore[attr-defined]
                            _('Item ${idx} in file ${name} is not an object.',
                              mapping={'idx': index + 1, 'name': filename})
                        )
                        return

                    missing_keys = required_keys - item.keys()
                    if missing_keys:
                        field.errors.append(  # type: ignore[attr-defined]
                            _('Item ${idx} in ${name} is missing keys ${keys}',
                              mapping={
                                  'idx': index + 1,
                                  'name': filename,
                                  'keys': ', '.join(sorted(missing_keys))
                              })
                        )
                        return

            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                field.errors.append(  # type: ignore[attr-defined]
                    _('Error reading file ${name}: ${error}',
                      mapping={'name': filename, 'error': str(e)})
                )
                return
            except Exception as e:
                field.errors.append(  # type: ignore[attr-defined]
                    _('Unexpected error processing file ${name}: ${error}',
                      mapping={'name': filename, 'error': str(e)})
                )
                return
