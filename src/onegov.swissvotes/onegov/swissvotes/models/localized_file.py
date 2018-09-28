class LocalizedFile(object):
    """ A helper for localized files.

    Automatically choses the file according to the currently used locale. The
    files are internally stored as normal files using the filename to identify
    the wanted file.

    Example:

        class MyModel(Base, AssociatedFiles):
            pdf = LocalizedFile()

    """

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
