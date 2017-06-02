""" Returns an XML / RDF / DCAT-AP for Switzerland format for opendata.swiss

See http://handbook.opendata.swiss/en/library/ch-dcat-ap for more information.

"""

from io import BytesIO
from onegov.ballot import Election
from onegov.ballot import Vote
from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.models import Principal
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import SubElement


def sub(parent, tag, attrib=None, text=None):
    element = SubElement(parent, tag, attrib=attrib or {})
    element.text = text or ''
    return element


@ElectionDayApp.view(model=Principal, permission=Public, name='catalog.rdf')
def view_rdf(self, request):

    @request.after
    def set_headers(response):
        response.headers['Content-Type'] = 'application/rdf+xml; charset=UTF-8'

    principal = request.app.principal
    domains = dict(principal.available_domains)

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
        ds = sub(catalog, 'dcat:dataset')
        ds = sub(ds, 'dcat:Dataset', {'rdf:about': item.id})
        sub(ds, 'dct:identifier', {}, '{}@{}'.format(item.id, principal.name))
        sub(
            ds, 'dct:issued',
            {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#dateTime'},
            item.created.isoformat()
        )
        sub(
            ds, 'dct:modified',
            {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#dateTime'},
            item.last_result_change.isoformat()
        )
        sub(
            ds, 'dct:accrualPeriodicity',
            {'rdf:resource': 'http://purl.org/cld/freq/completelyIrregular'}
        )
        sub(
            ds, 'dcat:theme',
            {'rdf:resource': 'http://opendata.swiss/themes/politics'}
        )
        sub(ds, 'dcat:landingPage', {}, request.link(item, 'data'))

        type_ = _("Election") if isinstance(item, Election) else _("vo")
        sub(ds, 'dcat:keyword', {'xml:lang': 'de'}, translate(type_, 'de_CH'))
        sub(ds, 'dcat:keyword', {'xml:lang': 'fr'}, translate(type_, 'fr_CH'))
        sub(ds, 'dcat:keyword', {'xml:lang': 'it'}, translate(type_, 'it_CH'))
        sub(ds, 'dcat:keyword', {'xml:lang': 'en'}, translate(type_, 'en'))

        domain = domains[item.domain]
        sub(ds, 'dcat:keyword', {'xml:lang': 'de'}, translate(domain, 'de_CH'))
        sub(ds, 'dcat:keyword', {'xml:lang': 'fr'}, translate(domain, 'fr_CH'))
        sub(ds, 'dcat:keyword', {'xml:lang': 'it'}, translate(domain, 'it_CH'))
        sub(ds, 'dcat:keyword', {'xml:lang': 'en'}, translate(domain, 'en'))

        for lang in ('de', 'fr', 'it', 'en'):
            title = item.title_translations.get('{}_CH'.format(lang))
            title = title or item.title
            sub(ds, 'dct:title', {'xml:lang': lang}, title)

        # Todo: add a generic description
        #  e.g. Abstimungsresultate der eidgenössischen Abstimmung "xxx"
        #  des Kantons St. Gallen
        des = _("Results")
        sub(ds, 'dct:description', {'xml:lang': 'en'}, translate(des, 'de_CH'))
        sub(ds, 'dct:description', {'xml:lang': 'fr'}, translate(des, 'fr_CH'))
        sub(ds, 'dct:description', {'xml:lang': 'it'}, translate(des, 'it_CH'))
        sub(ds, 'dct:description', {'xml:lang': 'en'}, translate(des, 'en'))

        pub = sub(ds, 'dct:publisher')
        pub = sub(pub, 'rdf:Description')
        sub(pub, 'rdfs:label', {}, principal.name)
        mail = sub(ds, 'dcat:contactPoint')
        mail = sub(mail, 'vcard:Organization')
        sub(mail, 'vcard:fn', {}, principal.name)
        # todo: Add email to instance
        sub(mail, 'vcard:hasEmail', {'rdf:resource': 'mailto:xxx@yyy.zzz'})

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

        for fmt, media_type in (
            ('csv', 'text/csv'),
            ('xlsx', ('application/vnd.openxmlformats-officedocument'
                      '.spreadsheetml.sheet')),
            ('json', 'application/json'),
        ):
            url = request.link(item, 'data-{}'.format(fmt))
            dist = sub(ds, 'dcat:distribution')
            dist = sub(dist, 'dcat:Distribution', {'rdf:about': url})

            sub(dist, 'dct:identifier', {}, url)
            sub(
                dist, 'dct:issued',
                {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#dateTime'},
                item.created.isoformat()
            )
            sub(
                dist, 'dct:modified',
                {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#dateTime'},
                item.last_result_change.isoformat()
            )
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
            sub(
                dist, 'dct:rights',
                {},
                'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired'
            )

            # todo: dct:license
            # todo: dcat:byteSize
            sub(dist, 'dcat:mediaType', {}, media_type)
            sub(dist, 'dcat:format', {}, fmt.upper())

    out = BytesIO()
    ElementTree(rdf).write(out, encoding='utf-8', xml_declaration=True)
    out.seek(0)
    return out.read()
