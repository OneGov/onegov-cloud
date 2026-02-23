from __future__ import annotations

ALLOWED_MIME_TYPES = {
    'application/excel',
    'application/vnd.ms-excel',
    'text/plain',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-office',
    'application/octet-stream',
    'application/zip',
    'text/csv'
}
ALLOWED_MIME_TYPES_XML = {
    'application/xml',  # official, standard
    'text/xml',  # deprecated MIME type for XML content
    'text/plain'
}


MAX_FILE_SIZE = 10 * 1024 * 1024
