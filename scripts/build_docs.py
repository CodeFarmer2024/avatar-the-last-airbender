#!/usr/bin/env python3
import re
import subprocess
import shutil
import html
from pathlib import Path
from typing import List, Tuple, Dict

ROOT = Path(__file__).resolve().parents[1]
EN_DIR = ROOT / "最后的气宗 英文剧本"
ZH_DIR = ROOT / "最后的气宗 中文剧本"
DOCS_DIR = ROOT / "docs"

SITE_NAME = "Avatar: The Last Airbender Scripts"
SITE_URL = "https://codefarmer2024.github.io/avatar-the-last-airbender/"
REPO_URL = "https://github.com/CodeFarmer2024/avatar-the-last-airbender"


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
    text = text.replace("\t", "    ").replace("\x0c", "\n")
    lines = [ln.rstrip().lstrip(" ") for ln in text.split("\n")]
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()
    # Collapse consecutive blank lines to a single blank line
    compact = []
    blank = False
    for ln in lines:
        if ln.strip() == "":
            if not blank:
                compact.append("")
            blank = True
        else:
            compact.append(ln)
            blank = False
    # Remove common leading indentation
    non_empty = [ln for ln in compact if ln.strip() != ""]
    if not non_empty:
        return ""
    min_indent = min(len(ln) - len(ln.lstrip(" ")) for ln in non_empty)
    if min_indent > 0:
        compact = [ln[min_indent:] if len(ln) >= min_indent else "" for ln in compact]
    return "\n".join(compact)


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
            # If the file contains more/less episodes than the filename suggests,
            # trust the actual split count and extend the range accordingly.
            end = start + len(chunks) - 1
            expected = list(range(start, end + 1))
        for num, chunk in zip(expected, chunks):
            out[num] = chunk

    return out


def season_episode(num: int) -> Tuple[int, int]:
    return num // 100, num % 100


def episode_slug(num: int) -> str:
    season, ep = season_episode(num)
    return f"s{season:02d}e{ep:02d}"


def indent_lines(lines: List[str], spaces: int = 4) -> List[str]:
    prefix = " " * spaces
    return [prefix + ln if ln != "" else "" for ln in lines]


def render_script_block(text: str) -> List[str]:
    escaped = html.escape(text)
    return [
        '<pre class="script">',
        escaped,
        "</pre>",
        "",
    ]


def render_two_column(en_text: str, zh_text: str) -> List[str]:
    en_block = "\n".join(render_script_block(en_text)).strip()
    zh_block = "\n".join(render_script_block(zh_text)).strip()
    return [
        '<table class="script-table">',
        "  <thead>",
        "    <tr>",
        "      <th>English</th>",
        "      <th>中文</th>",
        "    </tr>",
        "  </thead>",
        "  <tbody>",
        "    <tr>",
        f"      <td>{en_block}</td>",
        f"      <td>{zh_block}</td>",
        "    </tr>",
        "  </tbody>",
        "</table>",
        "",
    ]


def build_episode_title(num: int, en_text: str) -> str:
    season, ep = season_episode(num)
    title = f"S{season:02d}E{ep:02d}"
    en_title = find_title(en_text) if en_text else ""
    if en_title and en_title.lower() not in title.lower():
        title = f"{title} - {en_title}"
    return title


def write_episode_md(num: int, en_text: str, zh_text: str) -> str:
    season, _ = season_episode(num)
    season_dir = DOCS_DIR / f"season-{season:02d}"
    season_dir.mkdir(parents=True, exist_ok=True)

    title = build_episode_title(num, en_text)

    langs = []
    if en_text:
        langs.append("English")
    if zh_text:
        langs.append("中文")
    langs_label = " / ".join(langs) if langs else "N/A"

    lines = [f"# {title}", "", f"**Languages:** {langs_label}", ""]
    if en_text and zh_text:
        lines += render_two_column(en_text, zh_text)
    else:
        if en_text:
            lines += ["## English", ""] + render_script_block(en_text)
        if zh_text:
            lines += ["## 中文", ""] + render_script_block(zh_text)
        if not en_text and not zh_text:
            lines += ["_No script content available._", ""]

    path = season_dir / f"{episode_slug(num)}.md"
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return title


def write_indexes(
    season_nums: Dict[int, List[int]],
    titles: Dict[int, str],
    missing_en: List[int],
    missing_zh: List[int],
):
    # Root index
    idx = [f"# {SITE_NAME}", "", "按季/集整理的电子书版本。", ""]
    for season in sorted(season_nums.keys()):
        idx.append(f"- [Season {season}](season-{season:02d}/index.md)")
    if missing_en or missing_zh:
        idx += ["", "## Coverage", ""]
        if missing_en:
            idx.append(
                "- Missing English: "
                + ", ".join(episode_slug(n).upper() for n in missing_en)
            )
        if missing_zh:
            idx.append(
                "- Missing 中文: "
                + ", ".join(episode_slug(n).upper() for n in missing_zh)
            )
    (DOCS_DIR / "index.md").write_text("\n".join(idx) + "\n", encoding="utf-8")

    # Season indexes
    for season, nums in sorted(season_nums.items()):
        season_dir = DOCS_DIR / f"season-{season:02d}"
        season_dir.mkdir(parents=True, exist_ok=True)
        lines = [f"# Season {season}", ""]
        for num in nums:
            slug = episode_slug(num)
            title = titles.get(num, slug.upper())
            lines.append(f"- [{title}](./{slug}.md)")
        (season_dir / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_mkdocs(season_nums: Dict[int, List[int]]):
    lines = [
        f'site_name: "{SITE_NAME}"',
        f"site_url: {SITE_URL}",
        f"repo_url: {REPO_URL}",
        "theme: readthedocs",
        "docs_dir: docs",
        "site_dir: site",
        "use_directory_urls: false",
        "extra_css:",
        "  - styles.css",
        "nav:",
        "  - Home: index.md",
    ]
    for season in sorted(season_nums.keys()):
        lines.append(f"  - Season {season}:")
        lines.append(f"      - Index: season-{season:02d}/index.md")
        for num in season_nums[season]:
            slug = episode_slug(num)
            lines.append(f"      - {slug.upper()}: season-{season:02d}/{slug}.md")
    (ROOT / "mkdocs.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    en = load_english()
    zh = load_chinese()

    all_nums = sorted(set(en.keys()) | set(zh.keys()))
    season_nums: Dict[int, List[int]] = {1: [], 2: [], 3: []}
    titles: Dict[int, str] = {}
    missing_en = []
    missing_zh = []

    for num in all_nums:
        season, _ = season_episode(num)
        if season not in season_nums:
            continue
        season_nums[season].append(num)
        titles[num] = write_episode_md(num, en.get(num, ""), zh.get(num, ""))
        if num not in en:
            missing_en.append(num)
        if num not in zh:
            missing_zh.append(num)

    for season in season_nums:
        season_nums[season] = sorted(season_nums[season])
    write_indexes(season_nums, titles, missing_en, missing_zh)
    write_mkdocs(season_nums)


if __name__ == "__main__":
    main()
