from onegov.winterthur.app import WinterthurApp
from onegov.directory import DirectoryEntry, DirectoryEntryCollection
from onegov.core.templates import render_macro


@WinterthurApp.directory_search_widget('hierarchical')
class HierarchicalSearch(object):

    def __init__(self, app, directory, search_query):
        self.app = app
        self.directory = directory
        self.search_query = search_query

    @property
    def path(self):
        return self.search_query and self.search_query.get('path', '') or ''

    @path.setter
    def path(self, value):
        self.search_query['path'] = value

    @property
    def current_level(self):
        current = 0 if not self.path else self.path.count('/') + 1
        return min(self.max_level, current)

    @property
    def max_level(self):
        return max(len(items) - 1 for items in self.app.hierarchy)

    @property
    def parent_name(self):
        if not self.path:
            return None

        if '/' not in self.path:
            return self.path

        return self.path.split('/')[-1]

    def parent_link(self, request):

        if not self.path:
            return None

        if '/' not in self.path:
            search_query = None

        else:
            search_query = {
                'path': '/'.join(
                    p for ix, p in enumerate(self.path.split('/'))
                    if ix < (self.current_level - 1)
                )
            }

        return request.class_link(
            DirectoryEntryCollection,
            variables={
                'directory_name': self.directory.name,
                'search': self.name,
                'search_query': search_query
            }
        )

    def children(self):
        level = self.current_level

        return {
            i[level] for i in self.app.hierarchy
            if not self.path or '/'.join(i).startswith(self.path)
        }

    def child_path(self, child):
        return self.path and '/'.join((self.path, child)) or child

    def child_link(self, request, child):
        if self.current_level == self.max_level:
            return None

        return request.class_link(
            DirectoryEntryCollection,
            variables={
                'directory_name': self.directory.name,
                'search': self.name,
                'search_query': {'path': self.child_path(child)}
            }
        )

    def html(self, layout):
        return render_macro(
            macro=layout.macros['hierarchical_search'],
            request=layout.request,
            content={
                'parent_name': self.parent_name,
                'parent_link': self.parent_link(layout.request),
                'children': sorted([
                    (child, self.child_link(layout.request, child))
                    for child in self.children()
                ])
            }
        )

    def adapt(self, query):
        if not self.path:
            return query

        keys = {
            0: 'kategorie_themen',
            1: 'kategorie_vollzugsbereiche',
            2: 'kategorie_aufgaben'
        }

        for level, value in enumerate(self.path.split('/')):
            query = query.filter(
                DirectoryEntry.content['values'][keys[level]].astext.like(
                    f'%{value.strip()}%'
                )
            )

        return query


@WinterthurApp.directory_search_widget('inline')
class InlineSearch(object):

    def __init__(self, app, directory, search_query):
        self.app = app
        self.directory = directory
        self.search_query = search_query

    def html(self, layout):
        return f'<b>{self.name}</b>'

    def adapt(self, query):
        return query
