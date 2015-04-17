from onegov.core.utils import normalize_for_url
from onegov.page.model import Page
from onegov.page import utils


class PageCollection(object):
    """ Manages a hierarchy of pages.

    Use it like this:

        from onegov.page import PageCollection
        pages = PageCollection(session)

    """

    def __init__(self, session):
        self.session = session

    def query(self):
        """ Returns a query using :class:`onegov.page.model.Page`. """
        return self.session.query(Page)

    def by_id(self, page_id):
        """ Takes the given page id and returns the page. Try to keep this
        id away from the public. It's not a security problem if it leaks, but
        it's not something the public can necessarly count on.

        If possible use the path instead.

        """
        return self.query().filter(Page.id == page_id).first()

    def by_path(self, path):
        """ Takes a path and returns the page associated with it.

        For example, given this hierarchy::

            Page(name='documents', id=0, parent_id=None)
                Page(name='readme', id=1, parent_id=0)
                Page(name='license', id=2, parent_id=0)

        The following query would return the Page with the name 'license'::

            paths.by_path('documents/license')

        Slashes at the beginning or end are ignored, so the above is equal to::

            paths.by_path('/documents/license')
            paths.by_path('/documents/license/')
            paths.by_path('documents/license/')

        Lookups by path are currently quite wasteful. To get the root of
        a page nested deeply one has to walk the ascendants of the page one by
        one, triggering a number of queries.

        Should this actually become a bottleneck (it might be fine), we should
        probably implement a materialized view that is updated whenever a page
        changes.

        See:

        `<http://schinckel.net/2014/11/22/\
        postgres-tree-shootout-part-1%3A-introduction./>`

        `<http://schinckel.net/2014/11/27/\
        postgres-tree-shootout-part-2%3A-adjacency-list-using-ctes/>`

        """

        fragments = path.strip('/').split('/')

        page = self.query().filter(
            Page.name == fragments.pop(0),
            Page.parent_id == None
        ).first()

        while page and fragments:
            page = self.query().filter(
                Page.name == fragments.pop(0),
                Page.parent_id == page.id
            ).first()

        return page

    def get_unique_child_name(self, name, parent):
        """ Takes the given name or title, normalizes it and makes sure
        that it's unique among the siblings of the page.

        This is achieved by adding numbers at the end if there are overlaps.

        For example, ``root`` becomes ``root-1`` if ``root`` exists. ``root-2``
        if ``root-1`` exists and so on.

        """
        name = normalize_for_url(name)

        siblings = self.query().filter(Page.parent == parent)
        names = set(s[0] for s in siblings.with_entities(Page.name).all())

        while name in names:
            name = utils.increment_name(name)

        return name

    def add_root(self, title, meta=None, content=None, name=None):
        return self.add(None, title, meta, content, name)

    def add(self, parent, title, meta=None, content=None, name=None):
        """ Adds a page to the given parent. """

        name = name or self.get_unique_child_name(title, parent)

        page = Page(
            parent=parent,
            title=title,
            meta=meta,
            content=content,
            name=name
        )

        self.session.add(page)
        self.session.flush()

        return page

    def add_or_get_root(self, title, meta=None, content=None, name=None):
        return self.add_or_get(None, title, meta, content, name)

    def add_or_get(self, parent, title, meta=None, content=None, name=None):
        """ Adds a page to the given parent. If a page with the same name
        already exists the existing page is returned.

        If no name is given, the name is derived from the title.

        """

        name = name or normalize_for_url(title)

        query = self.query().filter(Page.parent == parent)
        query = query.filter(Page.name == name)

        page = query.first()

        if page:
            return page
        else:
            return self.add(parent, title, meta, content, name)

    def delete(self, page):
        """ Deletes the given page and *all* it's desecendants!. """
        self.session.delete(page)
        self.session.flush()

    def move(self, page, new_parent):
        """ Takes the given page and moves it under the new_parent. """
        page.parent = new_parent
        self.session.flush()

    def copy(self, page, parent):
        """ Takes the given page and copies it to a given parent.

        The parent may be the same as the given page or another. If there's
        a conflict with existing children, the name is adjusted using
        :meth:`get_unique_child_name`.

        """
        return self.add(parent, page.title, page.meta, page.content)
