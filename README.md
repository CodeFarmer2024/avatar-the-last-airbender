# Avatar: The Last Airbender Scripts (EN/CN)

[![Deploy MkDocs to GitHub Pages](https://github.com/CodeFarmer2024/avatar-the-last-airbender/actions/workflows/gh-pages.yml/badge.svg)](https://github.com/CodeFarmer2024/avatar-the-last-airbender/actions/workflows/gh-pages.yml)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-live-brightgreen)](https://codefarmer2024.github.io/avatar-the-last-airbender/)

Bilingual (English/Chinese) Avatar: The Last Airbender scripts organized by season and episode.

## Site

Live site: https://codefarmer2024.github.io/avatar-the-last-airbender/

This project publishes a static site via GitHub Pages with one page per season and episode.

Local preview:

```bash
pip install mkdocs mkdocs-material
python3 scripts/build_docs.py
mkdocs serve
```

Deploy (CI):

```bash
git push origin main
```

## Dependencies

- Linux CI uses `antiword` to read `.doc` files
- macOS local build uses `textutil` (built-in)

## Structure

- `最后的气宗 英文剧本/` source English txt files
- `最后的气宗 中文剧本/` source Chinese doc files
- `docs/` generated markdown pages
- `scripts/build_docs.py` build script
- `mkdocs.yml` site config

## License

MIT
