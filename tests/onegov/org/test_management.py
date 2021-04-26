from onegov.core.utils import Bunch
from onegov.org.management import LinkHealthCheck
from onegov.page import PageCollection


def test_link_health_check(org_app):

    test_domain = 'example.org'

    def get_request():
        return Bunch(
            link=lambda x: 'URL-' + x.__class__.__name__,
            session=org_app.session(),
            domain=test_domain
        )

    request = get_request()
    pages = PageCollection(request.session)

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

    links = valid + invalid_fmt + not_found + invalid_domain
    assert len(fragments) == len(links)
    fetched_count = len(links) - len(invalid_fmt)
    error_count = len(invalid_domain)
    nok_count = len(not_found)

    text = "\n".join(
        f.replace('$URL', u) for f, u in zip(fragments, links))

    page = pages.query().first()
    page.lead = text

    check = LinkHealthCheck(request)
    found_urls = check.extractor.find_urls(text, only_unique=True)
    assert found_urls == valid + not_found + invalid_domain

    urls = tuple(check.find_urls())
    assert urls == (('Topic', 'URL-Topic', found_urls),)

    all_results = check.unhealthy_urls()
    stats = check.unhealthy_urls_stats

    print(all_results[0])
    print(stats)
    assert stats.total == fetched_count
    assert stats.ok == len(valid)
    assert stats.nok == nok_count
    assert stats.error == error_count

    # check filters
    check.link_type = 'internal'
    urls = tuple(check.find_urls())
    filtered = tuple([u for u in found_urls if test_domain in u])
    assert urls == (('Topic', 'URL-Topic', filtered),)

    check.link_type = 'external'
    urls = tuple(check.find_urls())
    filtered = tuple([u for u in found_urls if test_domain not in u])
    assert urls == (('Topic', 'URL-Topic', filtered),)
