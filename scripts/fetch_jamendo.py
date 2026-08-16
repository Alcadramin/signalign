import argparse
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.jamendo.com/v3.0/tracks/"
MIN_LYRIC_WORDS = 20


def license_slug(ccurl: str) -> str:
    match = re.search(r"licenses/([a-z-]+)/([\d.]+)", ccurl or "")
    if not match:
        return "unknown"
    return f"CC-{match.group(1).upper()}-{match.group(2)}"


def usable_track(track: dict, exclude_ids: set[str]) -> bool:
    if str(track.get("id")) in exclude_ids:
        return False
    if not track.get("audiodownload_allowed") or not track.get("audiodownload"):
        return False
    slug = license_slug(track.get("license_ccurl", ""))
    if not slug.startswith(("CC-BY-", "CC-BY-SA-")):
        return False
    if any(term in slug for term in ("-NC", "-ND")):
        return False
    lyrics = (track.get("lyrics") or "").strip()
    if len(lyrics.split()) < MIN_LYRIC_WORDS:
        return False
    return True


def fetch_page(client_id: str, offset: int, limit: int) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "format": "json",
            "limit": limit,
            "offset": offset,
            "vocalinstrumental": "vocal",
            "ccnc": "false",
            "ccnd": "false",
            "include": "lyrics licenses",
            "audioformat": "mp32",
        }
    )
    with urllib.request.urlopen(f"{API}?{params}", timeout=60) as response:
        payload = json.loads(response.read())
    headers = payload.get("headers", {})
    if headers.get("status") != "success":
        raise RuntimeError(f"jamendo api error: {headers}")
    return payload["results"]


def download(url: str, out_path: Path) -> None:
    with urllib.request.urlopen(url, timeout=300) as response:
        out_path.write_bytes(response.read())


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch CC-BY/BY-SA vocal tracks with lyrics from Jamendo")
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("data/jamendo_corpus"))
    parser.add_argument("--max-tracks", type=int, default=200)
    parser.add_argument("--exclude-ids", type=Path, default=Path("scripts/bench_track_ids.txt"))
    args = parser.parse_args()

    exclude_ids = set()
    if args.exclude_ids.exists():
        exclude_ids = set(args.exclude_ids.read_text().split())

    audio_dir = args.out_dir / "audio"
    lyrics_dir = args.out_dir / "lyrics"
    audio_dir.mkdir(parents=True, exist_ok=True)
    lyrics_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out_dir / "tracks.csv"

    seen = set()
    if manifest_path.exists():
        with open(manifest_path) as f:
            seen = {row["id"] for row in csv.DictReader(f)}
    else:
        manifest_path.write_text("id,artist,title,license,url\n")

    kept, offset = len(seen), 0
    while kept < args.max_tracks:
        page = fetch_page(args.client_id, offset, 200)
        if not page:
            break
        offset += len(page)
        for track in page:
            if kept >= args.max_tracks:
                break
            track_id = str(track["id"])
            if track_id in seen or not usable_track(track, exclude_ids):
                continue
            stem = f"jamendo_{track_id}"
            try:
                download(track["audiodownload"], audio_dir / f"{stem}.mp3")
            except Exception as error:
                print(f"skip {track_id}: download failed ({error})", flush=True)
                continue
            (lyrics_dir / f"{stem}.txt").write_text(track["lyrics"].strip() + "\n")
            with open(manifest_path, "a") as f:
                writer = csv.writer(f)
                writer.writerow([
                    track_id, track["artist_name"], track["name"],
                    license_slug(track["license_ccurl"]),
                    f"https://www.jamendo.com/track/{track_id}",
                ])
            seen.add(track_id)
            kept += 1
            print(f"[{kept}/{args.max_tracks}] {track['artist_name']} - {track['name']} ({license_slug(track['license_ccurl'])})", flush=True)
        time.sleep(1)

    print(f"done: {kept} tracks in {args.out_dir}")


if __name__ == "__main__":
    main()
