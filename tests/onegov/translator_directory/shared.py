from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from docx.document import Document
from docx.oxml import CT_P, CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from onegov.translator_directory.collections.certificate import (
    LanguageCertificateCollection)
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import (
    TranslatorCollection)
from onegov.translator_directory.models.translator import GENDERS


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.translator_directory import TranslatorDirectoryApp
    from onegov.translator_directory.models.certificate import (
        LanguageCertificate)
    from onegov.translator_directory.models.language import Language
    from onegov.translator_directory.models.translator import Translator
    from sqlalchemy.orm import Session

translator_data: dict[str, Any] = {
    'state': 'published',
    'pers_id': 1234,
    'first_name': 'Hugo',
    'last_name': 'Benito',
    'admission': None,
    'withholding_tax': False,
    'self_employed': False,
    'gender': list(GENDERS.keys())[0],
    'date_of_birth': date.today(),
    'nationalities': ['CH', 'AT'],
    'address': 'Downing Street 5',
    'zip_code': '4000',
    'city': 'Luzern',
    'drive_distance': None,
    'social_sec_number': '756.1234.4568.94',
    'bank_name': 'R-BS',
    'bank_address': 'Bullstreet 5',
    'account_owner': 'Hugo Benito',
    'iban': '',
    'email': 'hugo@benito.com',
    'tel_mobile': '079 000 00 00',
    'tel_office': '041 444 44 44',
    'tel_private': None,
    'availability': 'always',
    'profession': 'craftsman',
    'occupation': 'baker',
    'operation_comments': '',
    'confirm_name_reveal': None,
    'date_of_application': date.today() - timedelta(days=100),
    'date_of_decision': date.today() - timedelta(days=50),
    'proof_of_preconditions': 'all okay',
    'agency_references': 'Some ref',
    'education_as_interpreter': False,
    'comments': None,
    'expertise_professional_guilds': tuple(),
    'expertise_professional_guilds_other': tuple(),
    'expertise_interpreting_types': tuple(),
    'for_admins_only': False
}


def create_languages(session: Session) -> list[Language]:
    collection = LanguageCollection(session)
    return [
        collection.add(name=lang)
        for lang in ('German', 'French', 'Italian', 'Arabic')
    ]


def create_certificates(session: Session) -> list[LanguageCertificate]:
    collection = LanguageCertificateCollection(session)
    return [
        collection.add(name=cert)
        for cert in ('AAAA', 'BBBB', 'CCCC', 'DDDD')
    ]


def create_translator(
    translator_app: TranslatorDirectoryApp,
    email: str | None = None,
    **kwargs: Any
) -> Translator:
    data = deepcopy(translator_data)
    for key in kwargs:
        if key in data:
            data[key] = kwargs[key]
    if email:
        data['email'] = email

    return TranslatorCollection(translator_app).add(**data)


def create_translators(
    translator_app: TranslatorDirectoryApp,
    count: int = 1
) -> list[Translator]:
    translators = TranslatorCollection(translator_app)
    results = []
    for i in range(count):
        data = deepcopy(translator_data)
        data['pers_id'] = i
        data['email'] = f'translator{i}@test.com'
        data['first_name'] = f'trans_{i}'
        data['last_name'] = f'later_{i}'
        results.append(translators.add(**data))

    return results


def iter_block_items(parent: Document | _Cell) -> Iterator[Paragraph]:
    """ Recursively iterates over the elements of the .docx document.
        Only use this for testing.

    See `https://github.com/python-openxml/python-docx/issues/40`
    """

    if isinstance(parent, Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Error parsing word file. ")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            table = Table(child, parent)
            for row in table.rows:
                for cell in row.cells:
                    yield from iter_block_items(cell)
