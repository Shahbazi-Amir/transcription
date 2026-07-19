#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


def sections(markdown):
    markdown = re.sub(r"^# .+?\n", "", markdown, count=1)
    markdown = re.sub(r"^>.*?\n", "", markdown, flags=re.MULTILINE)
    parts = re.split(r"(?=^##+ )", markdown, flags=re.MULTILINE)
    return [re.sub(r"\n{3,}", "\n\n", part).strip() for part in parts if len(part.strip()) > 80]


def split_long(text, limit=1800):
    if len(text) <= limit:
        return [text]
    paragraphs = text.split("\n\n")
    chunks, current = [], []
    for paragraph in paragraphs:
        if current and len("\n\n".join(current + [paragraph])) > limit:
            chunks.append("\n\n".join(current))
            current = [paragraph]
        else:
            current.append(paragraph)
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def main():
    episodes_dir = ROOT / "rag/episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    all_records = []

    for episode in MANIFEST["episodes"]:
        if episode["status"] != "reviewed":
            continue
        markdown = (ROOT / episode["transcript_path"]).read_text(encoding="utf-8")
        chunks = [chunk for section in sections(markdown) for chunk in split_long(section)]
        records = []
        program = episode.get("program", MANIFEST["program"])
        for index, text in enumerate(chunks, 1):
            metadata = {
                "program": program,
                "episode": episode["episode"],
                "title": episode["title"],
                "speakers": episode["speakers"],
                "source_url": episode["source_url"],
                "video_url": episode["video_url"],
                "language": MANIFEST["language"],
                "review_status": episode["status"]
            }
            if episode.get("season"):
                metadata["season"] = episode["season"]
            record = {
                "id": f"{episode['id']}-{index:03d}",
                "text": text,
                "metadata": metadata
            }
            records.append(record)
        destination = ROOT / episode["rag_path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in records), encoding="utf-8")
        all_records.extend(records)

    (ROOT / "rag/all-chunks.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in all_records), encoding="utf-8"
    )
    print(f"built {len(all_records)} chunks")


if __name__ == "__main__":
    main()
