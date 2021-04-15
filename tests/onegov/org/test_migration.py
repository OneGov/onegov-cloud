import transaction

from onegov.core.utils import Bunch
from onegov.org.migration import PageNameChange
from onegov.page import PageCollection


def test_page_name_change(client):
    session = client.app.session()

    def link(model):
        uri = "/".join(a.name for a in model.ancestors) + f'/{model.name}'
        return 'https://example.com/' + uri.lstrip('/')

    pages = PageCollection(session)

    type_ = 'topic'

    title = 'A'
    page = pages.add(
        parent=None,
        title=title,
        type=type_,
        meta={'trait': 'page', 'access': 'public'}
    )
    page_id = page.id
    subpage = pages.add(title=f'Sub {title}', type=type_, parent=page)
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

    transaction.commit()
    request = Bunch(session=client.app.session(), link=link)
    pages = PageCollection(request.session)
    page = pages.by_id(page_id)

    migration = PageNameChange(request, page, 'c')
    count = migration.execute()
    sublink = pages.by_id(sublink_id)
    subpage = pages.by_id(subpage_id)

    print(sublink.lead)
    print(sublink.text)
    assert count == 3
    assert link(page) != old_page_link
    assert sublink.url == link(page)
    assert link(page) in sublink.text
    assert link(subpage) in sublink.lead
