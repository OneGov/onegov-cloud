from onegov.core.crypto import random_token
from onegov.file.models.file import File
from onegov.file.utils import as_fileintent


class NamedFile:

    """ Helper for managing files using static names together with
    AssociatedFiles.

    A named file can be added by assigning a tuple of a file-like content and
    a filename. Reading the named file will return a File object. Finally,
    named files can be deleted using the del-Operator.

    Example:

        class MyClass(AssociatedFiles):
            pdf = NamedFile()

        obj = MyClass()
        with open('some.pdf', 'rb') as file:
            obj.pdf = (file.read(), 'some.pdf')
        obj.pdf.reference.file.read()
        del obj.pdf

    """

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance:
            for file in instance.files:
                if file.name == self.name:
                    return file

    def __set__(self, instance, value):
        if instance:
            content, filename = value
            self.__delete__(instance)
            file = File(id=random_token())
            file.name = self.name
            file.reference = as_fileintent(content, filename)
            instance.files.append(file)

    def __delete__(self, instance):
        if instance:
            for file in tuple(instance.files):
                if file.name == self.name:
                    instance.files.remove(file)
