#!/usr/bin/env python3
"""Markdown → 정적 HTML 사이트 빌더 (GitHub Actions 용).

README.md → index.html, docs/*.md → docs/*.html 로 변환하고
assets/ · profiles/ · patches/ 를 그대로 복사한다. 문서 간 .md 링크는 .html 로 재작성.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import markdown  # pip install markdown

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"

PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  :root {{ --bg:#0f1419; --panel:#171e26; --text:#d8e1ea; --muted:#8899a9;
          --accent:#4fc3f7; --border:#2a3644; --code:#10161d; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:0 0 80px; background:var(--bg); color:var(--text);
         font-family:'Pretendard','Noto Sans KR',-apple-system,'Segoe UI',sans-serif;
         line-height:1.7; font-size:16px; }}
  .wrap {{ max-width:920px; margin:0 auto; padding:32px 20px; }}
  nav {{ border-bottom:1px solid var(--border); background:var(--panel); }}
  nav .wrap {{ display:flex; gap:18px; padding:14px 20px; flex-wrap:wrap; }}
  nav a {{ color:var(--muted); text-decoration:none; font-size:14.5px; }}
  nav a:hover, nav a.on {{ color:var(--accent); }}
  h1,h2,h3 {{ color:#fff; line-height:1.35; }}
  h1 {{ font-size:30px; }}
  h2 {{ font-size:22px; color:var(--accent); border-bottom:1px solid var(--border); padding-bottom:8px; margin-top:44px; }}
  h3 {{ font-size:17.5px; color:#cfe6f5; }}
  a {{ color:var(--accent); }}
  img {{ max-width:100%; border-radius:12px; }}
  table {{ width:100%; border-collapse:collapse; margin:16px 0; font-size:14.5px;
          background:var(--panel); border-radius:8px; overflow:hidden; }}
  th,td {{ padding:9px 12px; text-align:left; border-bottom:1px solid var(--border); vertical-align:top; }}
  th {{ background:#1d2733; color:#b8cfe0; }}
  code {{ background:var(--code); padding:2px 7px; border-radius:4px;
         font-family:'JetBrains Mono','D2Coding',Consolas,monospace; font-size:13.5px; color:#9ccfff; }}
  pre {{ background:var(--code); border:1px solid var(--border); border-radius:8px;
        padding:14px 16px; overflow-x:auto; }}
  pre code {{ background:none; padding:0; color:#c5d8e8; }}
  blockquote {{ border-left:4px solid var(--accent); margin:14px 0; padding:8px 18px;
               background:var(--panel); border-radius:0 8px 8px 0; color:var(--muted); }}
  footer {{ color:var(--muted); font-size:13px; border-top:1px solid var(--border);
           margin-top:56px; padding-top:16px; }}
</style>
</head>
<body>
<nav><div class="wrap">
  <a href="{base}index.html">🦞 홈</a>
  <a href="{base}docs/01-gjc-intro.html">1부 GJC 개요·설치</a>
  <a href="{base}docs/02-multivendor-overview.html">2부 원본 가이드 개요</a>
  <a href="{base}docs/03-adaptation.html">3부 적응 가이드 · /mlbo</a>
  <a href="https://github.com/yazzang-homelab/gjc-multivendor-adaptation-guide">GitHub</a>
</div></nav>
<div class="wrap">
{body}
<footer>CC BY 4.0 · 파생: <a href="https://github.com/project820/gjc-multivendor-setup-guide">gjc-multivendor-setup-guide</a>
 · 엔진: <a href="https://github.com/Yeachan-Heo/gajae-code">Gajae Code (GJC)</a></footer>
</div>
</body>
</html>
"""

MD = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "md_in_html", "attr_list"])


def render(src: Path, dst: Path, base: str) -> None:
    text = src.read_text(encoding="utf-8")
    # 문서 간 .md 링크 → .html
    text = re.sub(r"\((?!https?://)([^)\s]+)\.md(#[^)\s]*)?\)", r"(\1.html\2)", text)
    MD.reset()
    body = MD.convert(text)
    m = re.search(r"^#\s+(.+)$", text, re.M)
    title = (m.group(1).strip() if m else src.stem).replace("*", "")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(PAGE.format(title=title, body=body, base=base), encoding="utf-8")
    print(f"  {src.relative_to(ROOT)} -> {dst.relative_to(OUT)}")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    render(ROOT / "README.md", OUT / "index.html", base="")
    for doc in sorted((ROOT / "docs").glob("*.md")):
        render(doc, OUT / "docs" / f"{doc.stem}.html", base="../")

    for static in ("assets", "profiles", "patches"):
        src = ROOT / static
        if src.exists():
            shutil.copytree(src, OUT / static)
            print(f"  {static}/ copied")

    (OUT / ".nojekyll").write_text("")
    print(f"done -> {OUT}")


if __name__ == "__main__":
    main()
