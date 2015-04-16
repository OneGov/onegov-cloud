""" Contains small helper classes used as abstraction for various templating
macros.

"""


class Link(object):
    """ Represents a link rendered in a template. """

    def __init__(self, text, url, active=False):
        #: The text of the link
        self.text = text

        #: The fully qualified url of the link
        self.url = url

        #: True if the link is active (sometimes used for the navigation)
        self.active = active


class Image(object):
    """ Represents an img element. """

    def __init__(self, src, alt=None, title=None):
        #: The src of the image
        self.src = src

        #: The text for people that can't or won't look at the picture
        self.alt = alt

        #: The title of the image
        self.title = title
