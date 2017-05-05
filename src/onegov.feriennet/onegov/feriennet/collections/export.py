from onegov.feriennet import _


class ExportCollection(object):

    @property
    def exports(self):
        yield (
            'export-durchfuehrungen',
            _("Occasions Export"),
            _("Exports activities which have an occasion in the given period.")
        )
