""" Returns an XML / RDF / DCAT-AP for Switzerland format for opendata.swiss

See http://handbook.opendata.swiss/en/library/ch-dcat-ap for more information.

"""

from io import BytesIO
from onegov.ballot import Election
from onegov.ballot import Vote
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import Layout
from onegov.election_day.models import Principal
from webob.exc import HTTPNotImplemented
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import SubElement


def sub(parent, tag, attrib=None, text=None):
    element = SubElement(parent, tag, attrib=attrib or {})
    element.text = text or ''
    return element


@ElectionDayApp.view(model=Principal, permission=Public, name='catalog.rdf')
def view_rdf(self, request):

    publisher_id = self.open_data.get('id')
    publisher_name = self.open_data.get('name')
    publisher_mail = self.open_data.get('mail')
    if not publisher_id or not publisher_name or not publisher_mail:
        raise HTTPNotImplemented()

    @request.after
    def set_headers(response):
        response.headers['Content-Type'] = 'application/rdf+xml; charset=UTF-8'

    layout = Layout(self, request)
    domains = dict(self.available_domains)

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

    session = request.app.session()
    items = session.query(Election).all()
    items.extend(session.query(Vote).all())

    translations = request.app.translations

    def translate(text, locale):
        translator = translations.get(locale)
        if translator:
            return text.interpolate(translator.gettext(text))
        return text.interpolate(text)

    for item in items:
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
            item.created.replace(microsecond=0).isoformat()
        )
        sub(
            ds, 'dct:modified',
            {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#dateTime'},
            item.last_result_change.replace(microsecond=0).isoformat()
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
            for lang in ('de', 'fr', 'it', 'en'):
                value = translate(keyword, '{}_CH'.format(lang)).lower()
                sub(ds, 'dcat:keyword', {'xml:lang': lang}, value)

        # Title
        for lang in ('de', 'fr', 'it', 'en'):
            title = item.title_translations.get('{}_CH'.format(lang))
            title = title or item.title
            sub(ds, 'dct:title', {'xml:lang': lang}, title)

        # Description
        # Todo: Add a more generic description?
        #  Schlussresultat der kantonalen Abstimmung "XXX" vom 1.1.2000,
        #    Kanton Zug.
        des = _("Results")
        sub(ds, 'dct:description', {'xml:lang': 'en'}, translate(des, 'de_CH'))
        sub(ds, 'dct:description', {'xml:lang': 'fr'}, translate(des, 'fr_CH'))
        sub(ds, 'dct:description', {'xml:lang': 'it'}, translate(des, 'it_CH'))
        sub(ds, 'dct:description', {'xml:lang': 'en'}, translate(des, 'en'))

        # Format description
        for lang in ('de', 'fr', 'it', 'en'):
            label = translate(_("Format Description"), '{}_CH'.format(lang))
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
            ('xlsx', ('application/vnd.openxmlformats-officedocument'
                      '.spreadsheetml.sheet')),
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
            for lang in ('de', 'fr', 'it', 'en'):
                title = item.title_translations.get('{}_CH'.format(lang))
                title = title or item.title
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
                item.last_result_change.replace(microsecond=0).isoformat()
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
                'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired'
            )

            # Media Type
            sub(dist, 'dcat:mediaType', {}, media_type)

    out = BytesIO()
    ElementTree(rdf).write(out, encoding='utf-8', xml_declaration=True)
    out.seek(0)
    return out.read()
