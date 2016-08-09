
def add_last_modified_header(response, last_modified):
    if last_modified:
        response.headers.add(
            'Last-Modified',
            last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
        )
