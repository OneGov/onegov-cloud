from inspect import isfunction
from morepath import generic
from morepath.directive import HtmlDirective, register_view
from onegov.core.framework import Framework


@Framework.directive('form')
class HtmlHandleFormDirective(HtmlDirective):
    """ Register Form view.

    Basically wraps the Morepath's ``html`` directive, registering both
    POST and GET (if no specific request method is given) and wrapping the
    view handler with :func:`wrap_with_generic_form_handler`.

    The form is either a class or a function. If it's a function, it is
    expected to return a form class when given an instance of the model.

    Example:

    .. code-block:: python

        @App.form(model=Root, template='form.pt',
                  permission=Public, form=LoginForm)
        def handle_form(self, request, form):
            if form.submitted():
                # do something if the form was submitted with valid data
            else:
                # do something if the form was not submitted or not
                # submitted correctly

            return {}  # template variables

    """
    def __init__(self, app, model, form, render=None, template=None,
                 permission=None, internal=False, **predicates):
        self.form = form
        super(HtmlHandleFormDirective, self).__init__(app, model, render,
                                                      template, permission,
                                                      internal, **predicates)

    def perform(self, registry, obj):
        registry.install_predicates(generic.view)
        registry.register_dispatch(generic.view)

        keys = self.key_dict()

        wrapped = wrap_with_generic_form_handler(
            obj, self.form, keys.get('name'))

        if 'request_method' not in keys:

            keys['request_method'] = 'GET'
            register_view(registry, keys, wrapped,
                          self.render, self.template,
                          self.permission, self.internal)

            keys['request_method'] = 'POST'
            register_view(registry, keys, wrapped,
                          self.render, self.template,
                          self.permission, self.internal)
        else:
            register_view(registry, keys, wrapped,
                          self.render, self.template,
                          self.permission, self.internal)


def wrap_with_generic_form_handler(obj, form_class, view_name):
    """ Wraps a view handler with generic form handling.

    This includes instantiatng the form with translations/csrf protection
    and setting the correct action.

    """

    def handle_form(self, request):

        if isfunction(form_class):
            form = request.get_form(form_class(self, request))
        else:
            form = request.get_form(form_class)

        form.action = request.link(self, name=view_name)

        return obj(self, request, form)

    return handle_form
