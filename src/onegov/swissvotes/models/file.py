from onegov.file import AssociatedFiles
from onegov.file import File


class SwissVoteFile(File):
    """ An attachment to a vote. """

    __mapper_args__ = {'polymorphic_identity': 'swissvote'}

    @property
    def filename(self):
        return self.reference.filename


class TranslatablePageFile(File):
    """ An attachment to a translatable content page. """

    __mapper_args__ = {'polymorphic_identity': 'swissvotes_page'}

    @property
    def locale(self):
        return self.name.split('-')[0]

    @property
    def filename(self):
        return self.reference.filename


class FileSubCollection(object):
    """ """

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance:
            return sorted([
                file for file in instance.files
                if file.name.startswith(self.name)
            ], key=lambda file: file.name)


class LocalizedFile(object):
    """ A helper for localized files.

    Automatically choses the file according to the currently used locale. The
    files are internally stored as normal files using the filename to identify
    the wanted file.

    Example:

        class MyModel(Base, AssociatedFiles):
            pdf = LocalizedFile()

    """

    def __init__(self, extension, label, static_views):
        self.extension = extension
        self.label = label
        self.static_views = static_views or {}

    def __set_name__(self, owner, name):
        self.name = name

    def __get_localized_name__(self, instance, locale=None):
        return '{}-{}'.format(
            self.name,
            locale or instance.session_manager.current_locale
        )

    def __get_by_locale__(self, instance, locale=None):
        if instance:
            name = self.__get_localized_name__(instance, locale)
            for file in instance.files:
                if file.name == name:
                    return file

    def __get__(self, instance, owner):
        return self.__get_by_locale__(instance)

    def __set_by_locale__(self, instance, value, locale=None):
        if instance:
            value.name = self.__get_localized_name__(instance, locale)
            self.__delete_by_locale__(instance, locale)
            instance.files.append(value)

    def __set__(self, instance, value):
        return self.__set_by_locale__(instance, value)

    def __delete_by_locale__(self, instance, locale=None):
        if instance:
            name = self.__get_localized_name__(instance, locale)
            for file in instance.files:
                if file.name == name:
                    instance.files.remove(file)

    def __delete__(self, instance):
        self.__delete_by_locale__(instance)


class LocalizedFiles(AssociatedFiles):

    @classmethod
    def localized_files(cls):
        return {
            name: attribute
            for name, attribute in cls.__dict__.items()
            if isinstance(attribute, LocalizedFile)
        }
