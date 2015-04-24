from wtforms import Form as BaseForm


class Form(BaseForm):
    """ Extends wtforms.Form with useful methods and integrations needed in
    OneGov applications.

    """

    def submitted(self, request):
        """ Returns true if the given request is a successful post request. """
        return request.POST and self.validate()


def with_options(widget_class, **render_options):
    """ Takes a widget class and returns a child-instance of the widget class,
    with the given options set on the render call.

    This makes it easy to use existing WTForms widgets with custom render
    options:

    field = StringField(widget=with_options(TextArea, class_="markdown"))

    """

    class Widget(widget_class):

        def __call__(self, *args, **kwargs):
            render_options.update(kwargs)
            return super(Widget, self).__call__(*args, **render_options)

    return Widget()
