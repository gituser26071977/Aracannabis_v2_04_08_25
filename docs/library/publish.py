#!/usr/bin/env python3
"""
AraOS Library — Script de Publicação.

Renderiza AraOS Standards (AS-XXX) em múltiplos formatos (HTML, PDF)
a partir da fonte Markdown em docs/standards/.

Dependências:
  - pandoc >= 3.0 (para HTML e PDF)
  - xelatex + texlive (para PDF; opcional)

Uso:
  python docs/library/publish.py                  # publica AS-001 v1.0
  python docs/library/publish.py --all            # publica todos os AS-*
  python docs/library/publish.py --html-only      # apenas HTML
  python docs/library/publish.py --pdf-only       # apenas PDF
  python docs/library/publish.py --dry-run        # simula sem escrever
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Caminhos do repositório
ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "docs" / "standards"
LIBRARY_DIR = ROOT / "docs" / "library" / "standards"
STYLESHEET = ROOT / "docs" / "library" / "stylesheets" / "araos.css"
TEMPLATE = ROOT / "docs" / "library" / "templates" / "araos.tex"


# REDACTED
# Utilitários
# REDACTED

def parse_metadata(md_path: Path) -> dict:
    """Extrai metadados do cabeçalho do Markdown-fonte."""
    md = md_path.read_text(encoding="utf-8")
    meta: dict = {}

    # Identificador (AS-XXX)
    m = re.search(r"^#\s+(AS-\d+)\s+—\s+(.+?)$", md, re.MULTILINE)
    if m:
        meta["id"] = m.group(1)
        meta["title"] = m.group(2).strip()

    # Título (segunda linha do título)
    m = re.search(r"^#\s+AS-\d+\s+—\s+AraOS Standard\s+\d+:\s+(.+?)$",
                  md, re.MULTILINE)
    if m:
        meta["title"] = m.group(1).strip()

    # Versão
    m = re.search(r"\*\*Versão:\*\*\s+(\d+\.\d+(?:\.\d+)?)", md)
    if m:
        meta["version"] = m.group(1)

    # Status
    m = re.search(r"\*\*Status:\*\*\s+(\w+)", md)
    if m:
        meta["status"] = m.group(1)

    # Categoria
    m = re.search(r"\*\*Categoria\*\*\s*\|\s*(\w[\w\s]+?)\s*\|", md)
    if not m:
        m = re.search(r"\*\*Categoria:\*\*\s+(\w[\w\s]+?)$", md, re.MULTILINE)
    if m:
        meta["category"] = m.group(1).strip()

    # Maturity
    m = re.search(r"\*\*Maturity:\*\*\s+(\w+)", md)
    if m:
        meta["maturity"] = m.group(1)

    # Data
    m = re.search(r"\*\*Data de emissão:\*\*\s+(\d{4}-\d{2}-\d{2})", md)
    if not m:
        m = re.search(r"\*\*Data:\*\*\s+(\d{4}-\d{2}-\d{2})", md)
    if m:
        meta["date"] = m.group(1)

    meta.setdefault("version", "1.0")
    meta.setdefault("status", "Aceito")
    meta.setdefault("category", "Clinical Knowledge Representation")
    meta.setdefault("maturity", "Stable")
    meta.setdefault("date", "2026-07-17")

    return meta


def slugify(title: str) -> str:
    """Slug institucional: lowercase, dashes, sem acentos."""
    s = title.lower()
    s = re.sub(r"[áàâã]", "a", s)
    s = re.sub(r"[éèê]", "e", s)
    s = re.sub(r"[íì]", "i", s)
    s = re.sub(r"[óòôõ]", "o", s)
    s = re.sub(r"[úù]", "u", s)
    s = re.sub(r"ç", "c", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


# REDACTED
# Renderizações
# REDACTED

def has_pandoc() -> bool:
    return shutil.which("pandoc") is not None


def render_html(src: Path, dst: Path, meta: dict, dry_run: bool) -> bool:
    if not has_pandoc():
        print(f"  ⚠ pandoc não disponível — pulando HTML", file=sys.stderr)
        return False

    cmd = [
        "pandoc", "-s",
        f"--css={STYLESHEET.relative_to(ROOT)}",
        f"--metadata=title={meta['id']} — AraOS Standard {meta['id'].split('-')[1]}: {meta['title']}",
        "--toc",
        "--toc-depth=3",
        "--standalone",
        f"--from=markdown+yaml_metadata_block",
        str(src.relative_to(ROOT)),
        "-o", str(dst.relative_to(ROOT)),
    ]
    print(f"  → HTML: {dst.name}")
    if dry_run:
        return True
    return subprocess.run(cmd, cwd=ROOT, check=False).returncode == 0


def render_pdf(src: Path, dst: Path, meta: dict, dry_run: bool) -> bool:
    if not has_pandoc():
        print(f"  ⚠ pandoc não disponível — pulando PDF", file=sys.stderr)
        return False
    if shutil.which("xelatex") is None:
        print(f"  ⚠ xelatex não disponível — pulando PDF", file=sys.stderr)
        return False

    cmd = [
        "pandoc", "-s",
        f"--template={TEMPLATE.relative_to(ROOT)}",
        "--pdf-engine=xelatex",
        "--toc",
        "--toc-depth=3",
        f"--metadata=title:{' '}".replace(" ", "")  # placeholder
            if False else
        f"--metadata=title:{meta['id']} — {meta['title']}",
        f"--metadata=version:{meta['version']}",
        f"--metadata=status:{meta['status']}",
        f"--metadata=maturity:{meta['maturity']}",
        f"--metadata=category:{meta['category']}",
        f"--metadata=date:{meta['date']}",
        str(src.relative_to(ROOT)),
        "-o", str(dst.relative_to(ROOT)),
    ]
    print(f"  → PDF: {dst.name}")
    if dry_run:
        return True
    return subprocess.run(cmd, cwd=ROOT, check=False).returncode == 0


# REDACTED
# Orquestração
# REDACTED

def publish_one(src: Path,
                html_only: bool, pdf_only: bool,
                dry_run: bool) -> int:
    meta = parse_metadata(src)
    if "id" not in meta or "title" not in meta:
        print(f"  ✗ Cabeçalho institucional ausente em {src.name}",
              file=sys.stderr)
        return 1

    slug = slugify(meta["title"])
    stem = f"{meta['id'].lower()}-{slug}-v{meta['version']}"

    print(f"\n[{meta['id']}] {meta['title']} v{meta['version']}")
    print(f"  Status: {meta['status']} · Maturity: {meta['maturity']}")

    # Cópia do Markdown-fonte para a Library (sempre, com nome versionado)
    md_dst = LIBRARY_DIR / f"{stem}.md"
    if not dry_run:
        md_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, md_dst)
    print(f"  → MD:  {md_dst.name}")

    failures = 0
    if not pdf_only:
        html_dst = LIBRARY_DIR / f"{stem}.html"
        if not render_html(src, html_dst, meta, dry_run):
            failures += 1

    if not html_only:
        pdf_dst = LIBRARY_DIR / f"{stem}.pdf"
        if not render_pdf(src, pdf_dst, meta, dry_run):
            failures += 1

    return failures


def main() -> int:
    p = argparse.ArgumentParser(description="AraOS Library Publisher")
    p.add_argument("--all", action="store_true",
                   help="publica todos os AS-* em docs/standards/")
    p.add_argument("--html-only", action="store_true")
    p.add_argument("--pdf-only", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not args.all:
        # Modo padrão: publica AS-001
        sources = [SOURCE_DIR / "AS-001-clinical-gene.md"]
    else:
        sources = sorted(SOURCE_DIR.glob("AS-*.md"))

    if not sources:
        print("Nenhuma fonte encontrada em docs/standards/", file=sys.stderr)
        return 1

    failures = 0
    for src in sources:
        if not src.exists():
            print(f"Fonte ausente: {src}", file=sys.stderr)
            failures += 1
            continue
        failures += publish_one(
            src, args.html_only, args.pdf_only, args.dry_run
        )

    print()
    if failures:
        print(f"⚠ {failures} falha(s).", file=sys.stderr)
        return 1
    print("✓ Publicação concluída.")
    return 0


if __name__ == "__main__":
    sys.exit(main())