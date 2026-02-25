# Avatar: The Last Airbender Scripts

将现有剧本文档按“季/集”生成电子书页面，并可发布到 GitHub Pages。

站点地址：<https://codefarmer2024.github.io/avatar-the-last-airbender/>

## 本地生成

1. 生成 Markdown 内容

```bash
python3 scripts/build_docs.py
```

2. 本地预览（需要安装 mkdocs）

```bash
pip install mkdocs
mkdocs serve
```

## GitHub Pages 发布

- 已配置 `.github/workflows/gh-pages.yml`，推送到 `main` 或 `master` 分支后会自动构建并发布。
- 需要在 GitHub 仓库设置中启用 Pages：
  - `Settings` -> `Pages` -> `Build and deployment` 选择 `GitHub Actions`。

## 目录结构

- `docs/`：生成后的电子书内容（按季/集）
- `scripts/build_docs.py`：从中文 `.doc` 和英文 `.txt` 生成 Markdown
- `mkdocs.yml`：站点配置
