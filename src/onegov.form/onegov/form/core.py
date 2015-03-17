from wtforms import Form as BaseForm


class Form(BaseForm):
    """ Extends wtforms.Form with useful methods and integrations needed in
    OneGov applications.

    """

    def submitted(self, request):
        """ Returns true if the given request is a successful post request. """
        return request.POST and self.validate()
