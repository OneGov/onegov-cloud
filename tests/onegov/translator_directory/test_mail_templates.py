from io import BytesIO
import docx
from onegov.core.utils import module_path
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.views.translator import\
    fill_variables_in_docx, gendered_greeting
from tests.onegov.translator_directory.shared import translator_data,\
    iter_block_items


def test_read_write_cycle():
    translator = Translator(**translator_data)

    variables_to_fill = {
        'greeting': gendered_greeting(translator),
        'translator_first_name': translator.first_name,
        'translator_last_name': translator.last_name,
        'translator_address': translator.address,
        'translator_zip_code': translator.zip_code,
        'translator_city': translator.city,
        'sender_email_prefix': 'john.doe',
        'sender_phone_number': '041 229 99 99',
        'current_date': '20. April 2023'
    }
    template_name = module_path('tests.onegov.translator_directory',
                                'fixtures/template.docx')

    with open(template_name, 'rb') as f:
        filled_template = fill_variables_in_docx(
            BytesIO(f.read()), translator, **variables_to_fill
        )
        variables_to_fill['sender_phone_number'] = '229 99 99'
        found_variables_in_docx = set()
        expected_variables_in_docx = variables_to_fill.values()
        doc = docx.Document(BytesIO(filled_template))

        for target in expected_variables_in_docx:
            for block in iter_block_items(doc):
                if target in block.text:
                    assert '041 041' not in block.text  # 041 is static
                    found_variables_in_docx.add(target)

        assert set(expected_variables_in_docx) == found_variables_in_docx
