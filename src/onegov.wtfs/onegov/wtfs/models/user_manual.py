class UserManual(object):

    def __init__(self, app):
        self.app = app
        self.filename = 'user_manual.pdf'
        self.content_type = 'application/pdf'

    @property
    def exists(self):
        return self.app.filestorage.exists(self.filename)

    @property
    def pdf(self):
        if self.exists:
            with self.app.filestorage.open(self.filename, 'rb') as file:
                result = file.read()
            return result

    @pdf.setter
    def pdf(self, value):
        with self.app.filestorage.open(self.filename, 'wb') as file:
            file.write(value)

    @pdf.deleter
    def pdf(self):
        if self.exists:
            self.app.filestorage.remove(self.filename)

    @property
    def content_length(self):
        if self.exists:
            return self.app.filestorage.getsize(self.filename)
