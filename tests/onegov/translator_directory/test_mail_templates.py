from __future__ import annotations

import docx
import pytest
from docxtpl import DocxTemplate  # type: ignore[import-untyped]
from io import BytesIO
from os.path import basename
from onegov.core.layout import Layout
from onegov.core.utils import module_path, Bunch
from onegov.translator_directory import _
from onegov.translator_directory.constants import GENDERS
from onegov.translator_directory.generate_docx import (
    gendered_greeting,
    parse_from_filename,
)
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.utils import country_code_to_name
from onegov.translator_directory.views.translator import (
    fill_docx_with_variables,
)
from sedate import utcnow
from tests.onegov.translator_directory.shared import (
    translator_data,
    iter_block_items
)


from typing import Any


# FIXME: It might be better to just use freezegun to run the test
#        at a known good time
@pytest.mark.skip_night_hours
def test_read_write_cycle() -> None:
    translator = Translator(**translator_data)
    translator.admission = 'certified'

    request: Any = Bunch(
        locale='en',
        app=Bunch(version='1.0', sentry_dsn=None)
    )
    layout = Layout(model=object(), request=request)

    mapping = country_code_to_name(request.locale)
    nationalities = (
        ', '.join(mapping[n] for n in translator.nationalities)) if (
        translator.nationalities) else ''

    variables_to_fill: dict[str, Any] = {
        'current_date': layout.format_date(utcnow(), 'date'),
        'translator_date_of_birth': layout.format_date(
            translator.date_of_birth, 'date'
        ),
        'translator_date_of_decision': layout.format_date(
            translator.date_of_decision, 'date'
        ),
        'sender_initials': 'JODO',
        'greeting': gendered_greeting(translator),
        'translator_first_name': translator.first_name,
        'translator_last_name': translator.last_name,
        'translator_address': translator.address,
        'translator_zip_code': translator.zip_code,
        'translator_city': translator.city,
        'translator_nationality': nationalities,
        'translator_admission': '',
    }

    template_name = module_path(
        'tests.onegov.translator_directory', 'fixtures/Vorlage.docx'
    )

    with open(template_name, 'rb') as f:
        nulls, filled_template = fill_docx_with_variables(
            BytesIO(f.read()), translator, request, **variables_to_fill
        )
        assert 'translator_admission' in nulls
        f.seek(0)
        variables_to_fill['translator_admission'] = _(translator.admission)
        nulls, filled_template = fill_docx_with_variables(
            BytesIO(f.read()), translator, request, **variables_to_fill
        )
        found_variables_in_docx = set()
        expected_variables_in_docx = variables_to_fill.values()
        doc = docx.Document(BytesIO(filled_template))

        for target in expected_variables_in_docx:
            for block in iter_block_items(doc):
                if target in block.text:
                    found_variables_in_docx.add(target)

        assert set(expected_variables_in_docx) == found_variables_in_docx


def test_helper_methods() -> None:
    genders = list(GENDERS.keys())

    translator = Translator(**translator_data)
    assert gendered_greeting(translator) == 'Sehr geehrter Herr'
    translator.gender = genders[1]  # type: ignore[assignment]
    assert gendered_greeting(translator) == 'Sehr geehrte Frau'
    translator.gender = genders[2]  # type: ignore[assignment]
    assert gendered_greeting(translator) == 'Sehr geehrte*r Herr/Frau'


def test_signature_image_parse_from_filename() -> None:
    signature = module_path(
        'tests.onegov.translator_directory',
        'fixtures/Unterschrift__DOJO__Adj_mV_John_Doe__Stv_Dienstchef.jpg',
    )

    signature_values = parse_from_filename(basename(signature))

    assert signature_values.sender_abbrev == 'DOJO'
    assert signature_values.sender_full_name == 'Adj mV John Doe'
    assert signature_values.sender_function == 'Stv Dienstchef'

    template_name = module_path(
        'tests.onegov.translator_directory',
        'fixtures/Vorlage_mit_Unterschrift_als_Bild.docx'
    )
    additional_variables = {
        'sender_full_name': signature_values.sender_full_name,
        'sender_function': signature_values.sender_function,
    }

    with open(template_name, 'rb') as f1, open(signature, 'rb') as f2:
        nulls, filled_template = fill_docx_with_variables(
            BytesIO(f1.read()),
            Translator(**translator_data),
            request=Bunch(locale='en'),  # type: ignore[arg-type]
            signature_file=BytesIO(f2.read()),
            **additional_variables
        )
    doc = DocxTemplate(BytesIO(filled_template))
    assert doc.get_undeclared_template_variables() == set()
