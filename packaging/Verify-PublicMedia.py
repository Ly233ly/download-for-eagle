from __future__ import annotations

import argparse
import json
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/138.0 Safari/537.36"
)
APPLE_HLS = (
    "https://devstreaming-cdn.apple.com/videos/streaming/examples/"
    "img_bipbop_adv_example_fmp4/master.m3u8"
)


def fetch_json(url: str, referer: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Referer": referer},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def window_json(html: str, name: str) -> dict:
    marker = re.search(rf"window\.{re.escape(name)}\s*=\s*", html)
    if not marker:
        return {}
    try:
        value, _ = json.JSONDecoder().raw_decode(html[marker.end() :])
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def bilibili_dash(page_url: str) -> tuple[list[dict], list[dict]]:
    html = fetch_text(page_url)
    payload = window_json(html, "__playinfo__")
    dash = payload.get("data", {}).get("dash") if isinstance(payload, dict) else None
    if not isinstance(dash, dict):
        state = window_json(html, "__INITIAL_STATE__")
        video_data = state.get("videoData") or {} if state else {}
        bvid = str(video_data.get("bvid") or "")
        cid = str(video_data.get("cid") or "")
        if not bvid:
            match = re.search(r"/(BV[0-9A-Za-z]+)/?", page_url)
            bvid = match.group(1) if match else ""
        if bvid and not cid:
            view = fetch_json(
                "https://api.bilibili.com/x/web-interface/view?"
                + urllib.parse.urlencode({"bvid": bvid}),
                page_url,
            )
            pages = view.get("data", {}).get("pages") or []
            if pages:
                cid = str(pages[0].get("cid") or "")
        if not bvid or not cid:
            raise RuntimeError("Bilibili page metadata is incomplete")
        query = urllib.parse.urlencode(
            {"bvid": bvid, "cid": cid, "qn": 80, "fnval": 4048, "fnver": 0, "fourk": 1}
        )
        payload = fetch_json("https://api.bilibili.com/x/player/playurl?" + query, page_url)
        dash = payload.get("data", {}).get("dash")
    if not isinstance(dash, dict):
        raise RuntimeError("Public Bilibili playback is not DASH")
    videos = [item for item in dash.get("video", []) if isinstance(item, dict)]
    audios = [item for item in dash.get("audio", []) if isinstance(item, dict)]
    if not videos or not audios:
        raise RuntimeError("Public Bilibili DASH is missing video or audio")
    return videos, audios


def media_url(item: dict) -> str:
    candidates = [item.get("baseUrl"), item.get("base_url")]
    candidates.extend(item.get("backupUrl") or item.get("backup_url") or [])
    return next((str(value) for value in candidates if value), "")


def probe(ffprobe: Path, path: Path) -> dict:
    result = subprocess.run(
        [str(ffprobe), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=True,
    )
    payload = json.loads(result.stdout)
    return {
        "bytes": path.stat().st_size,
        "streamTypes": sorted(
            {str(item.get("codec_type")) for item in payload.get("streams", [])}
        ),
        "codecs": sorted(
            {str(item.get("codec_name")) for item in payload.get("streams", [])}
        ),
    }


def run_checked(command: list[str], timeout: int = 180) -> None:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip().splitlines()[-1:]
        raise RuntimeError("FFmpeg public-media sample failed: " + " ".join(detail))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify public non-DRM HLS and Bilibili DASH samples.")
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--ffprobe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument(
        "--bilibili",
        default="https://www.bilibili.com/video/BV19DkJYZEod/",
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    hls_output = args.output / "apple-hls-public-sample.mkv"
    run_checked(
        [
            str(args.ffmpeg), "-hide_banner", "-y", "-i", APPLE_HLS,
            "-t", "5", "-map", "0:v:0?", "-map", "0:a:0?", "-c", "copy", str(hls_output),
        ]
    )

    videos, audios = bilibili_dash(args.bilibili)
    video = max(videos, key=lambda item: int(item.get("bandwidth") or 0))
    audio = max(audios, key=lambda item: int(item.get("bandwidth") or 0))
    bili_output = args.output / "bilibili-public-dash-sample.mkv"
    headers = "Referer: https://www.bilibili.com/\r\n"
    run_checked(
        [
            str(args.ffmpeg), "-hide_banner", "-y", "-user_agent", USER_AGENT,
            "-headers", headers, "-i", media_url(video),
            "-user_agent", USER_AGENT, "-headers", headers, "-i", media_url(audio),
            "-t", "5", "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", str(bili_output),
        ]
    )

    evidence = {
        "appleHls": {"source": "Apple Developer HLS example", **probe(args.ffprobe, hls_output)},
        "bilibiliDash": {
            "sourcePage": args.bilibili,
            "videoRepresentations": len(videos),
            "audioRepresentations": len(audios),
            "selectedWidth": int(video.get("width") or 0),
            "selectedHeight": int(video.get("height") or 0),
            **probe(args.ffprobe, bili_output),
        },
    }
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
