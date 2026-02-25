#!/usr/bin/env python3
import re
import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple, Dict

ROOT = Path(__file__).resolve().parents[1]
EN_DIR = ROOT / "最后的气宗 英文剧本"
ZH_DIR = ROOT / "最后的气宗 中文剧本"
DOCS_DIR = ROOT / "docs"

SEASONS = {
    1: list(range(101, 121)),
    2: list(range(201, 221)),
    3: list(range(301, 322)),
}


def read_text_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.lstrip("\ufeff")


def read_doc_file(path: Path) -> str:
    textutil = shutil.which("textutil")
    antiword = shutil.which("antiword")

    if textutil:
        out = subprocess.check_output(
            [textutil, "-convert", "txt", "-stdout", str(path)]
        )
    elif antiword:
        out = subprocess.check_output([antiword, str(path)])
    else:
        raise FileNotFoundError(
            "Missing converter. Install 'antiword' (Linux) or use macOS 'textutil'."
        )

    text = out.decode("utf-8", errors="ignore")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.lstrip("\ufeff")


def normalize_block(text: str) -> str:
    # Trim trailing whitespace on each line and remove excessive leading/trailing blank lines
    lines = [ln.rstrip() for ln in text.split("\n")]
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()
    return "\n".join(lines)


def find_title(text: str) -> str:
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            # First non-empty line is usually a title; keep it short
            return re.sub(r"\s+", " ", stripped)
    return ""


def parse_episode_number(stem: str) -> int:
    m = re.match(r"^(\d{3})$", stem)
    if not m:
        raise ValueError(f"Unexpected episode filename: {stem}")
    return int(m.group(1))


def split_by_episode(text: str) -> List[str]:
    lines = text.split("\n")
    indices = []
    for i, line in enumerate(lines):
        if re.match(r"^第.+回", line.strip()):
            indices.append(i)
    if not indices:
        return [text]

    chunks = []
    for idx, start in enumerate(indices):
        end = indices[idx + 1] if idx + 1 < len(indices) else len(lines)
        chunk = "\n".join(lines[start:end])
        chunks.append(chunk)
    return chunks


def load_english() -> Dict[int, str]:
    out: Dict[int, str] = {}
    for path in sorted(EN_DIR.glob("*.txt")):
        num = parse_episode_number(path.stem)
        out[num] = normalize_block(read_text_file(path))
    return out


def parse_range_from_name(name: str) -> Tuple[int, int]:
    m = re.search(r"(\d{3})-(\d{3})", name)
    if not m:
        raise ValueError(f"Unexpected range in filename: {name}")
    return int(m.group(1)), int(m.group(2))


def load_chinese() -> Dict[int, str]:
    out: Dict[int, str] = {}
    # single episode docs
    for path in sorted(ZH_DIR.glob("avatar 1??.doc")):
        # skip range files for now
        if re.search(r"\d{3}-\d{3}", path.name):
            continue
        m = re.search(r"(\d{3})", path.name)
        if not m:
            continue
        num = int(m.group(1))
        out[num] = normalize_block(read_doc_file(path))

    # range files
    for path in sorted(ZH_DIR.glob("avatar *.doc")):
        if not re.search(r"\d{3}-\d{3}", path.name):
            continue
        start, end = parse_range_from_name(path.name)
        text = read_doc_file(path)
        chunks = [normalize_block(c) for c in split_by_episode(text)]
        expected = list(range(start, end + 1))
        if len(chunks) != len(expected):
            # Fallback: do not split, attach whole file to the first episode in range
            out[start] = normalize_block(text)
            continue
        for num, chunk in zip(expected, chunks):
            out[num] = chunk

    return out


def season_episode(num: int) -> Tuple[int, int]:
    return num // 100, num % 100


def episode_slug(num: int) -> str:
    season, ep = season_episode(num)
    return f"s{season:02d}e{ep:02d}"


def write_episode_md(num: int, en_text: str, zh_text: str):
    season, ep = season_episode(num)
    season_dir = DOCS_DIR / f"season-{season:02d}"
    season_dir.mkdir(parents=True, exist_ok=True)

    en_title = find_title(en_text) if en_text else ""
    title = f"S{season:02d}E{ep:02d}"
    if en_title and en_title.lower() not in title.lower():
        title = f"{title} - {en_title}"

    lines = [f"# {title}", ""]
    if en_text:
        lines += ["## English", "", "```text", en_text, "```", ""]
    if zh_text:
        lines += ["## 中文", "", "```text", zh_text, "```", ""]

    path = season_dir / f"{episode_slug(num)}.md"
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_indexes(season_nums: Dict[int, List[int]]):
    # Root index
    idx = ["# Avatar: The Last Airbender Scripts", "", "按季/集整理的电子书版本。", ""]
    for season in sorted(season_nums.keys()):
        idx.append(f"- [Season {season}](season-{season:02d}/index.md)")
    (DOCS_DIR / "index.md").write_text("\n".join(idx) + "\n", encoding="utf-8")

    # Season indexes
    for season, nums in sorted(season_nums.items()):
        season_dir = DOCS_DIR / f"season-{season:02d}"
        season_dir.mkdir(parents=True, exist_ok=True)
        lines = [f"# Season {season}", ""]
        for num in nums:
            slug = episode_slug(num)
            lines.append(f"- [{slug.upper()}](./{slug}.md)")
        (season_dir / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    en = load_english()
    zh = load_chinese()

    all_nums = sorted(set(en.keys()) | set(zh.keys()))
    season_nums: Dict[int, List[int]] = {1: [], 2: [], 3: []}

    for num in all_nums:
        season, _ = season_episode(num)
        if season not in season_nums:
            continue
        season_nums[season].append(num)
        write_episode_md(num, en.get(num, ""), zh.get(num, ""))

    for season in season_nums:
        season_nums[season] = sorted(season_nums[season])
    write_indexes(season_nums)


if __name__ == "__main__":
    main()
