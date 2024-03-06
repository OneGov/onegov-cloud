from collections import namedtuple
from io import BytesIO
from os.path import splitext, basename
from sqlalchemy import and_
from onegov.org.models import GeneralFileCollection, GeneralFile
from onegov.ticket import Ticket, TicketCollection
from onegov.translator_directory import _
from docxtpl import DocxTemplate, InlineImage


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.translator_directory.models.translator import Translator
    from onegov.core.request import CoreRequest


def fill_docx_with_variables(
    original_docx, t, request, signature_file=None, **kwargs
):
    """ Fills the variables in a docx file with the given key-value pairs.
      The original_docx template contains Jinja-Variables that map to keys
      in the template_variables dictionary.

    Returns A tuple containing two elements:
        - Variables that were found to be None or empty.
        - The rendered docx file (bytes).
    """

    docx_template = DocxTemplate(original_docx)
    template_variables = {
        'translator_last_name': t.last_name,
        'translator_first_name': t.first_name,
        'translator_nationality': t.nationality,
        'translator_address': t.address,
        'translator_city': t.city,
        'translator_zip_code': t.zip_code,
        'translator_occupation': t.occupation,
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
        'translator_functions': ', '.join(list(translator_functions(t))),
    }
    for key, value in kwargs.items():
        template_variables[key] = value or ''

    if signature_file:
        template_variables['sender_signature'] = FixedInplaceInlineImage(
            docx_template, signature_file
        )

    found_nulls = {k: v for k, v in template_variables.items() if not v}
    if found_nulls:
        non_null_values = {
            k: v for k, v in template_variables.items() if
            k not in found_nulls
        }
        return found_nulls, render_docx(docx_template, non_null_values)

    else:
        return {}, render_docx(docx_template, template_variables)


class FixedInplaceInlineImage(InlineImage):

    def _insert_image(self):
        pic = self.tpl.current_rendering_part.new_pic_inline(
            self.image_descriptor, self.width, self.height
        ).xml
        pic = self.fix_inline_image_alignment(pic)
        return (
            '</w:t></w:r><w:r><w:drawing>%s</w:drawing></w:r><w:r>'
            '<w:t xml:space="default">' % pic
        )

    def fix_inline_image_alignment(self, orig_xml):
        """ Fixes the position of the image by setting the `distL` to zero."""
        fix_pos = ' distT=\"0\" distB=\"0\" distL=\"0\" distR=\"0\"'
        index = orig_xml.find('wp:inline')
        if index != -1:
            return (
                orig_xml[: index + len('wp:inline')]
                + fix_pos
                + orig_xml[index + len('wp:inline'):]
            )
        else:
            return orig_xml


def render_docx(docx_template, template_variables):
    """ Creates the word file.

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


def get_hometown_or_city(
    translator: 'Translator', request: 'CoreRequest'
) -> str:
    """Returns the hometown. If it does not exist return the current city
    from address as a fallback.
    """
    translator_handler_data = TicketCollection(
        request.session
    ).by_handler_data_id(translator.id)
    hometown_query = translator_handler_data.with_entities(
        Ticket.handler_data['handler_data']['hometown']
    )
    return (hometown_query.first() or [translator.city])[0]


def get_ticket_nr_of_translator(
    translator: 'Translator', request: 'CoreRequest'
) -> str:
    query = TicketCollection(request.session).by_handler_data_id(
        translator.id
    )
    tickets = query.order_by(Ticket.last_state_change)
    if tickets.count() == 0:
        return "Kein Ticket"  # Very imporobable, but you never know
    return '/'.join(ticket.number for ticket in tickets)


def parse_from_filename(abs_signature_filename):
    """ Parses information from the filename. The delimiter is '__'.

     This is kind of implicit here, information about the user is stored in
     the filename of the signature image of the user.
    """
    filename, _ = splitext(basename(abs_signature_filename))
    filename = filename.replace('Unterschrift__', '')
    parts = filename.split('__')
    Signature = namedtuple(
        'Signature',
        ['sender_abbrev', 'sender_full_name', 'sender_function'],
    )
    return Signature(
        sender_abbrev=parts[0],
        sender_full_name=parts[1].replace('_', ' '),
        sender_function=parts[2].replace('_', ' ')
    )


def signature_for_mail_templates(request):
    """ The signature of the current user. It is an image that is manually
    uploaded. It should contain the string 'Unterschrift', as well as the
    first and last name of the user. """

    first_name, last_name = request.current_user.realname.split(' ')
    query = GeneralFileCollection(request.session).query().filter(
        and_(
            GeneralFile.name.like('Unterschrift%'),
            GeneralFile.name.like(f'%{first_name}%'),
            GeneralFile.name.like(f'%{last_name}%'),
        )
    )
    return query.first()
