from __future__ import annotations

from onegov.core.crypto import random_token
from onegov.file.models.file import File
from onegov.file.utils import as_fileintent


from typing import overload, IO, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Protocol
    from typing import Self

    class HasFiles(Protocol):
        files: list[File]


_F = TypeVar('_F', bound=File)


class NamedFile:

    """ Helper for managing files using static names together with
    AssociatedFiles.

    A named file can be added by assigning a tuple of a file-like content and
    a filename. Reading the named file will return a File object. Finally,
    named files can be deleted using the del-Operator.

    Example::

        class MyClass(AssociatedFiles):
            pdf = NamedFile()

        obj = MyClass()
        with open('some.pdf', 'rb') as file:
            obj.pdf = (file.read(), 'some.pdf')
        obj.pdf.reference.file.read()
        del obj.pdf

    """

    def __init__(self, cls: type[_F] | None = None):
        self.cls = cls or File

    def __set_name__(self, owner: type[object], name: str) -> None:
        self.name = name

    @overload
    def __get__(
        self,
        instance: None,
        owner: type[object] | None = None
    ) -> Self: ...

    @overload
    def __get__(
        self,
        instance: HasFiles,
        owner: type[object] | None = None
    ) -> File | None: ...

    def __get__(
        self,
        instance: HasFiles | None,
        owner: type[object] | None = None
    ) -> Self | File | None:

        if instance is None:
            return None

        file: File
        for file in instance.files:
            if file.name == self.name:
                return file

        return None

    def __set__(
        self,
        instance: HasFiles,
        value: tuple[bytes | IO[bytes], str | None]
    ) -> None:

        content, filename = value
        self.__delete__(instance)
        file = self.cls(id=random_token())
        file.name = self.name
        file.reference = as_fileintent(content, filename)
        instance.files.append(file)

    def __delete__(self, instance: HasFiles) -> None:
        for file in tuple(instance.files):
            if file.name == self.name:
                instance.files.remove(file)
