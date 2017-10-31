from onegov.core.orm.mixins import meta_property
from onegov.core.utils import linkify
from onegov.directory import Directory, DirectoryEntry
from onegov.form import as_internal_id
from onegov.org.models.extensions import CoordinatesExtension
from onegov.org.models.extensions import HiddenFromPublicExtension


class ExtendedDirectory(Directory, HiddenFromPublicExtension):
    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_directories'

    enable_map = meta_property('enable_map')


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
