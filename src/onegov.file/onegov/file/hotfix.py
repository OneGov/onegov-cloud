import pkg_resources

from depot.fields.sqlalchemy import _SQLAMutationTracker, UploadedFileField
from sqlalchemy import event
from sqlalchemy.orm import ColumnProperty, mapper


@event.listens_for(mapper, 'before_configured')
def receive_before_configured():

    # XXX temporary fix for https://github.com/amol-/depot/issues/33
    version = pkg_resources.get_distribution('filedepot').version
    whitelisted = ('0.3.0', '0.3.1', '0.4.0')

    assert version in whitelisted

    # only apply the patch if the mutation tracker is online
    original_handler = _SQLAMutationTracker._mapper_configured

    if not event.contains(mapper, 'mapper_configured', original_handler):
        return

    # use a new, fixed mutation tracker
    event.remove(mapper, 'mapper_configured', original_handler)

    @event.listens_for(mapper, 'mapper_configured')
    def patched_mapper_configured_handler(mapper, class_):
        for mapper_property in mapper.iterate_properties:
            if isinstance(mapper_property, ColumnProperty):
                for idx, col in enumerate(mapper_property.columns):
                    if isinstance(col.type, UploadedFileField):
                        if idx > 0:
                            raise TypeError(
                                'UploadedFileField currently supports a '
                                'single column'
                            )
                        _SQLAMutationTracker.mapped_entities.setdefault(
                            class_, []).append(mapper_property.key)
                        event.listen(
                            mapper_property, 'set',
                            _SQLAMutationTracker._field_set,
                            retval=True, propagate=True
                        )
