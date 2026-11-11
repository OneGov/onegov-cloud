from webtest import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


#: The start of a mp4 file, enough to be detected as video/mp4
MP4_HEADER = b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom'


def create_video(size: int = 4096) -> bytes:
    return MP4_HEADER + bytes(range(256)) * (size // 256)


def test_view_videos(client: Client) -> None:
    assert client.get('/videos', expect_errors=True).status_code == 403

    client.login_admin()

    videos_page = client.get('/videos')
    assert "Noch keine Videos hochgeladen" in videos_page

    # only videos which can be played by browsers are supported
    videos_page.form['file'] = [Upload('Test.txt', b'File content')]
    assert videos_page.form.submit(expect_errors=True).status_code == 415

    video = create_video()
    videos_page.form['file'] = [Upload('Film.mp4', video)]
    videos_page.form.submit()

    videos_page = client.get('/videos')
    assert "Noch keine Videos hochgeladen" not in videos_page
    assert "Film.mp4" in videos_page

    video_url = videos_page.pyquery('.video-container video').attr('src')
    assert '/storage/' in video_url

    # the video list for the editor
    videos = client.get('/videos/json').json
    assert len(videos) == 1
    assert videos[0]['videos'][0]['title'] == 'Film.mp4'
    assert videos[0]['videos'][0]['video'] == video_url

    # videos support range requests, which are required to seek and for
    # playback on iOS
    response = client.get(video_url)
    assert response.content_type == 'video/mp4'
    assert response.headers['Accept-Ranges'] == 'bytes'
    assert response.body == video

    response = client.get(video_url, headers={'Range': 'bytes=100-199'})
    assert response.status_code == 206
    assert response.headers['Content-Range'] == f'bytes 100-199/{len(video)}'
    assert response.body == video[100:200]

    response = client.get(video_url, headers={'Range': 'bytes=4000-'})
    assert response.status_code == 206
    assert response.body == video[4000:]

    # the menu links to the videos
    assert '/videos' in client.get('/').pyquery('a.videos').attr('href')


def test_upload_video_from_editor(client: Client) -> None:
    client.login_admin()

    editor = client.get('/topics/themen').click('Thema')
    form = editor.pyquery('form#main-form')
    upload_url = form.attr('data-video-upload-url')
    assert form.attr('data-video-list-url').endswith('/videos/json')

    result = client.post(upload_url, upload_files=[
        ('file', 'Film.mp4', create_video())
    ]).json
    assert result['filename'] == 'Film.mp4'
    assert '/storage/' in result['filelink']

    result = client.post(upload_url, upload_files=[
        ('file', 'Test.txt', b'File content')
    ]).json
    assert result['error'] is True

    # embedded videos are kept when saving a page
    editor.form['title'] = "Filme"
    editor.form['text'] = (
        '<p><video controls preload="metadata" src="/storage/abc" '
        'title="Film" onplay="alert(1)" autoplay></video></p>'
    )
    page = editor.form.submit().follow()

    video = page.pyquery('.page-text video')
    assert video.attr('src') == '/storage/abc'
    assert video.attr('controls') is not None
    assert video.attr('preload') == 'metadata'
    assert video.attr('onplay') is None
    assert video.attr('autoplay') is None
