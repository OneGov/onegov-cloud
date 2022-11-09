from base64 import b64encode
import requests


class GeverClient:

    def __init__(self, username, password):
        self.password = username
        self.username = password
        self.session = requests.Session()

    def upload_file(self, file: bytes, filename, endpoint):

        def _base64_str(s):
            if not isinstance(s, bytes):
                s = s.encode("utf-8")
            s = b64encode(s)
            if not isinstance(s, str):
                s = s.decode("utf-8")
            return s

        def _prepare_metadata(filename, content_type, _type=None):
            return "filename {},content-type {}{}".format(
                _base64_str(filename),
                _base64_str(content_type),
                ", @type " + _base64_str(_type) if _type else "",
            )

        file_size = len(file)
        if not isinstance(file, bytes) or file_size == 0:
            raise ValueError(f"Invalid Argument: {type(file)}")

        metadata = _prepare_metadata(
            filename, "application/pdf", "opengever.document.document"
        )

        headers = {
            "Accept": "application/json",
            "Tus-Resumable": "1.0.0",
            "Upload-Length": str(file_size),
            "Upload-Metadata": metadata,
        }
        last_char = endpoint[-1]
        endpoint += "@tus-upload" if last_char == "/" else "/@tus-upload"
        resp = self.request_with_basic_auth(
            "POST", endpoint, headers=headers
        )

        if not (resp.status_code == 201 and "Location" in resp.headers.keys()):
            return resp  # fail early

        # The server will return a temporary upload URL 'location' in header
        location = resp.headers["Location"]
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/offset+octet-stream",
            "Upload-Offset": "0",
            "Tus-Resumable": "1.0.0",
        }

        resp = self.request_with_basic_auth(
            "PATCH", location, headers=headers, data=file
        )
        return resp

    def request_with_basic_auth(self, method, url, **kwargs):
        self.session.auth = (self.username, self.password)
        response = self.session.request(method, url, **kwargs)
        return response
