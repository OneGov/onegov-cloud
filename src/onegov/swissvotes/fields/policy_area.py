from __future__ import annotations

from copy import deepcopy
from json import dumps
from onegov.swissvotes import _
from onegov.swissvotes.models import PolicyArea
from wtforms.fields import SelectMultipleField
from wtforms.widgets import Select


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from onegov.form.types import FormT
    from onegov.form.types import Filter
    from onegov.form.types import PricingRules
    from onegov.form.types import Validators
    from onegov.form.types import Widget
    from typing import NotRequired
    from typing import Self
    from typing import TypedDict
    from markupsafe import Markup
    from wtforms.fields.choices import SelectFieldBase
    from wtforms.form import BaseForm
    from wtforms.meta import _SupportsGettextAndNgettext
    from wtforms.meta import DefaultMeta

    class PolicyAreaTreeNode(TypedDict):
        value: str
        label: str
        children: list[PolicyAreaTreeNode]
        # NOTE: Technically these are guaranteed to be set when read out
        #       and don't ever need to be provided manually, but it's easier
        #       to just treat them as not required for now, since we just
        #       json.dumps them anyway
        expanded: NotRequired[bool]
        checked: NotRequired[bool]


class PolicyAreaWidget(Select):
    """ The widget for the React Dropdown Tree. """

    def __call__(
        self,
        field: PolicyAreaField,  # type:ignore[override]
        **kwargs: object
    ) -> Markup:

        kwargs['class_'] = 'policy-selector'
        kwargs['data-tree'] = dumps(field.tree)
        kwargs['data-placehoder-text'] = field.gettext(
            _('Select Some Options')
        )
        kwargs['data-no-matches-text'] = field.gettext(_('No results match'))
        return super().__call__(field, **kwargs)

    @classmethod
    def render_option(
        cls,
        value: str,  # type:ignore[override]
        label: str,
        selected: bool,
        **kwargs: object
    ) -> Markup:
        """ Adds a level specific class to each option.

        This allows to see the hierarchy in case the client has disabled
        javascript.

        """
        kwargs['class'] = f'level-{PolicyArea(value).level}'
        return super().render_option(value, label, selected, **kwargs)


class PolicyAreaField(SelectMultipleField):
    """ A select field with React Dropdown Tree support. """

    data: list[str] | None
    choices: list[tuple[str, str]]  # type:ignore[assignment]

    widget = PolicyAreaWidget(multiple=True)

    if TYPE_CHECKING:
        def __init__(
            self,
            label: str | None = None,
            validators: Validators[FormT, Self] | None = None,
            *,
            tree: list[PolicyAreaTreeNode] = ...,
            filters: Sequence[Filter] = (),
            description: str = '',
            id: str | None = None,
            default: object | None = None,
            widget: Widget[Self] | None = None,
            option_widget: Widget[SelectFieldBase._Option] | None = None,
            render_kw: dict[str, Any] | None = None,
            name: str | None = None,
            _form: BaseForm | None = None,
            _prefix: str = '',
            _translations: _SupportsGettextAndNgettext | None = None,
            _meta: DefaultMeta | None = None,
            # onegov specific kwargs that get popped off
            fieldset: str | None = None,
            depends_on: Sequence[Any] | None = None,
            pricing: PricingRules | None = None,
        ) -> None: ...
    else:
        def __init__(self, *args, **kwargs):
            self.tree = kwargs.pop('tree', [])
            super().__init__(*args, **kwargs)

    @property
    def tree(self) -> list[PolicyAreaTreeNode]:
        """ Returns the tree data and automatically preselects the selected
        select options.

        """
        tree = deepcopy(self._tree)

        def preselect(item: PolicyAreaTreeNode) -> bool:
            checked = item['value'] in (self.data or ())
            expanded = False
            for child in item['children']:
                expanded = True if preselect(child) else expanded
            item['checked'] = checked
            item['expanded'] = expanded
            return expanded or checked

        for item in tree:
            preselect(item)

        return tree

    @tree.setter
    def tree(self, value: list[PolicyAreaTreeNode]) -> None:
        """ Sets the tree data and automatically populates the select's
        choices.

        """
        self._tree = value

        def add_choices(item: PolicyAreaTreeNode) -> None:
            self.choices.append((item['value'], item['label']))
            for child in item['children']:
                add_choices(child)

        self.choices = []
        for item in value:
            add_choices(item)
