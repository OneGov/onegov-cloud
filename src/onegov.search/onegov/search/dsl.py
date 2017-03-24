from elasticsearch_dsl import Search as BaseSearch
from elasticsearch_dsl.response import Hit as BaseHit
from elasticsearch_dsl.response import Response as BaseResponse


class Search(BaseSearch):
    """ Extends elastichsearch_dsl's search object with ORM integration.

    Works exactly the same as the original, but the results it returns offer
    additional methods to query the SQLAlchemy models behind the results (if
    any).

    """

    def __init__(self, *args, **kwargs):

        # get the session and mapping if possilbe (not provided during cloning)
        self.session = kwargs.pop('session', None)
        self.mappings = kwargs.pop('mappings', None)

        super().__init__(*args, **kwargs)

        assert not self._doc_type_map

        # use the mappings to build the doc type map which elasticsearch_dsl
        # uses for their own models - since we don't use them, we can hijack
        # that map. When cloning, this map will be cloned as well.
        if self.mappings:
            for mapping in self.mappings:
                if not mapping.model:
                    continue

                if mapping.name not in self._doc_type_map:
                    self._doc_type_map[mapping.name] = Hit.bind(
                        mapping.model, self.session
                    )

        # bind responses to the orm
        self._response_class = Response.bind(
            self.session, self.mappings, self.explain)

    @property
    def explain(self):
        return self._extra.get('explain', False)

    def _clone(self):
        search = super()._clone()
        search.session = self.session
        search.mappings = self.mappings

        return search


class Response(BaseResponse):
    """ Extends the default response (list of results) with additional
    methods to query the SQLAlchemy models behind the results.

    """

    @classmethod
    def bind(cls, session, mappings, explain):

        class BoundResponse(cls):
            pass

        BoundResponse.session = session
        BoundResponse.mappings = mappings
        BoundResponse.explain = explain

        return BoundResponse

    def hits_by_type(self, type):
        for hit in self.hits:
            if hit.meta.doc_type == type:
                yield hit

    def query(self, type):
        """ Returns an SQLAlchemy query for the given type. You must provide
        a type, because a query can't consist of multiple unrelated tables.

        If no results match the type, None is returned.

        """
        hits = list(self.hits_by_type(type))

        if not hits:
            return None

        model = self.mappings[type].model
        query = self.session.query(model)

        model_ids = (h.meta.id for h in hits)
        query = query.filter(getattr(model, model.es_id).in_(model_ids))

        return query

    def load(self):
        """ Loads all results by querying the SQLAlchemy session in the order
        they were returned by elasticsearch.

        """

        positions = {}
        types = set()

        # put the types into buckets and store the original position...
        for ix, hit in enumerate(self.hits):
            type = hit.meta.doc_type
            positions[(type, str(hit.meta.id))] = ix
            types.add(type)

        results = [None] * len(positions)

        # ...so we can query the database once per type and not once per result
        # this has the potential of resulting in fewer queries
        for type in types:
            for result in self.query(type).all():
                object_id = str(getattr(result, result.es_id))
                ix = positions[(type, object_id)]

                if self.explain:

                    ex = self.hits[ix].meta.explanation

                    result.explanation = {
                        'raw': ex.__dict__,
                        'score': self.hits[ix].meta.score,
                        'term-frequency': explanation_value(
                            ex, 'termFreq'
                        ),
                        'inverse-document-frequency': explanation_value(
                            ex, 'idf'
                        ),
                        'field-norm': explanation_value(
                            ex, 'fieldNorm'
                        )
                    }

                results[ix] = result

        return results


def explanation_value(explanation, text):
    """ Gets the value from the explanation for descriptions starting with
    the given text.

    """

    if explanation.description.startswith(text):
        return {
            'description': explanation.description,
            'value': explanation.value
        }

    for detail in getattr(explanation, 'details', []):
        result = explanation_value(detail, text)

        if result:
            return result


class Hit(BaseHit):
    """ Extends a single result with additional methods to query the SQLAlchemy
    models behind the results.

    """

    @classmethod
    def bind(cls, model, session):

        class BoundHit(cls):
            pass

        BoundHit.model = model
        BoundHit.session = session

        return BoundHit

    def query(self):
        """ Returns the SQLAlchemy query for this result. """
        query = self.session.query(self.model)
        model_id = getattr(self.model, self.model.es_id)
        query = query.filter(model_id == self.meta.id)

        return query

    def load(self):
        """ Loads this result from the SQLAlchemy session. """
        return self.query().one()
