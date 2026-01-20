from __future__ import annotations

from onegov.core.orm.abstract import associated
from onegov.file.models.file import File


class AssociatedFiles:
    """ Use this  mixin if uploaded files belong to a specific instance """

    files = associated(File, 'files', 'one-to-many', order_by='File.name')


class MultiAssociatedFiles:
    """ Use this mixin if uploaded files can belong to any number of instances
    """

    files = associated(File, 'files', 'many-to-many')
