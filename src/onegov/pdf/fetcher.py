from weasyprint import (  # type: ignore[import-untyped]
    CSS,  # ruff: ignore[banned-api]
    HTML,  # ruff: ignore[banned-api]
)
from weasyprint.urls import (  # type: ignore[import-untyped]
    URLFetcher,
    URLFetcherResponse,
)

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


class AllowlistURLFetcher(URLFetcher):  # type: ignore[misc]
    """WeasyPrint URL fetcher that only fetches the given URLs.

    WeasyPrint's default fetcher follows any URL in the rendered HTML,
    including ``file://`` (embedding local files as PDF attachments) and
    internal hosts (SSRF).

    """

    def __init__(
        self, allowed_urls: Iterable[str] = (), **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.allowed_urls = frozenset(allowed_urls)

    def fetch(
        self, url: str, headers: dict[str, str] | None = None
    ) -> URLFetcherResponse:
        if url not in self.allowed_urls:
            raise ValueError(f'URL not allowed in PDF: {url}')
        return super().fetch(url, headers)


class SafeHTML(HTML):  # type: ignore[misc]
    """``weasyprint.HTML`` that fetches nothing but ``allowed_urls``.

    Direct use of ``weasyprint.HTML`` is banned via ruff (``TID251``).

    """

    def __init__(
        self, *args: Any, allowed_urls: Iterable[str] = (), **kwargs: Any
    ) -> None:
        if 'url_fetcher' in kwargs:
            raise TypeError('Use allowed_urls instead of url_fetcher')
        super().__init__(
            *args, url_fetcher=AllowlistURLFetcher(allowed_urls), **kwargs
        )


class SafeCSS(CSS):  # type: ignore[misc]
    """``weasyprint.CSS`` that fetches nothing but ``allowed_urls``.

    Direct use of ``weasyprint.CSS`` is banned via ruff (``TID251``).

    """

    def __init__(
        self, *args: Any, allowed_urls: Iterable[str] = (), **kwargs: Any
    ) -> None:
        if 'url_fetcher' in kwargs:
            raise TypeError('Use allowed_urls instead of url_fetcher')
        super().__init__(
            *args, url_fetcher=AllowlistURLFetcher(allowed_urls), **kwargs
        )
