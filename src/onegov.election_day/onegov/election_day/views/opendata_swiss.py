from babel.dates import format_date
from datetime import datetime
from io import BytesIO
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import Vote
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Principal
from webob.exc import HTTPNotImplemented
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import SubElement


def sub(parent, tag, attrib=None, text=None):
    element = SubElement(parent, tag, attrib=attrib or {})
    element.text = text or ''
    return element


@ElectionDayApp.view(
    model=Principal,
    name='catalog.rdf',
    permission=Public
)
def view_rdf(self, request):

    """ Returns an XML / RDF / DCAT-AP for Switzerland format for
    opendata.swiss.

    See http://handbook.opendata.swiss/en/library/ch-dcat-ap for more
    information.

    """

    principal_name = request.app.principal.name
    publisher_id = self.open_data.get('id')
    publisher_name = self.open_data.get('name')
    publisher_mail = self.open_data.get('mail')
    if not publisher_id or not publisher_name or not publisher_mail:
        raise HTTPNotImplemented()

    @request.after
    def set_headers(response):
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
    items = session.query(Election).all()
    items.extend(session.query(ElectionCompound).all())
    items.extend(session.query(Vote).all())

    translations = request.app.translations

    def translate(text, locale):
        translator = translations.get(locale)
        if translator:
            return text.interpolate(translator.gettext(text))
        return text.interpolate(text)

    for item in sorted(items, key=lambda i: i.date, reverse=True):
        is_vote = isinstance(item, Vote)

        # IDs
        item_id = '{}-{}'.format('vote' if is_vote else 'election', item.id)
        ds = sub(catalog, 'dcat:dataset')
        ds = sub(ds, 'dcat:Dataset', {
            'rdf:about': 'http://{}/{}'.format(publisher_id, item_id)}
        )
        sub(ds, 'dct:identifier', {}, '{}@{}'.format(item_id, publisher_id))

        # Dates
        sub(
            ds, 'dct:issued',
            {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#dateTime'},
            datetime(
                item.date.year, item.date.month, item.date.day
            ).isoformat()
        )
        sub(
            ds, 'dct:modified',
            {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#dateTime'},
            item.last_modified.replace(microsecond=0).isoformat()
        )
        sub(
            ds, 'dct:accrualPeriodicity',
            {'rdf:resource': 'http://purl.org/cld/freq/completelyIrregular'}
        )

        # Theme
        sub(
            ds, 'dcat:theme',
            {'rdf:resource': 'http://opendata.swiss/themes/politics'}
        )

        # Landing page
        sub(ds, 'dcat:landingPage', {}, request.link(item, 'data'))

        # Keywords
        for keyword in (
            _("Vote") if is_vote else _("Election"),
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
                        "Final results of the cantonal vote \"${title}\", "
                        "${date}, ${principal}, "
                        "broken down by municipalities.",
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
                        "Final results of the federal vote \"${title}\", "
                        "${date}, ${principal}, "
                        "broken down by municipalities.",
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
                        "Final results of the cantonal election \"${title}\", "
                        "${date}, ${principal}, "
                        "broken down by candidates and municipalities.",
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
                elif item.domain == 'region':
                    des = _(
                        "Final results of the regional election \"${title}\", "
                        "${date}, ${principal}, "
                        "broken down by candidates and municipalities.",
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
                        "Final results of the federal election \"${title}\", "
                        "${date}, ${principal}, "
                        "broken down by candidates and municipalities.",
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
            des = translate(des, locale)
            sub(ds, 'dct:description', {'xml:lang': lang}, des)

        # Format description
        for locale, lang in locales.items():
            label = translate(_("Format Description"), locale)
            url = layout.get_opendata_link(lang)

            fmt_des = sub(ds, 'dct:relation')
            fmt_des = sub(fmt_des, 'rdf:Description', {'rdf:about': url})
            sub(fmt_des, 'rdfs:label', {}, label)

        # Publisher
        pub = sub(ds, 'dct:publisher')
        pub = sub(pub, 'rdf:Description')
        sub(pub, 'rdfs:label', {}, publisher_name)
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
        for fmt, media_type in (
            ('csv', 'text/csv'),
            ('json', 'application/json'),
        ):
            url = request.link(item, 'data-{}'.format(fmt))

            # IDs
            dist = sub(ds, 'dcat:distribution')
            dist = sub(dist, 'dcat:Distribution', {
                'rdf:about': 'http://{}/{}/{}'.format(
                    publisher_id, item_id, fmt
                )
            })
            sub(dist, 'dct:identifier', {}, fmt)

            # Title
            for locale, lang in locales.items():
                title = item.get_title(locale, default_locale) or item.id
                title = '{}.{}'.format(normalize_for_url(title), fmt)
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
                item.last_modified.replace(microsecond=0).isoformat()
            )

            # URLs
            sub(
                dist, 'dcat:accessURL',
                {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#anyURI'},
                url
            )
            sub(
                dist, 'dcat:downloadURL',
                {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#anyURI'},
                url
            )

            # Legal
            sub(
                dist, 'dct:rights',
                {},
                'NonCommercialAllowed-CommercialAllowed-ReferenceRequired'
            )

            # Media Type
            sub(dist, 'dcat:mediaType', {}, media_type)

    out = BytesIO()
    ElementTree(rdf).write(out, encoding='utf-8', xml_declaration=True)
    out.seek(0)
    return out.read()
