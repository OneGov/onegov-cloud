from __future__ import annotations

import base64

from datetime import datetime
from onegov.org.models.legacy_file import LegacyFile, LegacyImage


def test_legacy_file_path() -> None:
    assert LegacyFile('abc.pdf').path == 'files/abc.pdf'
    assert LegacyImage('abc.jpg').path == 'images/abc.jpg'


def test_legacy_file_date() -> None:
    assert LegacyFile('abc.pdf').date is None

    moment = datetime(2021, 5, 1, 12, 0)
    dated = LegacyFile('abc.pdf', info={'modified_time': moment})
    assert dated.date == moment.date()


def test_legacy_file_original_name() -> None:
    encoded = base64.urlsafe_b64encode(b'report.pdf').decode()
    legacy = LegacyFile(f'{encoded}-thumbnail')
    assert legacy.original_name == b'report.pdf'

    # no dash -> no original name
    assert LegacyFile('plainname').original_name is None


def test_legacy_file_from_url() -> None:
    legacy = LegacyFile.from_url('https://example.org/files/abc.pdf')
    assert legacy.filename == 'abc.pdf'
    assert legacy.path == 'files/abc.pdf'
