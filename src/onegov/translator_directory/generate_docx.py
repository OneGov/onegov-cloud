from io import BytesIO
from onegov.translator_directory.models.translator import Translator
from docxtpl import DocxTemplate


def fill_variables_in_docx(original_docx, t: Translator, **kwargs):
    docx_template = DocxTemplate(original_docx)

    template_variables = {
        "translator_last_name": t.last_name,
        "translator_first_name": t.first_name,
        "translator_nationality": t.nationality or "",
        "translator_gender": t.gender or "",
        "translator_address": t.address or "",
        "translator_city": t.city or "",
        "translator_zip_code": t.zip_code or "",
        "greeting": gendered_greeting(t) or "",
    }

    # Values below are also required for one template. where to get?
    # translator_decision = ('definitiv provisorisch).
    # translator_function = ('Dolmetschen', 'Übsersetzen', '
    # 'Kommunikationsüberwachung')

    for key, value in kwargs.items():
        template_variables[key] = value or ""

    found_nulls = {k: v for k, v in template_variables.items() if not v}
    if found_nulls:
        non_null_values = {
            k: v for k, v in template_variables.items() if k not in found_nulls
        }
        return found_nulls, render_docx(docx_template, non_null_values)

    else:
        return {}, render_docx(docx_template, template_variables)


def render_docx(docx_template, template_variables):
    """ Creates the word file.

    substituted_variables: dictionary of values to find and replace in final
    word file
    """
    docx_template.render(template_variables)
    in_memory_docx = BytesIO()
    docx_template.save(in_memory_docx)
    in_memory_docx.seek(0)
    return in_memory_docx.read()


def gendered_greeting(translator):
    if translator.gender == "M":
        return "Sehr geehrter Herr"
    elif translator.gender == "F":
        return "Sehr geehrte Frau"
    else:
        return "Sehr geehrte*r Herr/Frau"
