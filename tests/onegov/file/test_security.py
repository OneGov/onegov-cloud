from onegov.core.utils import module_path
from onegov.file.security import sanitize_pdf


def test_sanitize_pdf():
    malicious = module_path('tests.onegov.file', '/fixtures/malicious.pdf')

    with open(malicious, 'rb') as f:
        assert b'JavaScript' in f.read()
        f.seek(0)

        sanitized = sanitize_pdf(f)

    with open(sanitized, 'rb') as f:
        assert b'JavaScript' not in f.read()
