from morepath.directive import HtmlAction
from onegov.core.directives import HtmlHandleFormAction
from onegov.core.security import Private
from onegov.election_day.forms import EmptyForm


class ManageHtmlAction(HtmlAction):

    """ HTML directive for manage views which makes sure the permission is set
    to private.

    """

    def __init__(self, model, **kwargs):
        kwargs.pop('permission', None)
        super(ManageHtmlAction, self).__init__(
            model,
            permission=Private,
            **kwargs
        )


class ManageFormAction(HtmlHandleFormAction):

    """ HTML directive for manage forms which makes sure the permission is set
    to private. Sets a valid default for the template and form class.

    """

    def __init__(self, model, **kwargs):
        kwargs.pop('permission', None)
        template = kwargs.pop('template', 'form.pt')
        form = kwargs.pop('form', EmptyForm)
        super(ManageFormAction, self).__init__(
            model,
            template=template,
            form=form,
            permission=Private,
            **kwargs
        )
