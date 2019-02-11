from cached_property import cached_property
from decimal import Decimal
from onegov.activity.models import Invoice, InvoiceItem
from onegov.activity.models.invoice_reference import KNOWN_SCHEMAS
from onegov.core.collection import GenericCollection
from sqlalchemy import func, and_, not_
from onegov.user import User
from uuid import uuid4


class InvoiceCollection(GenericCollection):

    def __init__(self, session, period_id=None, user_id=None,
                 schema='feriennet-v1', schema_config=None):
        super().__init__(session)
        self.user_id = user_id
        self.period_id = period_id

        if schema not in KNOWN_SCHEMAS:
            raise RuntimeError("Unknown schema: {schema}")

        self.schema_name = schema
        self.schema_config = (schema_config or {})

    @cached_property
    def schema(self):
        return KNOWN_SCHEMAS[self.schema_name](**self.schema_config)

    def query(self):
        q = super().query()

        if self.user_id:
            q = q.filter_by(user_id=self.user_id)

        if self.period_id is not None:
            q = q.filter_by(period_id=self.period_id)

        return q

    def query_items(self):
        return self.session.query(InvoiceItem)\
            .filter(InvoiceItem.invoice_id.in_(
                self.query().with_entities(Invoice.id).subquery()
            ))

    def for_user_id(self, user_id):
        return self.__class__(self.session, self.period_id, user_id,
                              self.schema_name, self.schema_config)

    def for_period_id(self, period_id):
        return self.__class__(self.session, period_id, self.user_id,
                              self.schema_name, self.schema_config)

    def for_schema(self, schema, schema_config=None):
        return self.__class__(self.session, self.period_id, self.user_id,
                              schema, schema_config)

    @cached_property
    def invoice(self):
        # XXX used for compatibility with legacy implementation in Feriennet
        return self.period_id and self.period_id.hex or None

    @cached_property
    def username(self):
        # XXX used for compatibility with legacy implementation in Feriennet
        if self.user_id:
            user = self.session.query(User)\
                .with_entities(User.username)\
                .filter_by(id=self.user_id)\
                .first()

            return user and user.username or None

    @property
    def model_class(self):
        return Invoice

    def _invoice_ids(self):
        return self.query().with_entities(Invoice.id).subquery()

    def _sum(self, condition):
        q = self.session.query(func.sum(InvoiceItem.amount).label('amount'))
        q = q.filter(condition)

        return Decimal(q.scalar() or 0.0)

    @property
    def total_amount(self):
        return self._sum(InvoiceItem.invoice_id.in_(self._invoice_ids()))

    @property
    def outstanding_amount(self):
        return self._sum(and_(
            InvoiceItem.invoice_id.in_(self._invoice_ids()),
            InvoiceItem.paid == False
        ))

    @property
    def paid_amount(self):
        return self._sum(and_(
            InvoiceItem.invoice_id.in_(self._invoice_ids()),
            InvoiceItem.paid == True
        ))

    def unpaid_count(self, excluded_period_ids=None):
        q = self.query().with_entities(func.count(Invoice.id))

        if excluded_period_ids:
            q = q.filter(not_(Invoice.period_id.in_(excluded_period_ids)))

        q = q.filter(Invoice.paid == False)

        return q.scalar() or 0

    def sync(self):
        for invoice in self.query():
            invoice.sync()

    def add(self, period_id=None, user_id=None, code=None):
        invoice = Invoice(
            id=uuid4(),
            period_id=period_id or self.period_id,
            user_id=user_id or self.user_id)

        # deprecated -> remove in Feriennet 1.6
        if code is not None:
            invoice.code = code

        self.session.add(invoice)
        self.schema.link(self.session, invoice)
        self.session.flush()

        return invoice
