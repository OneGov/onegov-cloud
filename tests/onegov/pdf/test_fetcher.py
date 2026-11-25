from __future__ import annotations

import pytest

from onegov.pdf.fetcher import AllowlistURLFetcher, SafeCSS, SafeHTML
from weasyprint import (  # type: ignore[import-untyped]
    HTML,  # ruff: ignore[TID251]
)


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def attachment_html(tmp_path: Path) -> tuple[str, str]:
    secret = tmp_path / 'secret.txt'
    secret.write_text('SECRET_MARKER')
    allowed = tmp_path / 'allowed.txt'
    allowed.write_text('ALLOWED_MARKER')
    html = (
        f'<a rel="attachment" href="file://{secret}">x</a>'
        f'<a rel="attachment" href="file://{allowed}">y</a>'
    )
    return html, f'file://{allowed}'


def test_allowlist_url_fetcher(tmp_path: Path) -> None:
    html, allowed_url = attachment_html(tmp_path)

    pdf = HTML(string=html).write_pdf()
    assert pdf.count(b'/EmbeddedFile') == 2

    fetcher = AllowlistURLFetcher([allowed_url])
    pdf = HTML(string=html, url_fetcher=fetcher).write_pdf()
    assert pdf.count(b'/EmbeddedFile') == 1

    pdf = HTML(string=html, url_fetcher=AllowlistURLFetcher()).write_pdf()
    assert b'/EmbeddedFile' not in pdf


def test_safe_html(tmp_path: Path) -> None:
    html, allowed_url = attachment_html(tmp_path)

    assert b'/EmbeddedFile' not in SafeHTML(string=html).write_pdf()

    pdf = SafeHTML(string=html, allowed_urls=[allowed_url]).write_pdf()
    assert pdf.count(b'/EmbeddedFile') == 1

    with pytest.raises(TypeError):
        SafeHTML(string=html, url_fetcher=AllowlistURLFetcher())


def test_safe_css(tmp_path: Path) -> None:
    imported = tmp_path / 'a5.css'
    imported.write_text('@page { size: A5 }')
    url = f'file://{imported}'
    css = f"@import url('{url}');"

    def page_width(stylesheet: SafeCSS) -> float:
        document = SafeHTML(string='<p>x</p>').render(stylesheets=[stylesheet])
        return document.pages[0].width

    a4 = page_width(SafeCSS(string=''))
    assert page_width(SafeCSS(string=css)) == a4
    assert page_width(SafeCSS(string=css, allowed_urls=[url])) != a4

    with pytest.raises(TypeError):
        SafeCSS(string=css, url_fetcher=AllowlistURLFetcher())
