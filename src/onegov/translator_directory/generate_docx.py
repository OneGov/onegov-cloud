from io import BytesIO
from onegov.translator_directory import _
from docxtpl import DocxTemplate


def fill_docx_with_variables(original_docx, t, request, **kwargs):
    """ Fills the variables in a docx file with the given key-value pairs.
        The original_docx template contains Jinja-Variables that map to keys
        in the template_variables dictionary.

      Returns A tuple containing two elements:
          - Variables that were found to be None or empty.
          - The rendered docx file.
      """

    docx_template = DocxTemplate(original_docx)
    template_variables = {
        'translator_last_name': t.last_name,
        'translator_first_name': t.first_name,
        'translator_nationality': t.nationality,
        'translator_gender': t.gender,
        'translator_address': t.address,
        'translator_city': t.city,
        'translator_zip_code': t.zip_code,
        'translator_languages': '\n'.join(
            ''.join(
                [request.translate(lang_type) + ': ']
                + [', '.join([str(language) for language in langs])]
            )
            for langs, lang_type in (
                (t.spoken_languages, _('Spoken languages')),
                (t.written_languages, _('Written languages')),
                (t.monitoring_languages, _('Monitoring languages')),
            )
            if langs
        ),
        'greeting': gendered_greeting(t),
        'translator_decision': 'definitiv'
        if t.admission == 'certified'
        else 'provisorisch',
        'translator_full_or_part': 'vollumfänglicher'
        if t.admission == 'certified'
        else 'teilweiser',
        'translator_functions': ', '.join(list(translator_functions(t))),
    }

    for key, value in kwargs.items():
        template_variables[key] = value or ''

    found_nulls = {k: v for k, v in template_variables.items() if not v}
    if found_nulls:
        non_null_values = {
            k: v for k, v in template_variables.items() if k not in found_nulls
        }
        return found_nulls, render_docx(docx_template, non_null_values)

    else:
        return {}, render_docx(docx_template, template_variables)


def render_docx(docx_template, template_variables):
    """Creates the word file.

    substituted_variables: dictionary of values to find and replace in final
    word file. Values not present are simply ignored.
    """
    docx_template.render(template_variables)
    in_memory_docx = BytesIO()
    docx_template.save(in_memory_docx)
    in_memory_docx.seek(0)
    return in_memory_docx.read()


def translator_functions(translator):
    if translator.written_languages:
        yield 'Übersetzen'
    if translator.spoken_languages:
        yield 'Dolmetschen'
    if translator.monitoring_languages:
        yield 'Kommunikationsüberwachung'


def gendered_greeting(translator):
    if translator.gender == "M":
        return "Sehr geehrter Herr"
    elif translator.gender == "F":
        return "Sehr geehrte Frau"
    else:
        return "Sehr geehrte*r Herr/Frau"
