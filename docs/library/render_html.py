#!/usr/bin/env python3
"""
Renderiza o Markdown-fonte em HTML aplicando o stylesheet AraOS.

Uso:
  python3 docs/library/render_html.py <input.md> <output.html>
"""
import sys
import re
import markdown
from pathlib import Path

def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 1

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])

    md_text = src.read_text(encoding="utf-8")

    # Configuração do markdown: TOCs, tables, fenced code, footnotes
    md = markdown.Markdown(
        extensions=[
            "toc",
            "tables",
            "fenced_code",
            "footnotes",
            "attr_list",
            "def_list",
            "sane_lists",
        ],
        extension_configs={
            "toc": {"permalink": False, "toc_depth": "2-4"},
        },
    )

    body_html = md.convert(md_text)

    # Extrai TOC se gerada
    toc_html = ""
    if hasattr(md, "toc") and md.toc:
        toc_html = f'<nav id="TOC" role="doc-toc" aria-label="Sumário">\n{md.toc}\n</nav>'

    # Extrai título do cabeçalho
    title_match = re.search(r"^#\s+(.+?)$", md_text, re.MULTILINE)
    page_title = title_match.group(1) if title_match else "AraOS Standard"

    # CSS path relativo (um nível acima de standards/)
    css_href = "../stylesheets/araos.css"

    full_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{page_title}</title>
<link rel="stylesheet" href="{css_href}">
</head>
<body>
{toc_html}
{body_html}
</body>
</html>
"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(full_html, encoding="utf-8")
    print(f"✓ HTML gerado: {dst.name} ({len(full_html):,} bytes)")
    return 0

if __name__ == "__main__":
    sys.exit(main())