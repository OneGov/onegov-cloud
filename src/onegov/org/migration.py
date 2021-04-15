import re
from collections import defaultdict

from onegov.core.utils import normalize_for_url
from onegov.org.models import SiteCollection


class ContentMigrationMixin:
    migration_fields = ('lead', 'text', 'url')


class LinkMigration(ContentMigrationMixin):

    def __init__(self, request, old_uri, new_uri=None):
        self.request = request
        self.old_uri = old_uri
        self.new_uri = new_uri

        old_is_domain = not self.old_uri.startswith('http')
        new_is_domain = not self.new_uri.startswith('http')

        if old_is_domain != new_is_domain:
            raise ValueError('Domains must be consistent')

        self.use_domain = old_is_domain
        self.site_collection = SiteCollection(request.session)

    def migrate_url(
            self,
            item,
            fields,
            test=False,
            group_by=None,
            count_obj=None
    ):
        """Supports replacing url's and domain names.

         """
        count = 0
        count_by_id = count_obj or {}

        old_uri = self.old_uri
        new_uri = self.new_uri
        group_by = group_by or item.__class_.__name__

        def repl(matchobj):
            if self.use_domain:
                return f'{matchobj.group(1)}{new_uri}'
            return new_uri

        if self.use_domain:
            # Prevent replacing things that might not be an url
            pattern = re.compile(r'(https?://)' + f'({re.escape(old_uri)})')
        else:
            pattern = re.compile(re.escape(old_uri))

        for field in fields:
            value = getattr(item, field, None)
            if not value:
                continue
            new_val = pattern.sub(repl, value)
            if value != new_val:
                count += 1
                id_count = count_by_id.setdefault(
                    group_by,
                    defaultdict(int)
                )

                id_count[field] += 1
                if not test:
                    setattr(
                        item,
                        field,
                        new_val
                    )
        return count, count_by_id

    def migrate_site_collection(self, test=False):
        grouped = {}
        total = 0

        for name, entries in self.site_collection.get().items():
            for item in entries:
                count, grouped_count = self.migrate_url(
                    item, self.migration_fields,
                    test=test,
                    group_by=name,
                    count_obj=grouped
                )
                grouped = grouped_count
                total += count
        return total, grouped


class PageNameChange(ContentMigrationMixin):

    def __init__(self, request, page, new_name):
        assert new_name == normalize_for_url(new_name)
        assert page.name != new_name

        self.request = request
        self.page = page
        self.new_name = new_name
        self.site_collection = SiteCollection(request.session)

    @property
    def subpages(self):
        pages = []

        def add(page):
            nonlocal pages
            pages.append(page)
            for child in page.children:
                add(child)

        for p in self.page.children:
            add(p)

        return pages

    def execute(self, test=False):
        """ Executes a page name change. All subpages' urls are changed by
        this action. For all subpages, the old and new url must be swapped in
        all possible fields of all sites of the SiteCollection.
        """

        page = self.page
        subpages = self.subpages

        # Make sure the order before and after is the same
        urls_before = tuple(self.request.link(p) for p in subpages + [page])
        page.name = self.new_name
        self.request.session.flush()
        urls_after = tuple(self.request.link(p) for p in subpages + [page])
        assert urls_before != urls_after

        count = 0
        for before, after in zip(urls_before, urls_after):
            migration = LinkMigration(self.request, before, after)
            total, grouped = migration.migrate_site_collection(test=test)
            count += total
        return count

    @classmethod
    def from_form(cls, model, form):
        return cls(form.request, model, form.name.data)
