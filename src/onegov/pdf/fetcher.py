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
    internal hosts (SSRF). Pass this to every ``HTML(...)`` that renders
    data we don't fully control.

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
