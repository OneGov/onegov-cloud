""" Contains the model describing the page editor. """


class Editor(object):
    """ Defines the model for the page editor. Required because pages need
    to be edited outside their url structure, since their urls are absorbed
    completely and turned into SQL queries.

    """
    def __init__(self, action, page, trait=None):
        """ The editor is defined by an action and a page/context.

        :action:
            One of 'new', 'edit' or 'delete'.

        :page:
            The 'context' of the action. The actual page in the case of 'edit'
            and 'delete'. The parent in the case of 'new' or 'paste'.

            New pages inherit the type from the parent.

        :trait:
            The trait of the page. Currently either 'link' or 'page'.
            Only necessary if it's a new page. The trait controls the content
            of the page and leads to different forms.

            See :module:`onegov.org.models.page`.

        """

        assert self.is_supported_action(action)

        self.action = action
        self.page = page
        self.trait = action == 'new' and trait or page.trait

    @staticmethod
    def is_supported_action(action):
        """ Returns True if the given action is supported. """
        return action in {'new', 'paste', 'edit', 'delete'}

    @property
    def page_id(self):
        """ Returns the page id so morepath can create a link to this. """
        return self.page.id
