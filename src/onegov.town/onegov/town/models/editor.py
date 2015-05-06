""" Contains the model describing the page editor. """


class Editor(object):
    """ Defines the model for the page editor. Required because pages need
    to be edited outside their url structure, since their urls are absorbed
    completely and turned into SQL queries.

    """
    def __init__(self, action, page, page_type=None):
        """ The editor is defined by an action and a page/context.

        :action:
            One of 'new', 'edit' or 'delete'.

        :page:
            The 'context' of the action. The actual page in the case of 'edit'
            and 'delete'. The parent in the case of 'new'.

        :page_type:
            The type of the page. Only necessary in the case of 'new'.

        """

        self.action = action
        self.page = page

        if self.action == 'new':
            self.page_type = page_type
        else:
            self.page_type = page.type

    @property
    def page_id(self):
        return self.page.id
