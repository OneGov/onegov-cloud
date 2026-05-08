from __future__ import annotations

from onegov.translator_directory.layout import TranslatorLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_translator_layout(session: Session) -> None:
    assert TranslatorLayout.format_languages(None) == ''
    assert TranslatorLayout.format_drive_distance(None) == ''
    assert TranslatorLayout.format_drive_distance(5) == '5 km'
