from fetch_jamendo import usable_track


def track(**overrides):
    base = {
        "id": "123",
        "name": "Song",
        "artist_name": "Artist",
        "audiodownload_allowed": True,
        "audiodownload": "https://x/dl.mp3",
        "license_ccurl": "http://creativecommons.org/licenses/by-sa/3.0/",
        "lyrics": " ".join(f"word{i}" for i in range(30)),
    }
    return {**base, **overrides}


def test_usable_track_accepts_by_sa_with_lyrics():
    assert usable_track(track(), exclude_ids=set()) is True


def test_usable_track_rejects_missing_lyrics():
    assert usable_track(track(lyrics=""), exclude_ids=set()) is False


def test_usable_track_rejects_nc_and_nd_licenses():
    nc = track(license_ccurl="http://creativecommons.org/licenses/by-nc-sa/3.0/")
    nd = track(license_ccurl="http://creativecommons.org/licenses/by-nd/3.0/")
    assert usable_track(nc, exclude_ids=set()) is False
    assert usable_track(nd, exclude_ids=set()) is False


def test_usable_track_rejects_download_forbidden():
    assert usable_track(track(audiodownload_allowed=False), exclude_ids=set()) is False


def test_usable_track_rejects_benchmark_tracks():
    assert usable_track(track(), exclude_ids={"123"}) is False


def test_usable_track_rejects_tiny_lyrics():
    assert usable_track(track(lyrics="la la"), exclude_ids=set()) is False
