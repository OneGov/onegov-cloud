from __future__ import annotations

from onegov.pdf.fetcher import AllowlistURLFetcher
from weasyprint import HTML  # type: ignore[import-untyped]


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def test_allowlist_url_fetcher(tmp_path: Path) -> None:
    secret = tmp_path / 'secret.txt'
    secret.write_text('SECRET_MARKER')
    allowed = tmp_path / 'allowed.txt'
    allowed.write_text('ALLOWED_MARKER')

    html = (
        f'<a rel="attachment" href="file://{secret}">x</a>'
        f'<a rel="attachment" href="file://{allowed}">y</a>'
    )

    pdf = HTML(string=html).write_pdf()
    assert pdf.count(b'/EmbeddedFile') == 2

    fetcher = AllowlistURLFetcher([f'file://{allowed}'])
    pdf = HTML(string=html, url_fetcher=fetcher).write_pdf()
    assert pdf.count(b'/EmbeddedFile') == 1

    pdf = HTML(string=html, url_fetcher=AllowlistURLFetcher()).write_pdf()
    assert b'/EmbeddedFile' not in pdf
