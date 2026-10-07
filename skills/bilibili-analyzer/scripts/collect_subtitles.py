#!/usr/bin/env python3
"""Collect timed subtitle evidence without third-party Python dependencies."""
import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def seconds(value):
    if isinstance(value, str):
        value = value.strip().rstrip("s").replace(",", ".")
        if ":" in value:
            result = 0.0
            for piece in value.split(":"):
                result = result * 60 + float(piece)
            return result
    return float(value)


def normalize(payload):
    rows = payload if isinstance(payload, list) else payload.get("body", payload.get("segments", []))
    if not isinstance(rows, list) or not rows:
        raise ValueError("Subtitle body is empty or invalid")
    output = []
    for row in rows:
        start = seconds(row.get("from", row.get("start")))
        end = seconds(row.get("to", row.get("end")))
        content = str(row.get("content", row.get("text", ""))).strip()
        if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start or not content:
            raise ValueError("Invalid subtitle interval or empty text")
        output.append({"from": start, "to": end, "content": content})
    output.sort(key=lambda row: (row["from"], row["to"]))
    return [{"index": i, **row} for i, row in enumerate(output, 1)]


def parse_srt(text):
    rows = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip()):
        lines = block.splitlines()
        for i, line in enumerate(lines):
            if "-->" in line:
                start, end = line.split("-->", 1)
                rows.append({"from": start.strip(), "to": end.strip().split()[0],
                             "content": "\n".join(lines[i + 1:])})
                break
        else:
            raise ValueError("Invalid SRT block")
    return rows


def stamp(value):
    ms = round(value * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02}.{ms % 1000:03}"


def get_json(url, headers, params=None):
    if params:
        url += "?" + urlencode(params)
    with urlopen(Request(url, headers=headers), timeout=15) as response:
        return json.load(response)


def api(path, headers, **params):
    payload = get_json("https://api.bilibili.com" + path, headers, params)
    if payload.get("code") != 0:
        raise ValueError(f"API code {payload.get('code')}")
    return payload["data"]


def fetch(args, report):
    headers = {"User-Agent": "Mozilla/5.0", "Referer": args.url}
    if args.cookie_file:
        headers["Cookie"] = Path(args.cookie_file).read_text(encoding="utf-8-sig").strip()
    info = api("/x/web-interface/view", headers, bvid=report["bvid"])
    pages = [p for p in info["pages"] if p["page"] == report["page"]]
    if len(pages) != 1:
        raise ValueError("Requested part does not exist")
    page = pages[0]
    if args.cid is not None and args.cid != page["cid"]:
        raise ValueError("CID does not match requested part")
    report.update(cid=page["cid"], title=info["title"], part=page["part"],
                  duration=page["duration"], identity_verified=True)
    for endpoint in ("/x/player/v2", "/x/player/wbi/v2"):
        try:
            data = api(endpoint, headers, bvid=report["bvid"], cid=page["cid"])
            tracks = data.get("subtitle", {}).get("subtitles", [])
            tracks = [t for t in tracks if t.get("subtitle_url")]
            report["attempts"].append({"endpoint": endpoint, "track_count": len(tracks),
                                       "login_required": bool(data.get("need_login_subtitle"))})
            # Respect selected language. Other tracks must not silently replace it.
            tracks = [t for t in tracks if t.get("lan") == args.language]
            for track in tracks:
                url = track["subtitle_url"]
                if url.startswith("//"):
                    url = "https:" + url
                if urlparse(url).scheme != "https":
                    continue
                # Do not forward the account Cookie to subtitle CDNs.
                payload = get_json(url, {k: v for k, v in headers.items() if k != "Cookie"})
                rows = normalize(payload)
                report.update(source="platform", language=track["lan"], track_id=track.get("id"))
                return rows, payload
        except Exception as exc:
            report["attempts"].append({"endpoint": endpoint, "error_type": type(exc).__name__})
    raise ValueError("No usable subtitle track; login, language availability or API access may be required")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--input", help="Existing JSON or SRT; skips network")
    parser.add_argument("--source", choices=["cache", "asr", "manual"], default="cache")
    parser.add_argument("--cid", type=int, help="Expected part CID")
    parser.add_argument("--language", default="ai-zh", help="Exact platform language code")
    parser.add_argument("--cookie-file", help="Private file containing a Cookie header; never logged")
    parser.add_argument("--frame-map", help="JSON list of file/time/precision entries; use capture timestamps")
    args = parser.parse_args()
    directory = Path(args.output)
    directory.mkdir(parents=True, exist_ok=True)
    match = re.search(r"BV[0-9A-Za-z]+", args.url)
    if not match:
        parser.error("Use a full Bilibili URL containing a BV ID")
    page = int(parse_qs(urlparse(args.url).query).get("p", ["1"])[0])
    if page < 1:
        parser.error("p must be positive")
    report = {"url": args.url, "bvid": match[0], "page": page, "cid": args.cid,
              "collected_at": datetime.now(timezone.utc).isoformat(), "attempts": [],
              "status": "missing", "identity_verified": False}
    # A rerun must not accidentally expose stale evidence after a failed collection.
    generated = [directory / name for name in
                 ("subtitles.json", "subtitles.srt", "sectioned.md", "subtitle-raw.json", "evidence-index.json")]
    try:
        if args.input:
            source = Path(args.input)
            if source.resolve() in [p.resolve() for p in generated]:
                raise ValueError("Import must be outside this output's generated files")
            raw = source.read_bytes()
            payload = parse_srt(raw.decode("utf-8-sig")) if source.suffix.lower() == ".srt" else read_json(source)
            rows = normalize(payload)
            report.update(source=args.source, input_file=str(source.resolve()),
                          sha256=hashlib.sha256(raw).hexdigest(), language=args.language)
            # Supplied identity is declared, not independently verified for legacy caches.
            if isinstance(payload, dict) and isinstance(payload.get("metadata"), dict):
                metadata = payload["metadata"]
                for key in ("bvid", "page", "cid"):
                    if metadata.get(key) is not None and report.get(key) is not None and metadata[key] != report[key]:
                        raise ValueError("Imported subtitle metadata mismatch: " + key)
        else:
            rows, payload = fetch(args, report)
        frame_map = read_json(args.frame_map) if args.frame_map else []
        for frame in frame_map:
            if not math.isfinite(seconds(frame["time"])) or seconds(frame["time"]) < 0:
                raise ValueError("Invalid frame timestamp")
        report.update(status="available", segment_count=len(rows), start=rows[0]["from"],
                      end=max(r["to"] for r in rows), audio_verified=False)
        (directory / "subtitle-raw.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        (directory / "subtitles.json").write_text(json.dumps({"metadata": report, "body": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
        srt = "\n\n".join(f"{r['index']}\n{stamp(r['from']).replace('.', ',')} --> {stamp(r['to']).replace('.', ',')}\n{r['content']}" for r in rows)
        (directory / "subtitles.srt").write_text(srt + "\n", encoding="utf-8")
        lines = ["# 字幕证据", "", f"来源：{report['source']}；{report['bvid']} P{page}；CID {report['cid']}。", "", "保留原文；缓存或ASR可能有错字，未逐句核验音轨。", ""]
        bucket = None
        for row in rows:
            current = int(row["from"] // 60)
            if current != bucket:
                lines.extend([f"## {stamp(current * 60)} 起", ""])
                bucket = current
            lines.append(f"- S{row['index']:04} [{stamp(row['from'])}–{stamp(row['to'])}] {row['content']}")
        (directory / "sectioned.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        evidence = [{**f, "subtitle_ids": [r["index"] for r in rows if r["from"] <= seconds(f["time"]) < r["to"]]} for f in frame_map]
        (directory / "evidence-index.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        # Only remove this script's generated outputs, never source files/video/frames.
        protected = Path(args.input).resolve() if args.input else None
        for path in generated:
            if path.resolve() != protected:
                path.unlink(missing_ok=True)
        report.update(status="missing", error_type=type(exc).__name__,
                      reason=str(exc) if isinstance(exc, ValueError) else "Collection failed; see error_type")
    (directory / "subtitle-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report.get(key) for key in ("status", "source", "page", "cid", "segment_count", "reason")}, ensure_ascii=False))
    return 0 if report["status"] == "available" else 2


if __name__ == "__main__":
    raise SystemExit(main())
