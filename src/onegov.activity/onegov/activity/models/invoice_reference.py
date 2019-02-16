import re
import secrets
import string

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.utils import chunks, hash_dictionary
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import backref, relationship, validates


KNOWN_SCHEMAS = {}

INVALID_REFERENCE_CHARS_EX = re.compile(r'[^Q0-9A-F]+')
REFERENCE_EX = re.compile(r'Q{1}[A-F0-9]{10}')


class InvoiceReference(Base, TimestampMixin):
    """ A reference pointing to an invoice. References are keys which are used
    outside the application. Usually a code used on an invoice to enter through
    online-banking.

    Each invoice may have multiple references pointing to it. Each refernce
    is however unique.

    There are multiple schemas for references. Each schema generates its own
    set of references using a Python class and some optional settings given
    by the user (say a specific bank's account number).

    Each schema may only reference an invoice once.

    Though each schema has its own set of references, the references-space
    is shared between all schemas. In other words, reference 'foo' of schema
    A would conflict with reference 'foo' of schema B.

    This is because we do not know which schema was used when we encounter
    a reference.

    In reality this should not be a problem as reference schemes provided
    by banks usually cover a very large space, so multiple schemas are expected
    to just generate random numbers until one is found that has not been used
    yet (which should almost always happen on the first try).

    """

    __tablename__ = 'invoice_references'

    #: the unique reference
    reference = Column(Text, primary_key=True)

    #: the referenced invoice
    invoice_id = Column(UUID, ForeignKey('invoices.id'), nullable=False)
    invoice = relationship(
        'Invoice', backref=backref(
            "references", cascade="all, delete-orphan"))

    #: the schema used to generate the invoice
    schema = Column(Text, nullable=False)

    #: groups schema name and its config to identify records created by a
    #: given schema and config
    bucket = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            'bucket', 'invoice_id', name='unique_bucket_invoice_id'),
    )

    @validates
    def validate_schema(self, field, value):

        if value not in KNOWN_SCHEMAS:
            raise ValueError(f'{value} is an unknown schema')

        return value

    @property
    def readable(self):
        """ Returns the human formatted variant of the reference. """

        return KNOWN_SCHEMAS[self.schema]().format(self.reference)


class Schema(object):
    """ Defines the methods that need to be implemented by schemas. Schemas
    should generate numbers and be able to format them.

    Schemas should never be deleted as we want to be able to display
    past schemas even if a certain schema is no longer in use.

    If a new schema comes along that replaces an old one in an incompatible
    way, the new schema should get a new name and should be added alongside
    the old one.

    """

    def __init_subclass__(cls, name, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.name = name
        KNOWN_SCHEMAS[cls.name] = cls

    def __init__(self, **config):
        """ Each schema may have a custom config. This is *only used for
        creation of references*. For other uses like formatting the config
        is not passed in.

        """
        for k, v in config.items():
            setattr(self, k, v)

        self.config = config

    @property
    def bucket(self):
        """ Generates a unique identifer for the current schema and config. """

        return self.render_bucket(self.name, self.config)

    @classmethod
    def render_bucket(cls, schema_name, schema_config=None):
        if schema_config:
            return f'{schema_name}-{hash_dictionary(schema_config)}'

        return schema_name

    def link(self, session, invoice, optimistic=False, flush=True):
        """ Creates a new :class:`InvoiceReference` for the given invoice.

        The returned invoice should have a unique reference, so the chance
        of ending up with a conflict error later down the line are slim.

        If the schema already has a linke to the invoice, we skip the
        creation.

        By default we check our constraints before we write to the database.
        To be faster in performance critical situation we can however also
        chose to be 'optimistic' and forego those checks. Due to the random
        nature of schema references this should usually work.

        The constraints are set on the database, so they will be enforced
        either way.

        Additionally we can forego the session.flush if we want to.

        """

        assert invoice.id, "the invoice id must be konwn"

        q = optimistic or session.query(InvoiceReference)

        # check if we are already linked
        if not optimistic:
            if q.filter_by(bucket=self.bucket, invoice_id=invoice.id).first():
                return

        # find an unused reference
        for i in range(0, 10):
            candidate = self.new()

            if not optimistic:
                if q.filter_by(reference=candidate).first():
                    continue

            break
        else:
            raise RuntimeError("No unique reference after 10 tries")

        reference = InvoiceReference(
            invoice_id=invoice.id,
            reference=candidate,
            schema=self.name,
            bucket=self.bucket,
        )

        session.add(reference)

        if flush:
            session.flush()

        return reference

    def new(self):
        """ Returns a new reference in the most compact way possible. """
        raise NotImplementedError()

    def format(self, reference):
        """ Turns the reference into something human-readable. """
        raise NotImplementedError()


class FeriennetSchema(Schema, name='feriennet-v1'):
    """ The default schema for customers without specific bank integrations.

    The generated reference is entered as a note when conducting the
    online-banking transaction.

    """

    def new(self):
        return f'q{secrets.token_hex(5)}'

    def format(self, reference):
        reference = reference.upper()

        return '-'.join((
            reference[:1],
            reference[1:6],
            reference[6:]
        ))

    def extract(self, text):
        """ Takes a bunch of text and tries to extract the feriennet-v1
        reference from it.

        """
        if text is None:
            return None

        text = text.replace('\n', '').strip()

        if not text:
            return None

        # ENTER A WORLD WITHOUT LOWERCASE
        text = text.upper()

        # replace all O-s (as in OMG) with 0.
        text = text.replace('O', '0')

        # normalize the text by removing all invalid characters.
        text = INVALID_REFERENCE_CHARS_EX.sub('', text)

        # try to fetch the reference
        match = REFERENCE_EX.search(text)

        if not match:
            return None

        return match.group().lower()


class ESRSchema(Schema, name='esr-v1'):
    """ The default schema for ESR by Postfinance. In it's default form it is
    random and requires no configuration.

    A ESR reference has 27 characters from 0-9. The first 26 characters can
    be chosen freely and the last character is the checksum.

    Some banks require that references have certain prefixes/suffixes, but
    Postfinance who defined the ESR standard does not.

    """

    def new(self):
        number = ''.join(secrets.choice(string.digits) for _ in range(0, 26))
        return number + self.checksum(number)

    def checksum(self, number):
        """ Generates the modulo 10 checksum as required by Postfinance. """

        table = (0, 9, 4, 6, 8, 2, 7, 1, 3, 5)
        carry = 0

        for n in number:
            carry = table[(carry + int(n)) % 10]

        return str((10 - carry) % 10)

    def format(self, reference):
        """ Takes an ESR reference and formats it in a human-readable way.

        This is mandated as follows by Postfinance:

        > Die Referenznummer ist rechtsbündig, in 5er-Blocks und einem
        > allfälligen Restblock zu platzieren. Vorlaufende Nullen können
        > unterdrückt werden.

        """

        reference = reference.lstrip('0')
        reference = reference.replace(' ', '')

        blocks = []

        for values in chunks(reversed(reference), n=5, fillvalue=''):
            blocks.append(''.join(reversed(values)))

        return ' '.join(reversed(blocks))


class RaiffeisenSchema(ESRSchema, name='raiffeisen-v1'):
    """ Customised ESR for Raiffeisen. """

    def new(self):
        ident = self.esr_identification_number.replace('-', '').strip()
        assert 3 <= len(ident) <= 7

        rest = 26 - len(ident)
        random = ''.join(secrets.choice(string.digits) for _ in range(0, rest))
        number = f'{self.esr_identification_number}{random}'

        return number + self.checksum(number)
