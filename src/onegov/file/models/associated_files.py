from onegov.core.orm.abstract import associated
from onegov.file.models.file import File


class AssociatedFiles:

    files = associated(File, 'files', 'one-to-many')
