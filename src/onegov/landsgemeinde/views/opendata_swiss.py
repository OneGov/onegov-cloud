from __future__ import annotations

from io import BytesIO
from onegov.core.security import Public
from onegov.landsgemeinde import _
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import Assembly
from onegov.org.models import Organisation
from sedate import as_datetime
from webob.exc import HTTPNotImplemented
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import SubElement


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.landsgemeinde.request import LandsgemeindeRequest
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


@LandsgemeindeApp.view(
    model=Organisation,
    name='catalog.rdf',
    permission=Public
)
def view_rdf(
    self: Organisation,
    request: LandsgemeindeRequest
) -> bytes:

    """ Returns an XML / RDF / DCAT-AP for Switzerland format for
    opendata.swiss.

    See https://handbook.opendata.swiss/de/content/glossar/bibliothek/
    dcat-ap-ch.html and https://dcat-ap.ch/ for more information.

    """

    publisher_mail = self.ogd_publisher_mail
    publisher_id = self.ogd_publisher_id
    publisher_name = self.ogd_publisher_name
    if not publisher_id or not publisher_name or not publisher_mail:
        raise HTTPNotImplemented()

    @request.after
    def set_headers(response: Response) -> None:
        response.headers['Content-Type'] = 'application/rdf+xml; charset=UTF-8'

    layout = DefaultLayout(self, request)

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
    items = session.query(Assembly).all()

    for item in sorted(items, key=lambda i: i.date, reverse=True):

        if item.state != 'completed':
            continue

        # IDs
        item_id = f'landsgemeinde-{item.date}'
        ds = sub(catalog, 'dcat:dataset')
        ds = sub(ds, 'dcat:Dataset', {
            'rdf:about': f'https://{publisher_id}/{item_id}'
        })
        sub(ds, 'dct:identifier', {}, f'{item_id}@{publisher_id}')

        # Dates
        sub(
            ds, 'dct:issued',
            {'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#dateTime'},
            as_datetime(item.date).isoformat()
        )
        last_modified = item.last_modified or as_datetime(item.date)
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
        sub(ds, 'dcat:landingPage', {'rdf:resource': request.link(item)})

        # Keywords
        keyword = request.translate(_('Assembly'))
        sub(ds, 'dcat:keyword', {'xml:lang': 'de'}, keyword)

        # Title
        title = request.translate(layout.assembly_title(item))
        sub(ds, 'dct:title', {'xml:lang': 'de'}, title)

        # Description
        description = request.translate(_(
            'Results from the ${title}, structured as json',
            mapping={'title': title}
        ))
        sub(ds, 'dct:description', {'xml:lang': 'de'}, description)

        # Format description
        # label = request.translate(_("Format Description"))
        # url = request.link(self, 'open-data')
        # fmt_des = sub(ds, 'dct:relation')
        # fmt_des = sub(fmt_des, 'rdf:Description', {'rdf:about': url})
        # sub(fmt_des, 'rdfs:label', {}, label)

        # Publisher
        pub = sub(ds, 'dct:publisher')
        pub = sub(pub, 'foaf:Organization', {
            'rdf:about': f'https://{publisher_id}'
        })
        sub(pub, 'foaf:name', {}, publisher_name)

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

        # Distribution
        dist = sub(ds, 'dcat:distribution')
        dist = sub(dist, 'dcat:Distribution', {
            'rdf:about': f'http://{publisher_id}/{item_id}/json'
        })
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
        url = request.link(item, 'json')
        sub(dist, 'dcat:accessURL', {'rdf:resource': url})
        sub(dist, 'dcat:downloadURL', {'rdf:resource': url})
        sub(dist, 'dct:license', {
            'rdf:resource': 'http://dcat-ap.ch/vocabulary/licenses/terms_by'
        })
        sub(dist, 'dcat:mediaType', {
            'rdf:resource': 'https://www.iana.org/assignments/media-types/'
            'application/json'
        })
        sub(dist, 'dcat:format', {
            'rdf:resource': 'http://publications.europa.eu/resource/'
            'authority/file-type/JSON'
        })

    out = BytesIO()
    ElementTree(rdf).write(out, encoding='utf-8', xml_declaration=True)
    return out.getvalue()
