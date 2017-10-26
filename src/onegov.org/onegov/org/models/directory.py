from onegov.core.utils import linkify
from onegov.directory import Directory, DirectoryEntry
from onegov.form import as_internal_id
from onegov.org.models.extensions import HiddenFromPublicExtension
from onegov.org.models.extensions import CoordinatesExtension


class ExtendedDirectory(Directory, HiddenFromPublicExtension):
    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_directories'


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

            return '<ul>{}</ul>'.format(
                ''.join(
                    '<li>{}</li>'.format(linkify(value))
                    for value in values if value
                )
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
