from copy import deepcopy
from json import dumps
from onegov.swissvotes import _
from onegov.swissvotes.models import PolicyArea
from wtforms import SelectMultipleField
from wtforms.widgets import Select


class PolicyAreaWidget(Select):
    """ The widget for the React Dropdown Tree. """

    def __call__(self, field, **kwargs):
        kwargs['class_'] = 'policy-selector'
        kwargs['data-tree'] = dumps(field.tree)
        kwargs['data-placehoder-text'] = field.gettext(
            _("Select Some Options")
        )
        kwargs['data-no-matches-text'] = field.gettext(_("No results match"))
        return super().__call__(field, **kwargs)

    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        """ Adds a level specific class to each option.

        This allows to see the hierarchie in case the client has disabled
        javascript.

        """
        kwargs['class'] = 'level-{}'.format(PolicyArea(value).level)
        return super(PolicyAreaWidget, cls).render_option(
            value, label, selected, **kwargs
        )


class PolicyAreaField(SelectMultipleField):
    """ A select field with React Dropdown Tree support. """

    widget = PolicyAreaWidget(multiple=True)

    def __init__(self, *args, **kwargs):
        self.tree = kwargs.pop('tree', [])
        super().__init__(*args, **kwargs)

    @property
    def tree(self):
        """ Returns the tree data and automatically preselects the selected
        select options.

        """

        tree = deepcopy(self._tree)

        def preselect(item):
            checked = item['value'] in self.data
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
    def tree(self, value):
        """ Sets the tree data and automatically populates the select's
        choices.

        """
        self._tree = value

        def add_choices(item):
            self.choices.append((item['value'], item['label']))
            for child in item['children']:
                add_choices(child)

        self.choices = []
        for item in value:
            add_choices(item)
