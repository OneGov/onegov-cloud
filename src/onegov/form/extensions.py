form_extensions = {}


class FormExtension(object):
    """ Enables the extension of form definitions/submissions.

    When either of those models create a form class they will take the
    'extensions' key in the meta dictionary to extend those formcode
    based forms.

    This allows for specialised behaviour of formcode forms with the drawback
    that those definitions/submissions are more tightly bound to the code. That
    is to say code in module A could not use submissions defined by module B
    unless module B is also present in the path.

    To create and register a form extension subclass as follows::

        class MyExtension(FormExtension, name='my-extension'):
            def create(self):
                return self.form_class

    Note that you *should not* change the form_class provided to you. Instead
    you should subclass it. If you need to change the form class, you need
    to clone it::

        class MyExtension(FormExtension, name='my-extension'):
            def create(self):
                return self.form_class.clone()

        class MyExtension(FormExtension, name='my-extension'):
            def create(self):
                class ExtendedForm(self.form_class):
                    pass

                return ExtendedForm

    Also, names must be unique and can only be registered once.

    """

    def __init__(self, form_class):
        self.form_class = form_class

    def __init_subclass__(cls, name, **kwargs):
        super().__init_subclass__(**kwargs)

        assert name not in form_extensions, (
            f"A form extension named {name} already exists"
        )

        form_extensions[name] = cls

    def create(self):
        raise NotImplementedError


class Extendable(object):
    """ Models extending their form classes use this mixin to create the
    extended forms. It also serves as a marker to possibly keep track of all
    classes that use extended forms.

    """

    def extend_form_class(self, form_class, extensions):
        if not extensions:
            return form_class

        for extension in extensions:
            if extension not in form_extensions:
                raise KeyError(f"Unknown form extension: {extension}")

            form_class = form_extensions[extension](form_class).create()

        return form_class
