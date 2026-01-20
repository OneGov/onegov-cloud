from __future__ import annotations

from onegov.file import File
from operator import attrgetter


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import SessionManager
    from onegov.swissvotes.models import SwissVote
    from onegov.swissvotes.models import TranslatablePage
    from sqlalchemy.orm import relationship
    from typing import Protocol
    from typing import TypeVar

    FileT = TypeVar('FileT', bound=File)

    class HasFiles(Protocol[FileT]):
        files: list[FileT]

    class HasFilesAndSessionManager(HasFiles[FileT], Protocol):
        @property
        def session_manager(self) -> SessionManager | None: ...


class SwissVoteFile(File):
    """ An attachment to a vote. """

    __mapper_args__ = {'polymorphic_identity': 'swissvote'}

    if TYPE_CHECKING:
        # backrefs created through associated
        linked_swissvotes: relationship[list[SwissVote]]

    @property
    def locale(self) -> str:
        return self.name.split('-')[1]

    @property
    def filename(self) -> str:
        return self.reference.filename


class TranslatablePageFile(File):
    """ An attachment to a translatable content page. """

    __mapper_args__ = {'polymorphic_identity': 'swissvotes_page'}

    if TYPE_CHECKING:
        # backrefs created through associated
        linked_swissvotes_page: relationship[list[TranslatablePage]]

    @property
    def locale(self) -> str:
        return self.name.split('-')[0]

    @property
    def filename(self) -> str:
        return self.reference.filename


class FileSubCollection:
    """ A subset of files prefixed by the descriptor's name. """

    def __set_name__(self, owner: type[object], name: str) -> None:
        self.name = name

    def __get__(
        self,
        instance: HasFiles[FileT] | None,
        owner: type[object]
    ) -> list[FileT]:

        if instance:
            return sorted((
                file for file in instance.files
                if file.name.startswith(self.name)
            ), key=attrgetter('name'))
        return []


class LocalizedFile:
    """ A helper for localized files.

    Automatically choses the file according to the currently used locale. The
    files are internally stored as normal files using the filename to identify
    the wanted file.

    Example:

        class MyModel(Base, AssociatedFiles):
            pdf = LocalizedFile()

    """

    def __init__(
        self,
        extension: str,
        label: str,
        static_views: dict[str, str]
    ) -> None:

        self.extension = extension
        self.label = label
        self.static_views = static_views or {}

    def __set_name__(self, owner: type[object], name: str) -> None:
        self.name = name

    def __get_localized_name__(
        self,
        instance: HasFilesAndSessionManager[FileT],
        locale: str | None = None
    ) -> str:

        if not locale:
            assert instance.session_manager is not None
            locale = instance.session_manager.current_locale
        return f'{self.name}-{locale}'

    def __get_by_locale__(
        self,
        instance: HasFilesAndSessionManager[FileT] | None,
        locale: str | None = None
    ) -> FileT | None:

        if instance:
            name = self.__get_localized_name__(instance, locale)
            file: FileT
            for file in instance.files:
                if file.name == name:
                    return file
        return None

    def __get__(
        self,
        instance: HasFilesAndSessionManager[FileT] | None,
        owner: type[object]
    ) -> FileT | None:
        return self.__get_by_locale__(instance)

    def __set_by_locale__(
        self,
        instance: HasFilesAndSessionManager[FileT],
        value: FileT,
        locale: str | None = None
    ) -> None:

        value.name = self.__get_localized_name__(instance, locale)
        self.__delete_by_locale__(instance, locale)
        instance.files.append(value)

    def __set__(
        self,
        instance: HasFilesAndSessionManager[FileT],
        value: FileT
    ) -> None:

        return self.__set_by_locale__(instance, value)

    def __delete_by_locale__(
        self,
        instance: HasFilesAndSessionManager[FileT],
        locale: str | None = None
    ) -> None:

        name = self.__get_localized_name__(instance, locale)
        # create a copy of the list since we remove elements
        for file in tuple(instance.files):
            if file.name == name:
                instance.files.remove(file)

    def __delete__(self, instance: HasFilesAndSessionManager[FileT]) -> None:
        self.__delete_by_locale__(instance)


class LocalizedFiles:

    @classmethod
    def localized_files(cls) -> dict[str, LocalizedFile]:
        return {
            name: attribute
            for name, attribute in cls.__dict__.items()
            if isinstance(attribute, LocalizedFile)
        }
