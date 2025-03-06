from __future__ import annotations

from babel.dates import format_date
from io import BytesIO
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import Principal
from onegov.election_day.models import Vote
from sedate import as_datetime
from webob.exc import HTTPNotImplemented
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import SubElement


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.request import ElectionDayRequest
    from translationstring import TranslationString
    from webob.response import Response


def sub(
    parent: Element,
    tag: str,
    attrib: dict[str, str] | None = None,
    text: str | None = None
) -> Element:

    element = SubElement(parent, tag, attrib=attrib or {})
    element.text = text or ''
    return element


@ElectionDayApp.view(
    model=Principal,
    name='catalog.rdf',
    permission=Public
)
def view_rdf(self: Principal, request: ElectionDayRequest) -> bytes:

    """ Returns an XML / RDF / DCAT-AP for Switzerland format for
    opendata.swiss.

    See https://handbook.opendata.swiss/de/content/glossar/bibliothek/
    dcat-ap-ch.html and https://dcat-ap.ch/ for more information.

    """

    principal_name = request.app.principal.name
    publisher_id = self.open_data.get('id')
    publisher_name = self.open_data.get('name')
    publisher_mail = self.open_data.get('mail')
    publisher_uri = self.open_data.get(
        'uri',
        f'urn:onegov_election_day:publisher:{publisher_id}'
    )
    if not publisher_id or not publisher_name or not publisher_mail:
        raise HTTPNotImplemented()

    @request.after
    def set_headers(response: Response) -> None:
        response.headers['Content-Type'] = 'application/rdf+xml; charset=UTF-8'

    layout = DefaultLayout(self, request)
    domains = dict(self.domains_election)
    domains.update(self.domains_vote)
    locales = {k: k[:2] for k in request.app.locales}
    default_locale = request.default_locale

    rdf = Element('rdf:RDF', attrib={
        'xmlns:dct': 'http://purl.org/dc/terms/',
        'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
        'xmlns:dcat': 'http://www.w3.org/ns/dcat#',
        'xmlns:foaf': 'http://xmlns.com/foaf/0.1/',
        'xmlns:xsd': 'http://www.w3.org/2001/XMLSchema#',
        'xmlns:rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'xmlns:rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'xmlns:vcard': 'http://www.w3.org/2006/vcard/ns#',
        'xmlns:odrs': 'http://schema.theodi.org/odrs#',
        'xmlns:schema': 'http://schema.org/',
    })
    catalog = sub(rdf, 'dcat:Catalog')

    session = request.session
    items: list[Election | ElectionCompound | Vote]
    items = session.query(Election).all()  # type:ignore[assignment]
    items.extend(session.query(ElectionCompound))
    items.extend(session.query(Vote))

    translations = request.app.translations

    def translate(text: TranslationString, locale: str) -> str:
        translator = translations.get(locale)
        if translator:
            return text.interpolate(translator.gettext(text))
        return text.interpolate(text)

    for item in sorted(items, key=lambda i: i.date, reverse=True):

        if not item.completed:
            continue

        is_vote = isinstance(item, Vote)

        # IDs
        item_id = '{}-{}'.format('vote' if is_vote else 'election', item.id)
        ds = sub(catalog, 'dcat:dataset')
        ds = sub(ds, 'dcat:Dataset', {
            'rdf:about': f'http://{publisher_id}/{item_id}'
        })
        sub(ds, 'dct:identifier', {}, f'{item_id}@{publisher_id}')

        # Dates
        sub(
            ds, 'dct:issued',
            {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#dateTime'},
            as_datetime(item.date).isoformat()
        )
        last_modified = item.last_modified or as_datetime(item.date)
        assert last_modified is not None
        sub(
            ds, 'dct:modified',
            {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#dateTime'},
            last_modified.replace(microsecond=0).isoformat()
        )
        sub(
            ds, 'dct:accrualPeriodicity',
            {'rdf:resource': 'http://publications.europa.eu/resource/'
             'authority/frequency/IRREG'}
        )

        # Theme
        sub(
            ds, 'dcat:theme',
            {'rdf:resource': 'http://publications.europa.eu/resource/'
             'authority/data-theme/GOVE'}
        )

        # Landing page
        sub(
            ds, 'dcat:landingPage',
            {'rdf:resource': request.link(item, 'data')}
        )

        # Keywords
        for keyword in (
            _('Vote') if is_vote else _('Election'),
            domains[item.domain]
        ):
            for locale, lang in locales.items():
                value = translate(keyword, locale).lower()
                sub(ds, 'dcat:keyword', {'xml:lang': lang}, value)

        # Title
        for locale, lang in locales.items():
            title = item.get_title(locale, default_locale) or ''
            sub(ds, 'dct:title', {'xml:lang': lang}, title)

        # Description
        for locale, lang in locales.items():
            locale = locale
            if is_vote:
                if item.domain == 'canton':
                    des = _(
                        'Final results of the cantonal vote "${title}", '
                        '${date}, ${principal}, '
                        'broken down by municipalities.',
                        mapping={
                            'title': (
                                item.get_title(locale, default_locale) or ''
                            ),
                            'date': format_date(
                                item.date, format='long', locale=locale
                            ),
                            'principal': principal_name
                        }
                    )
                else:
                    des = _(
                        'Final results of the federal vote "${title}", '
                        '${date}, ${principal}, '
                        'broken down by municipalities.',
                        mapping={
                            'title': (
                                item.get_title(locale, default_locale) or ''
                            ),
                            'date': format_date(
                                item.date, format='long', locale=locale
                            ),
                            'principal': principal_name
                        }
                    )
            else:
                if item.domain == 'canton':
                    des = _(
                        'Final results of the cantonal election "${title}", '
                        '${date}, ${principal}, '
                        'broken down by candidates and municipalities.',
                        mapping={
                            'title': (
                                item.get_title(locale, default_locale) or ''
                            ),
                            'date': format_date(
                                item.date, format='long', locale=locale
                            ),
                            'principal': principal_name
                        }
                    )
                elif item.domain in ('region', 'district', 'none'):
                    des = _(
                        'Final results of the regional election "${title}", '
                        '${date}, ${principal}, '
                        'broken down by candidates and municipalities.',
                        mapping={
                            'title': (
                                item.get_title(locale, default_locale) or ''
                            ),
                            'date': format_date(
                                item.date, format='long', locale=locale
                            ),
                            'principal': principal_name
                        }
                    )
                else:
                    des = _(
                        'Final results of the federal election "${title}", '
                        '${date}, ${principal}, '
                        'broken down by candidates and municipalities.',
                        mapping={
                            'title': (
                                item.get_title(locale, default_locale) or ''
                            ),
                            'date': format_date(
                                item.date, format='long', locale=locale
                            ),
                            'principal': principal_name
                        }
                    )
            translated_des = translate(des, locale)
            sub(ds, 'dct:description', {'xml:lang': lang}, translated_des)

        # Format description
        for locale, lang in locales.items():
            label = translate(_('Format Description'), locale)
            url = layout.get_opendata_link(lang)

            fmt_des = sub(ds, 'dct:relation')
            fmt_des = sub(fmt_des, 'rdf:Description', {'rdf:about': url})
            sub(fmt_des, 'rdfs:label', {}, label)

        # Publisher
        pub = sub(ds, 'dct:publisher')
        pub = sub(pub, 'foaf:Organization', {
            'rdf:about': publisher_uri
        })
        sub(pub, 'foaf:name', {}, publisher_name)
        sub(pub, 'foaf:mbox', {
            'rdf:resource': 'mailto:{}'.format(publisher_mail)
        })

        #  Contact point
        mail = sub(ds, 'dcat:contactPoint')
        mail = sub(mail, 'vcard:Organization')
        sub(mail, 'vcard:fn', {}, publisher_name)
        sub(mail, 'vcard:hasEmail', {
            'rdf:resource': 'mailto:{}'.format(publisher_mail)
        })

        # Date
        date = sub(ds, 'dct:temporal')
        date = sub(date, 'dct:PeriodOfTime')
        sub(
            date, 'schema:startDate',
            {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#date'},
            item.date.isoformat()
        )
        sub(
            date, 'schema:endDate',
            {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#date'},
            item.date.isoformat()
        )

        # Distributions
        for fmt, extension, media_type, party_result in (
            ('csv', 'csv', 'text/csv', False),
            ('json', 'json', 'application/json', False),
            ('parties-csv', 'csv', 'text/csv', True),
            ('parties-json', 'json', 'application/json', True),
        ):
            if party_result:
                if not getattr(item, 'has_party_results', False):
                    continue

            url = request.link(item, f'data-{fmt}')

            # IDs
            dist = sub(ds, 'dcat:distribution')
            dist = sub(dist, 'dcat:Distribution', {
                'rdf:about': f'http://{publisher_id}/{item_id}/{fmt}'
            })
            sub(dist, 'dct:identifier', {}, fmt)

            # Title
            for locale, lang in locales.items():
                title = item.get_title(locale, default_locale) or item.id
                if party_result:
                    title += ' ({})'.format(translate(_('Parties'), locale))
                title = f'{normalize_for_url(title)}.{extension}'
                sub(dist, 'dct:title', {'xml:lang': lang}, title)

            # Dates
            sub(
                dist, 'dct:issued',
                {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#dateTime'},
                item.created.replace(microsecond=0).isoformat()
            )
            sub(
                dist, 'dct:modified',
                {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#dateTime'},
                last_modified.replace(microsecond=0).isoformat()
            )

            # URLs
            sub(dist, 'dcat:accessURL', {'rdf:resource': url})
            sub(dist, 'dcat:downloadURL', {'rdf:resource': url})

            # Legal
            sub(dist, 'dct:license', {
                'rdf:resource': 'http://dcat-ap.ch/vocabulary/licenses/terms_by'
            })

            # Media Type
            sub(dist, 'dcat:mediaType', {}, media_type)
            sub(dist, 'dcat:mediaType', {
                'rdf:resource': f'https://www.iana.org/assignments/'
                f'media-types/{media_type}'
            })
            sub(dist, 'dcat:format', {
                'rdf:resource': f'http://publications.europa.eu/resource/'
                f'authority/file-type/{extension.upper()}'
            })

    out = BytesIO()
    ElementTree(rdf).write(out, encoding='utf-8', xml_declaration=True)
    return out.getvalue()
