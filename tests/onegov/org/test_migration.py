from __future__ import annotations

import transaction

from onegov.core.utils import Bunch
from onegov.directory import DirectoryCollection, DirectoryConfiguration
from onegov.org.management import PageNameChange
from onegov.org.models import ExtendedDirectory, Topic
from onegov.page import PageCollection


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.directory import Directory
    from onegov.page import Page
    from .conftest import TestOrgApp


def test_page_name_change(org_app: TestOrgApp) -> None:
    session = org_app.session()

    def link(model: Page) -> str:
        uri = "/".join(a.name for a in model.ancestors) + f'/{model.name}'
        return 'https://example.com/' + uri.lstrip('/')

    pages = PageCollection(session)
    directories: DirectoryCollection[Directory]
    directories = DirectoryCollection(session, type='extended')

    type_ = 'topic'

    title = 'A'
    page = pages.add(
        parent=None,
        title=title,
        type=type_,
        meta={'trait': 'page', 'access': 'public'}
    )
    assert isinstance(page, Topic)
    page_id = page.id
    subpage = pages.add(title=f'Sub {title}', type=type_, parent=page)
    assert isinstance(subpage, Topic)
    subpage_id = subpage.id
    old_page_link = link(page)
    sublink_id = pages.add(
        title=f'SubLink {title}',
        type=type_,
        parent=subpage,
        url=old_page_link,
        lead=f'subpage redirect to {link(subpage)}',
        text=f'Go to Home: {link(page)}',
        meta={'trait': 'link', 'access': 'public'}
    ).id

    # SiteCollection uses Directory in query, so we test if we do not skip
    # content or meta fields (lead, text). The query actually returns the
    # correct polymorphic class
    directory = directories.add(
        title='Dir',
        lead=f'Links to {link(page)}',
        text=f'Links to {link(page)}',
        structure="""
                Name *= ___
            """,
        configuration=DirectoryConfiguration(
            title="[name]",
            order=['name']
        )
    )
    dir_id = directory.id
    transaction.commit()
    request: Any = Bunch(session=org_app.session(), link=link)
    pages = PageCollection(request.session)
    directories = DirectoryCollection(request.session)
    page = pages.by_id(page_id)  # type: ignore[assignment]

    migration = PageNameChange(request, page, new_name='c')
    count = migration.execute()
    sublink = pages.by_id(sublink_id)
    subpage = pages.by_id(subpage_id)  # type: ignore[assignment]
    directory = directories.by_id(dir_id)  # type: ignore[assignment]

    assert count == 5
    assert link(page) != old_page_link
    assert isinstance(sublink, Topic)
    assert sublink.url == link(page)
    assert sublink.text is not None
    assert sublink.lead is not None
    assert link(page) in sublink.text
    assert link(subpage) in sublink.lead
    assert isinstance(directory, ExtendedDirectory)
    assert directory.text is not None
    assert directory.lead is not None
    assert link(page) in directory.text
    assert link(page) in directory.lead
