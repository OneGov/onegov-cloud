from io import BytesIO
from onegov.translator_directory.models.translator import Translator
from docxtpl import DocxTemplate


def fill_variables_in_docx(original_docx, t: Translator, **kwargs):
    docx_template = DocxTemplate(original_docx)

    # Variables to find and replace in final word file
    substituted_variables = {
        'translator_last_name': t.last_name,
        'translator_first_name': t.first_name,
        'translator_nationality': t.nationality,
        'translator_gender': t.gender,
        'translator_address': t.address,
        'translator_city': t.city,
        'translator_zip_code': t.zip_code,
        'greeting': gendered_greeting(t),
    }

    # Values below are also required for one template. where to get?

    # translator_decision = ('definitiv provisorisch).
    # translator_function = ('Dolmetschen', 'Übsersetzen', '
    # 'Kommunikationsüberwachung')

    for key, value in kwargs.items():
        substituted_variables[key] = value

    docx_template.render(substituted_variables)
    in_memory_docx = BytesIO()
    docx_template.save(in_memory_docx)

    in_memory_docx.seek(0)
    return in_memory_docx.read()


def gendered_greeting(translator):
    if translator.gender == 'M':
        return 'Sehr geehrter Herr'
    elif translator.gender == 'F':
        return 'Sehr geehrte Frau'
    else:
        return 'Sehr geehrte*r Herr/Frau'
