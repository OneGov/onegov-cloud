from __future__ import annotations

from io import BytesIO
from os.path import splitext, basename
from sqlalchemy import and_
from onegov.org.models import GeneralFileCollection, GeneralFile
from onegov.ticket import Ticket, TicketCollection
from onegov.translator_directory import _
from onegov.translator_directory.utils import country_code_to_name
from docxtpl import DocxTemplate, InlineImage  # type:ignore[import-untyped]


from typing import Any, IO, NamedTuple, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.translator_directory.models.translator import Translator
    from onegov.translator_directory.request import TranslatorAppRequest


def fill_docx_with_variables(
    original_docx: IO[bytes],
    t: Translator,
    request: TranslatorAppRequest,
    signature_file: IO[bytes] | None = None,
    **kwargs: Any
) -> tuple[dict[str, Any], bytes]:
    """ Fills the variables in a docx file with the given key-value pairs.
      The original_docx template contains Jinja-Variables that map to keys
      in the template_variables dictionary.

    Returns A tuple containing two elements:
        - Variables that were found to be None or empty.
        - The rendered docx file (bytes).
    """

    mapping = country_code_to_name(request.locale)
    nationalities = ', '.join(mapping[n] for n in t.nationalities) if (
        t.nationalities) else ''

    docx_template = DocxTemplate(original_docx)
    template_variables = {
        'translator_last_name': t.last_name,
        'translator_first_name': t.first_name,
        'translator_nationalities': nationalities,
        'translator_address': t.address,
        'translator_city': t.city,
        'translator_zip_code': t.zip_code,
        'translator_occupation': t.occupation,
        'translator_languages': '\n'.join(
            request.translate(lang_type) + ': ' + ', '.join(
                str(language) for language in langs
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


class FixedInplaceInlineImage(InlineImage):  # type:ignore[misc]
    """ InlineImage adds images to .docx files, but additional tweaking
    was required for left margin alignment.

    We determined the precise values needed for alignment by manually aligning
    the image within a .docx file, saving the changes, and then comparing
    the updated document's XML with the previous version. """

    def _insert_image(self) -> str:
        pic = self.tpl.current_rendering_part.new_pic_inline(
            self.image_descriptor, self.width, self.height
        ).xml
        pic = self.fix_inline_image_alignment(pic)
        return (
            f'</w:t></w:r><w:r><w:drawing>{pic}</w:drawing></w:r><w:r>'
            '<w:t xml:space="default">'
        )

    def fix_inline_image_alignment(self, orig_xml: str) -> str:
        """ Fixes the position of the image by setting the `distL` to zero."""
        fix_pos = ' distT="0" distB="0" distL="0" distR="0"'
        index = orig_xml.find('wp:inline')
        if index != -1:
            return (
                orig_xml[: index + len('wp:inline')]
                + fix_pos
                + orig_xml[index + len('wp:inline'):]
            )
        else:
            return orig_xml


def render_docx(
    docx_template: DocxTemplate,
    template_variables: dict[str, Any]
) -> bytes:
    """ Creates the word file.

    template_variables: dictionary of values to find and replace in final
    word file. Values not present are simply ignored.
    """
    docx_template.render(template_variables)
    in_memory_docx = BytesIO()
    docx_template.save(in_memory_docx)
    return in_memory_docx.getvalue()


def translator_functions(translator: Translator) -> Iterator[str]:
    if translator.written_languages:
        yield 'Übersetzen'
    if translator.spoken_languages:
        yield 'Dolmetschen'
    if translator.monitoring_languages:
        yield 'Kommunikationsüberwachung'


def gendered_greeting(translator: Translator) -> str:
    if translator.gender == 'M':
        return 'Sehr geehrter Herr'
    elif translator.gender == 'F':
        return 'Sehr geehrte Frau'
    else:
        return 'Sehr geehrte*r Herr/Frau'


def get_ticket_nr_of_translator(
    translator: Translator,
    request: TranslatorAppRequest
) -> str:
    query = TicketCollection(request.session).by_handler_data_id(
        translator.id
    )
    query = query.order_by(Ticket.last_state_change)
    ticket_nrs = query.with_entities(Ticket.number)
    return '/'.join(ticket_nr for ticket_nr, in ticket_nrs) or 'Kein Ticket'


class Signature(NamedTuple):
    sender_abbrev: str
    sender_full_name: str
    sender_function: str


def parse_from_filename(abs_signature_filename: str) -> Signature:
    """ Parses information from the filename. The delimiter is '__'.

    This is kind of implicit here, information about the user is stored in
    the filename of the signature image of the user.
    """
    filename, _ = splitext(basename(abs_signature_filename))
    filename = filename.replace('Unterschrift__', '')
    parts = filename.split('__')
    return Signature(
        sender_abbrev=parts[0],
        sender_full_name=parts[1].replace('_', ' '),
        sender_function=parts[2].replace('_', ' ')
    )


def signature_for_mail_templates(
    request: TranslatorAppRequest
) -> GeneralFile | None:
    """ The signature of the current user. It is an image that is manually
    uploaded. It should contain the string 'Unterschrift', as well as the
    first and last name of the user. """

    assert request.current_user is not None
    assert request.current_user.realname is not None
    first_name, last_name = request.current_user.realname.split(' ')
    query = GeneralFileCollection(request.session).query().filter(
        and_(
            GeneralFile.name.like('Unterschrift%'),
            GeneralFile.name.like(f'%{first_name}%'),
            GeneralFile.name.like(f'%{last_name}%'),
        )
    )
    return query.first()
