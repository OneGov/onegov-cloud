from __future__ import annotations

import pytest

from base64 import b64encode
from datetime import date, datetime, time, UTC
from decimal import Decimal
from freezegun import freeze_time
from onegov.api.form import model_from_form
from onegov.core.utils import dictionary_to_binary
from onegov.form import parse_form
from pydantic import ValidationError
from tests.shared.utils import create_pdf
from textwrap import dedent


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path


def test_text_fields() -> None:
    text = dedent("""
        First name * = ___
        Last name = ___
        Country = ___[50]
        Comment = ...
        Zipcode = ___[4]/^[0-9]*$
        Currency = ___/^[A-Z]{3}$
    """)

    form = parse_form(text)()
    model = model_from_form(form)

    with pytest.raises(ValidationError, match=r'first_name\s+Field required'):
        model.model_validate({})

    with pytest.raises(
        ValidationError,
        match=r'country\s+String should have at most 50 characters'
    ):
        model.model_validate({'first_name': 'John', 'country': 'a'*51})

    with pytest.raises(
        ValidationError,
        match=r'zipcode\s+String should have at most 4 characters'
    ):
        model.model_validate({'first_name': 'John', 'zipcode': '12345'})

    with pytest.raises(
        ValidationError,
        match=r'zipcode\s+String should match pattern'
    ):
        model.model_validate({'first_name': 'John', 'zipcode': 'ABCD'})

    with pytest.raises(
        ValidationError,
        match=r'currency\s+String should match pattern'
    ):
        model.model_validate({'first_name': 'John', 'currency': 'AB'})

    with pytest.raises(
        ValidationError,
        match=r'currency\s+String should match pattern'
    ):
        model.model_validate({'first_name': 'John', 'currency': 'ABCD'})

    result: Any = model.model_validate({'first_name': 'John'})
    assert result.first_name == 'John'
    assert result.last_name is None
    assert result.country is None
    assert result.comment is None
    assert result.zipcode is None
    assert result.currency is None

    result = model.model_validate({
        'first_name': 'John',
        'last_name': 'Doe',
        'country': 'Switzerland',
        'comment': 'Oh so important',
        'zipcode': '6003',
        'currency': 'CHF',
    })
    assert result.first_name == 'John'
    assert result.last_name == 'Doe'
    assert result.country == 'Switzerland'
    assert result.comment == 'Oh so important'
    assert result.zipcode == '6003'
    assert result.currency == 'CHF'


def test_email_field() -> None:
    form = parse_form("E-Mail = @@@")()
    model = model_from_form(form)

    with pytest.raises(ValidationError, match=r'not a valid email address'):
        model.model_validate({'e_mail': 'bogus'})

    result: Any = model.model_validate({'e_mail': 'john.doe@example.com'})
    assert result.e_mail == 'john.doe@example.com'


def test_url_field() -> None:
    form = parse_form("Url = http://")()
    model = model_from_form(form)

    with pytest.raises(ValidationError, match=r'should be a valid URL'):
        model.model_validate({'url': 'bogus'})

    with pytest.raises(ValidationError, match=r'hostname is not valid'):
        model.model_validate({'url': 'http://localhost'})

    result: Any = model.model_validate({'url': 'https://example.com'})
    assert result.url == 'https://example.com/'


def test_video_url_field() -> None:
    form = parse_form("Url = video-url")()
    model = model_from_form(form)

    with pytest.raises(ValidationError, match=r'should be a valid URL'):
        model.model_validate({'url': 'bogus'})

    with pytest.raises(ValidationError, match=r'hostname is not valid'):
        model.model_validate({'url': 'http://localhost'})

    result: Any = model.model_validate({'url': 'https://example.com'})
    assert result.url == 'https://example.com/'


@freeze_time('2022-10-10')
def test_date_field() -> None:
    form = parse_form("Date = YYYY.MM.DD (today..+1 months)")()
    model = model_from_form(form)

    with pytest.raises(ValidationError, match=r'should be a valid date'):
        model.model_validate({'date': 'bogus'})

    with pytest.raises(ValidationError, match=r'should be greater'):
        model.model_validate({'date': '2022-10-09'})

    with pytest.raises(ValidationError, match=r'should be less'):
        model.model_validate({'date': '2022-11-11'})

    result: Any = model.model_validate({'date': '2022-10-10'})
    assert result.date == date(2022, 10, 10)


@freeze_time('2022-10-10')
def test_datetime_field() -> None:
    form = parse_form("Date = YYYY.MM.DD HH:MM (today..+1 months)")()
    model = model_from_form(form)

    with pytest.raises(ValidationError, match=r'should be a valid date'):
        model.model_validate({'date': 'bogus'})

    with pytest.raises(ValidationError, match=r'should be greater'):
        model.model_validate({'date': '2022-10-09T08:00:00Z'})

    with pytest.raises(ValidationError, match=r'should be less'):
        model.model_validate({'date': '2022-11-11T08:00:00Z'})

    result: Any = model.model_validate({'date': '2022-10-10T08:00:00Z'})
    assert result.date == datetime(2022, 10, 10, 8, tzinfo=UTC)


def test_time_field() -> None:
    form = parse_form("Time = HH:MM")()
    model = model_from_form(form)

    with pytest.raises(ValidationError, match=r'should be in a valid time'):
        model.model_validate({'time': 'bogus'})

    result: Any = model.model_validate({'time': '08:24'})
    assert result.time == time(8, 24)


def create_pdf_file_dict(path: Path, filename: str) -> dict[str, str]:
    pdf_path = path / filename
    create_pdf(str(pdf_path))
    with open(pdf_path, mode='rb') as fp:
        return {
            'filename': filename,
            'data': b64encode(fp.read()).decode('ascii')
        }


def test_fileinput_field(tmp_path: Path) -> None:
    form = parse_form("File * = *.pdf|*.doc")()
    model = model_from_form(form)

    with pytest.raises(ValidationError, match=r'should be a valid dict'):
        model.model_validate({'file': 'bogus'})

    with pytest.raises(
        ValidationError,
        match=r'file\.filename\s+Field required'
    ):
        model.model_validate({'file': {}})

    with pytest.raises(
        ValidationError,
        match=r'file\.data\s+Field required'
    ):
        model.model_validate({'file': {'filename': 'test.txt'}})

    with pytest.raises(
        ValidationError,
        match=r'file\.data\s+Base64 decoding error'
    ):
        model.model_validate({
            'file': {
                'filename': 'test.txt',
                'data': 'bogus'
            }
        })

    with pytest.raises(
        ValidationError,
        match=r'file\s+Value error, Unsupported mimetype'
    ):
        model.model_validate({
            'file': {
                'filename': 'test.txt',
                'data': b64encode(b'Hello world').decode('ascii')
            }
        })


    result: Any = model.model_validate({
        'file': create_pdf_file_dict(tmp_path, 'test.pdf')
    })
    assert result.file['filename'] == 'test.pdf'
    assert result.file['mimetype'] == 'application/pdf'
    assert result.file['size'] > 0
    assert dictionary_to_binary(result.file)


def test_multiplefileinput_field(tmp_path: Path) -> None:
    form = parse_form("Files * = *.pdf|*.doc (multiple)")()
    model = model_from_form(form)

    with pytest.raises(ValidationError, match=r'should be a valid list'):
        model.model_validate({'files': 'bogus'})

    with pytest.raises(ValidationError, match=r'at least 1 item'):
        model.model_validate({'files': []})

    with pytest.raises(
        ValidationError,
        match=r'files\.0\.filename\s+Field required'
    ):
        model.model_validate({'files': [{}]})

    with pytest.raises(
        ValidationError,
        match=r'files\.0\.data\s+Field required'
    ):
        model.model_validate({'files': [{'filename': 'test.txt'}]})

    with pytest.raises(
        ValidationError,
        match=r'files\.0\.data\s+Base64 decoding error'
    ):
        model.model_validate({
            'files': [{
                'filename': 'test.txt',
                'data': 'bogus'
            }]
        })

    with pytest.raises(
        ValidationError,
        match=r'files\.0\s+Value error, Unsupported mimetype'
    ):
        model.model_validate({
            'files': [{
                'filename': 'test.txt',
                'data': b64encode(b'Hello world').decode('ascii')
            }]
        })


    result: Any = model.model_validate({
        'files': [
            create_pdf_file_dict(tmp_path, 'test1.pdf'),
            create_pdf_file_dict(tmp_path, 'test2.pdf'),
        ]
    })
    assert len(result.files) == 2
    assert result.files[0]['filename'] == 'test1.pdf'
    assert result.files[0]['mimetype'] == 'application/pdf'
    assert result.files[0]['size'] > 0
    assert dictionary_to_binary(result.files[0])
    assert result.files[1]['filename'] == 'test2.pdf'
    assert result.files[1]['mimetype'] == 'application/pdf'
    assert result.files[1]['size'] > 0
    assert dictionary_to_binary(result.files[1])


def test_integer_field() -> None:
    form = parse_form("Age = 21..150")()
    model = model_from_form(form)

    with pytest.raises(ValidationError, match=r'should be a valid integer'):
        model.model_validate({'age': 'bogus'})

    with pytest.raises(ValidationError, match=r'should be greater'):
        model.model_validate({'age': 20})

    with pytest.raises(ValidationError, match=r'should be less'):
        model.model_validate({'age': 151})

    result: Any = model.model_validate({'age': 25})
    assert result.age == 25


def test_decimal_field() -> None:
    form = parse_form("Percentage = 0.00..100.00")()
    model = model_from_form(form)

    with pytest.raises(ValidationError, match=r'should be a valid decimal'):
        model.model_validate({'percentage': 'bogus'})

    with pytest.raises(ValidationError, match=r'should be greater'):
        model.model_validate({'percentage': '-1.00'})

    with pytest.raises(ValidationError, match=r'should be less'):
        model.model_validate({'percentage': '100.01'})

    result: Any = model.model_validate({'percentage': '50.00'})
    assert result.percentage == Decimal('50.00')


def test_stdnum_field() -> None:
    form = parse_form("Bank Account = # iban")()
    model = model_from_form(form)

    with pytest.raises(ValidationError):
        model.model_validate({'bank_account': 'bogus'})

    result: Any = model.model_validate({
        'bank_account': 'CH93 0076 2011 6238 5295 7'
    })
    assert result.bank_account == 'CH93 0076 2011 6238 5295 7'


def test_radio_field() -> None:
    text = dedent("""
        Gender =
            ( ) Male
            (x) Female
    """)
    form = parse_form(text)()
    model = model_from_form(form)

    with pytest.raises(ValidationError, match=r"should be 'Male' or 'Female'"):
        model.model_validate({'gender': 'bogus'})

    result: Any = model.model_validate({'gender': 'Female'})
    assert result.gender == 'Female'


def test_checkbox_field() -> None:
    text = dedent("""
        Required * =
            [ ] A
            [ ] B
            [ ] C
        Defaults =
            [x] D
            [ ] E
            [x] F
    """)
    form = parse_form(text)()
    model = model_from_form(form)

    with pytest.raises(ValidationError, match=r'required\s+Field required'):
        model.model_validate({})

    with pytest.raises(ValidationError, match=r'at least 1 item'):
        model.model_validate({'required': []})

    with pytest.raises(ValidationError, match=r"should be 'A', 'B' or 'C'"):
        model.model_validate({'required': ['bogus']})

    result: Any = model.model_validate({'required': ['A', 'B']})
    assert result.required == ['A', 'B']
    assert result.defaults == ['D', 'F']

    result = model.model_validate({
        'required': ['A', 'B'],
        'defaults': [],
    })
    assert result.required == ['A', 'B']
    assert result.defaults == []


def test_dependency_validation_chain() -> None:
    text = dedent("""
        Say * =
            ( ) Yes
                This * = ___
            (x) No
        Select =
            [x] A
                That * = ___
            [ ] B
            [ ] C
                Email * = @@@
    """)
    form = parse_form(text)()
    model = model_from_form(form)

    with pytest.raises(ValidationError, match=r'say_this is required'):
        model.model_validate({'say': 'Yes'})

    with pytest.raises(ValidationError, match=r'select_that is required'):
        model.model_validate({'say': 'No'})

    with pytest.raises(ValidationError, match=r'select_email is required'):
        model.model_validate({'say': 'No', 'select': ['C']})

    # NOTE: Even though e-mail is not required with this selection
    #       we will error if bogus data was submitted
    with pytest.raises(ValidationError, match=r'not a valid email address'):
        model.model_validate({
            'say': 'No',
            'select': ['B'],
            'select_email': 'bogus'
        })

    result: Any = model.model_validate({'say': 'No', 'select': ['B']})
    assert result.say == 'No'
    assert result.say_this is None
    assert result.select == ['B']
    assert result.select_that is None
    assert result.select_email is None

    result = model.model_validate({
        'say': 'Yes',
        'say_this': 'Something',
        'select': ['A', 'C'],
        'select_that': 'Nothing',
        'select_email': 'john.doe@example.com'
    })
    assert result.say == 'Yes'
    assert result.say_this == 'Something'
    assert result.select == ['A', 'C']
    assert result.select_that == 'Nothing'
    assert result.select_email == 'john.doe@example.com'
