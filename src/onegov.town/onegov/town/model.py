""" Contains the models directly provided by onegov.town. """

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.town.theme import user_colors
from sqlalchemy import Column, Text
from uuid import uuid4


class Town(Base, TimestampMixin):
    """ Defines the basic information associated with a town.

    It is assumed that there's only one town record in the schema associated
    with this town.
    """

    __tablename__ = 'towns'

    #: the id of the town, an automatically generated uuid
    id = Column(UUID, nullable=False, primary_key=True, default=uuid4)

    #: the name of the town (as registered with the Swiss governement)
    name = Column(Text, nullable=False)

    #: the logo of the town
    logo_url = Column(Text, nullable=True)

    #: the theme options of the town
    theme_options = Column(JSON, nullable=True, default=user_colors.copy)


class ImageCollection(object):
    """ Defines the collection of images uploaded to the site. Currently
    this is done without any ORM backing (and therefore without any
    special features like tagging, metadata and so on).

    Instead it's simply a list of images in a directory.

    This can be made more powerful (and complicated) once we have sufficent
    time to do it.

    """

    def __init__(self, app):
        assert app.has_filestorage

        self.path_prefix = 'images/'
        self.filestorage = app.filestorage.makeopendir('images')


class Editor(object):
    """ Defines the model for the page editor. Required because pages need
    to be edited outside their url structure, since their urls are absorbed
    completely and turned into SQL queries.

    """
    def __init__(self, action, page):
        """ The editor is defined by an action and a page/context.

        :action:
            One of 'new', 'edit' or 'delete'.

        :page:
            The 'context' of the action. The actual page in the case of 'edit'
            and 'delete'. The parent in the case of 'new'.

        """

        self.action = action
        self.page = page

    @property
    def page_id(self):
        return self.page.id


class PageEditor(Editor):
    """ Editor for the page type "page". """
    pass


class LinkEditor(Editor):
    """ Editor for the page type "link". """
    pass
