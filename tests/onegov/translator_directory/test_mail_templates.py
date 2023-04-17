from io import BytesIO
import docx
from onegov.core.utils import module_path, Bunch
from onegov.translator_directory.constants import GENDERS, ADMISSIONS
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.views.translator import\
    fill_variables_in_docx, gendered_greeting, get_initials
from sedate import utcnow
from tests.onegov.translator_directory.shared import translator_data,\
    iter_block_items
from onegov.translator_directory import _
from onegov.core.layout import Layout


def test_read_write_cycle():
    translator = Translator(**translator_data)
    translator.admission = ADMISSIONS['certified']

    layout = Layout(model=object(), request=Bunch(locale='en'))
    variables_to_fill = {
        'current_date': layout.format_date(utcnow(), 'date'),
        'translator_date_of_birth': layout.format_date(
            translator.date_of_birth, 'date'
        ),
        'translator_date_of_decision': layout.format_date(
            translator.date_of_decision, 'date'
        ),
        'translator_admission': _(translator.admission),
        'greeting': gendered_greeting(translator),
        'translator_first_name': translator.first_name,
        'translator_last_name': translator.last_name,
        'translator_address': translator.address,
        'translator_zip_code': translator.zip_code,
        'translator_city': translator.city,
    }
    template_name = module_path('tests.onegov.translator_directory',
                                'fixtures/template.docx')

    with open(template_name, 'rb') as f:
        filled_template = fill_variables_in_docx(
            BytesIO(f.read()), translator, **variables_to_fill
        )
        found_variables_in_docx = set()
        expected_variables_in_docx = variables_to_fill.values()
        doc = docx.Document(BytesIO(filled_template))

        for target in expected_variables_in_docx:
            for l in iter_block_items(doc):
                line = l.text
                # make sure all variables have been rendered
                assert '{{' not in line and '}}' not in line
                if target in line:
                    found_variables_in_docx.add(target)

        assert set(expected_variables_in_docx) == found_variables_in_docx


def test_helper_methods():
    assert get_initials(first_name='Jane', last_name='Doe') == 'DOJA'

    genders = list(GENDERS.keys())

    translator = Translator(**translator_data)
    assert gendered_greeting(translator) == 'Sehr geehrter Herr'
    translator.gender = genders[1]
    assert gendered_greeting(translator) == 'Sehr geehrte Frau'
    translator.gender = genders[2]
    assert gendered_greeting(translator) == 'Sehr geehrte*r Herr/Frau'
