""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
import multiprocessing

from concurrent.futures import ThreadPoolExecutor
from copy import copy
from onegov.core.orm import as_selectable
from onegov.core.orm.types import UTCDateTime, JSON
from onegov.core.upgrade import upgrade_task
from onegov.core.utils import normalize_for_url
from onegov.file import File, FileCollection
from onegov.file.attachments import get_svg_size_or_default, extract_pdf_info
from onegov.file.filters import WithPDFThumbnailFilter
from onegov.file.integration import DepotApp
from onegov.file.utils import content_type_from_fileobj
from onegov.file.utils import get_image_size
from onegov.file.utils import word_count
from PIL import Image
from sqlalchemy import Boolean, Column, Integer, Text, text, select
from sqlalchemy.orm import load_only
from sqlalchemy.orm.attributes import flag_modified


@upgrade_task('Add checksum column')
def add_checksum_column(context):
    context.operations.add_column(
        'files', Column('checksum', Text, nullable=True, index=True)
    )


@upgrade_task('Add image size 3')
def add_image_size(context):
    images = FileCollection(context.session, type='image')

    for image in images.query():
        if not hasattr(image.reference, 'size'):

            # potentially dangerous and might not work with other storage
            # providers, so don't reuse unless you are sure about the
            # consequences
            image.reference._thaw()

            if image.reference.content_type == 'image/svg+xml':
                image.reference.size = get_svg_size_or_default(
                    image.reference.file
                )
            else:
                image.reference.size = get_image_size(
                    Image.open(image.reference.file)
                )

                thumbnail_metadata = copy(image.reference.thumbnail_small)
                thumbnail_metadata['size'] = get_image_size(
                    Image.open(
                        context.app.bound_depot.get(
                            image.get_thumbnail_id(size='small')
                        )
                    )
                )

                image.reference.thumbnail_small = thumbnail_metadata

            flag_modified(image, 'reference')


@upgrade_task('Add files by type and name index')
def add_files_by_type_and_name_index(context):
    context.operations.create_index(
        'files_by_type_and_name', 'files', ['type', 'name'])


@upgrade_task('Migrate file metadata to JSONB')
def migrate_file_metadata_to_jsonb(context):
    context.session.execute("""
        ALTER TABLE files
        ALTER COLUMN reference
        TYPE JSONB USING reference::jsonb
    """)

    context.operations.drop_index('files_by_type_and_name')

    context.add_column_with_defaults(
        table='files',
        column=Column('order', Text, nullable=False),
        default=lambda r: normalize_for_url(r.name))

    context.operations.create_index(
        'files_by_type_and_order', 'files', ['type', 'order'])


@upgrade_task('Add thumbnails to PDFs')
def add_thumbnails_to_pdfs(context):

    if not isinstance(context.app, DepotApp):
        return False

    depot = context.request.app.bound_depot

    files = FileCollection(context.session).query()
    files = iter(files.filter(text(
        "files.reference->>'content_type' = 'application/pdf'"
    )))

    pdf_filter = WithPDFThumbnailFilter(
        'medium', size=(512, 512), format='png'
    )

    # make sure that all cores are used for ghostscript
    # each thread will keep one ghostscript process busy
    max_workers = multiprocessing.cpu_count()

    def chunks(size=max_workers):
        while True:
            chunk = []

            for n in range(size):
                pdf = next(files, None)

                if not pdf:
                    return

                chunk.append((pdf, depot.get(pdf.reference.file_id)))

            yield chunk

    for chunk in chunks():
        pdfs, contents = zip(*(chunk))

        with ThreadPoolExecutor(max_workers=max_workers) as e:
            results = zip(
                pdfs,
                e.map(pdf_filter.generate_thumbnail, contents)
            )

            for pdf, thumbnail in results:
                # potentially dangerous and might not work with other storage
                # providers, so don't reuse unless you are sure about the
                # consequences
                pdf.reference._thaw()

                pdf_filter.store_thumbnail(pdf.reference, thumbnail)

                flag_modified(pdf, 'reference')


@upgrade_task('Add publication dates')
def add_publication_dates(context):
    context.operations.add_column(
        'files', Column('publish_date', UTCDateTime, nullable=True))

    context.add_column_with_defaults(
        table='files',
        column=Column('published', Boolean, nullable=False),
        default=True)


@upgrade_task('Add signed property')
def add_signed_property(context):
    context.add_column_with_defaults(
        table='files',
        column=Column('signed', Boolean, nullable=False),
        default=False)


@upgrade_task('Reclassify office documents')
def reclassify_office_documents(context):
    if not isinstance(context.app, DepotApp):
        return False

    files = FileCollection(context.session).query()\
        .options(load_only('reference'))

    with context.stop_search_updates():
        for f in files.filter(File.name.op('~*')(r'^.*\.(docx|xlsx|pptx)$')):
            content_type = content_type_from_fileobj(f.reference.file)
            f._update_metadata(content_type=content_type)

        context.session.flush()


@upgrade_task('Add extract and pages column')
def add_extract_and_pages_column(context):
    context.operations.add_column(
        'files', Column('extract', Text, nullable=True))

    context.operations.add_column(
        'files', Column('pages', Integer, nullable=True))


@upgrade_task('Extract pdf text of existing files')
def extract_pdf_text_of_existing_files(context):
    pdfs = FileCollection(context.session).by_content_type('application/pdf')

    for pdf in pdfs:
        pdf.pages, pdf.extract = extract_pdf_info(pdf.reference.file)

        # potentially dangerous and might not work with other storage
        # providers, so don't reuse unless you are sure about the
        # consequences
        pdf.reference._thaw()
        pdf.reference['temporary-pages-count'] = pdf.pages

        flag_modified(pdf, 'reference')


@upgrade_task('Add signature_metadata column')
def add_signature_metadata_column(context):
    context.operations.add_column(
        'files', Column('signature_metadata', JSON, nullable=True))


@upgrade_task('Add stats column')
def add_stats_column(context):
    context.operations.add_column(
        'files', Column('stats', JSON, nullable=True))

    selectable = as_selectable("""
        SELECT
            id,   -- Text
            pages -- Integer
        FROM files
        WHERE reference->>'content_type' = 'application/pdf'
    """)

    pages = {
        f.id: f.pages for f in context.session.execute(
            select(selectable.c)
        )
    }

    pdfs = FileCollection(context.session).by_content_type('application/pdf')

    for pdf in pdfs:
        pdf.stats = {
            'pages': pdf.reference.pop('temporary-pages-count', pages[pdf.id]),
            'words': word_count(pdf.extract)
        }

    context.session.flush()
    context.operations.drop_column('files', 'pages')
