from __future__ import annotations

from onegov.org.forms.directory import (
    DirectoryBaseForm as OrgDirectoryBaseForm)
from onegov.town6.theme import user_options


class DirectoryBaseForm(OrgDirectoryBaseForm):
    """ Form for directories. """

    @property
    def default_marker_color(self) -> str:
        return (
            (self.request.app.org.theme_options or {}).get('primary-color-ui')
            or user_options['primary-color-ui']
        )
