from onegov.form.fields import MultiCheckboxField as MultiCheckboxFieldBase
from onegov.form.widgets import MultiCheckboxWidget as MultiCheckboxWidgetBase
from onegov.gazette import _


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from markupsafe import Markup


class MultiCheckboxWidget(MultiCheckboxWidgetBase):

    def __call__(
        self,
        field: 'MultiCheckboxField',  # type:ignore[override]
        **kwargs: Any
    ) -> 'Markup':
        kwargs['data-expand-title'] = field.gettext(_("Show all"))
        kwargs['data-fold-title'] = field.gettext(_("Show less"))

        return super().__call__(field, **kwargs)


class MultiCheckboxField(MultiCheckboxFieldBase):
    """ A multi checkbox field where only the first elements are display and
    the the rest can be shown when needed.

    """

    widget = MultiCheckboxWidget()

    # FIXME: Use args from superclass (could use a decorator for that)
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        render_kw = kwargs.pop('render_kw', {})
        render_kw['data-limit'] = str(kwargs.pop('limit', 5))
        kwargs['render_kw'] = render_kw

        super().__init__(*args, **kwargs)
