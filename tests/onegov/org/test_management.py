from __future__ import annotations

from markupsafe import Markup
from onegov.people import AgencyCollection
from onegov.core.utils import Bunch
from onegov.org.management import LinkHealthCheck
from onegov.page import PageCollection


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import TestOrgApp


def test_link_health_check(org_app: TestOrgApp) -> None:

    test_domain = 'example.org'

    def get_request() -> Any:
        return Bunch(
            link=lambda x: 'URL-' + x.__class__.__name__,
            session=org_app.session(),
            domain=test_domain
        )

    request = get_request()
    pages = PageCollection(request.session)
    agencies = AgencyCollection(request.session)

    valid = [
        'www.discord.com',
        'https://example.org'
    ]

    invalid_fmt = [
        'www.disco.',
        'https:/nonsense.com',
        'www.wrong-domain.comm',
    ]

    not_found = ['https://seantis.ch/xxx']
    invalid_domain = ['https://testesttest.com']

    fragments = [
        "Other valid: $URL. twice: $URL",
        "Check out $URL. It's for free.",
        "Invalid: $URL  ",
        "Invalid: $URL...",
        "Invalid: $URL",
        "Invalid: $URL",
        "Invalid: $URL",
    ]

    external_exp = [valid[0]] + not_found + invalid_domain
    internal_exp = [valid[1]]

    links = valid + invalid_fmt + not_found + invalid_domain
    assert len(fragments) == len(links)

    text = "\n".join(f.replace('$URL', u) for f, u in zip(fragments, links))

    page = pages.query().first()
    assert page is not None
    page.lead = text  # type: ignore[attr-defined]

    agencies.add(
        title='Test',
        parent=None,
        portrait=Markup('<a href="http://www.google.com"></a>')
    )

    # check external
    check = LinkHealthCheck(request, 'external')

    found_urls = check.extractor.find_urls(text, only_unique=True)
    assert found_urls == valid + not_found + invalid_domain

    urls = tuple(check.find_urls())
    assert urls == (
        ('Topic', 'URL-Topic', tuple(external_exp)),
        ('Agency', 'URL-Agency', ('http://www.google.com',))
    )

    # check internal
    check.link_type = 'internal'
    urls = tuple(check.find_urls())
    assert urls == (
        ('Topic', 'URL-Topic', tuple(internal_exp)),
        ('Agency', 'URL-Agency', tuple())
    )
    stats, all_results = check.unhealthy_urls()

    # handled by js in the frontend, so the stats are basically empty
    assert len(all_results) == len(internal_exp)
    assert stats.total == 0
    assert stats.ok == 0
    assert stats.nok == 0
    assert stats.error == 0
