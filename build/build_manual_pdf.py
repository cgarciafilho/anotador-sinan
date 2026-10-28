#!/usr/bin/env python3
"""Builds the printable manual (PDF, A4) from docs/MANUAL.md, so that the markdown is the only source of the text.

    python3 build/build_manual_pdf.py [--saida PASTA_OU_ARQUIVO] [--html]   (default: build/dist/MANUAL_anotador_sinan_v<versão>.pdf)

Needs `markdown` and `weasyprint` (pip); the version comes from src/sinan_anotador/__init__.py and the concept DOI from
CITATION.cff. Markdown → HTML (tables, GitHub-style heading ids so the "Sumário" links resolve) → cover + table of contents
with page numbers + running footer (CSS paged media) → PDF. Links to other files of the repository become plain names,
with the GitHub address of the version on the cover; external links keep their address in print.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUAL = ROOT / "docs" / "MANUAL.md"
REPO_URL = "https://github.com/cgarciafilho/anotador-sinan"

CSS = """
@page {
    size: A4;
    margin: 20mm 18mm 22mm 18mm;
    @bottom-left { content: "anotador SINAN v%(version)s — Manual"; font: 8.5pt "Liberation Sans", "DejaVu Sans", sans-serif; color: #555; }
    @bottom-right { content: "página " counter(page) " de " counter(pages); font: 8.5pt "Liberation Sans", "DejaVu Sans", sans-serif; color: #555; }
}
@page :first { @bottom-left { content: none; } @bottom-right { content: none; } }
html { font: 10.5pt/1.4 "Liberation Serif", "DejaVu Serif", serif; color: #111; }
body { margin: 0; }
h1, h2, h3, h4 { font-family: "Liberation Sans", "DejaVu Sans", sans-serif; color: #0b3d5c; break-after: avoid; line-height: 1.2; }
h1 { font-size: 22pt; margin: 0 0 6mm; }
h2 { font-size: 15pt; margin: 10mm 0 3mm; border-bottom: 1.2pt solid #0b3d5c; padding-bottom: 1mm; }
h2.toc, h2.quebra { break-before: page; }   /* new page only where it pays: the table of contents and the long sections */
h3 { font-size: 12pt; margin: 6mm 0 2mm; }
h4 { font-size: 11pt; margin: 5mm 0 2mm; }
p { margin: 0 0 2.6mm; text-align: left; orphans: 3; widows: 3; }
ul, ol { margin: 0 0 3mm; padding-left: 6mm; }
li { margin-bottom: 1mm; }
code { font: 9pt "Liberation Mono", "DejaVu Sans Mono", monospace; background: #f1f3f5; padding: 0 1.5pt; border-radius: 2pt;
       white-space: pre-wrap; overflow-wrap: break-word; }
pre { font: 8.5pt/1.3 "Liberation Mono", "DejaVu Sans Mono", monospace; background: #f1f3f5; padding: 2mm; white-space: pre-wrap; }
strong { color: #000; }
a { color: #0b3d5c; text-decoration: none; }
a.ext::after { content: " (" attr(href) ")"; font: 8pt "Liberation Mono", "DejaVu Sans Mono", monospace; color: #555; overflow-wrap: anywhere; }
span.doc { font: 9pt "Liberation Mono", "DejaVu Sans Mono", monospace; }
table { border-collapse: collapse; width: 100%%; margin: 2mm 0 4mm; font-size: 8.8pt; line-height: 1.3; break-inside: auto; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
th, td { border: 0.5pt solid #9aa5ad; padding: 1.2mm 1.6mm; vertical-align: top; text-align: left; overflow-wrap: break-word; }
th:first-child, td:first-child code { white-space: nowrap; }   /* key names and short headers must not be squeezed */
th { background: #e3ebf0; font-family: "Liberation Sans", "DejaVu Sans", sans-serif; font-size: 8.6pt; }
td code, th code { font-size: 8.2pt; }
blockquote { margin: 2mm 0 2mm 4mm; padding-left: 3mm; border-left: 1.5pt solid #9aa5ad; color: #333; }
hr { border: 0; border-top: 0.5pt solid #9aa5ad; margin: 4mm 0; }

/* cover */
.cover { height: 240mm; display: flex; flex-direction: column; justify-content: center; }
.cover h1 { font-size: 30pt; border: 0; margin-bottom: 3mm; }
.cover .sub { font: 14pt "Liberation Sans", "DejaVu Sans", sans-serif; color: #333; margin-bottom: 14mm; }
.cover .meta { font-size: 10.5pt; color: #333; }
.cover .meta p { margin-bottom: 1.5mm; }
.cover .aviso { margin-top: 14mm; padding: 3mm; border: 0.7pt solid #9aa5ad; background: #f7f8f9; font-size: 9.5pt; }

/* table of contents: the manual's own "Sumário" list, with page numbers */
ol.sumario { list-style: none; padding: 0; margin: 0 0 4mm; }
ol.sumario li { margin-bottom: 1.6mm; font-family: "Liberation Sans", "DejaVu Sans", sans-serif; font-size: 10.5pt; }
ol.sumario a::after { content: leader(". ") target-counter(attr(href), page); color: #333; }
ol.sumario ol { list-style: none; padding-left: 6mm; margin-top: 1.6mm; }
ol.sumario ol li { font-size: 9.5pt; margin-bottom: 1.2mm; }
"""


def github_slug(value: str, separator: str = "-") -> str:
    """Heading id the way GitHub makes it: lower case, drop punctuation (accented letters stay), spaces to hyphens."""
    value = value.strip().lower()
    value = re.sub(r"[^\w\- ]", "", value)
    return value.replace(" ", separator)


def version() -> str:
    m = re.search(r'^__version__ = "(.*)"', (ROOT / "src" / "sinan_anotador" / "__init__.py").read_text(encoding="utf-8"), re.M)
    if not m:
        sys.exit("ERRO: __version__ não encontrada em src/sinan_anotador/__init__.py")
    return m.group(1)


def concept_doi() -> str | None:
    last = None
    for line in (ROOT / "CITATION.cff").read_text(encoding="utf-8").splitlines():
        if m := re.match(r"\s*(?:-\s+)?(?:type: doi\s*)?value:\s*(\S+)", line):
            last = m.group(1)
        if "conceito" in line and last:
            return last
    return None


def headings_with_ids(md_text: str) -> list[tuple[int, str, str]]:
    """(level, text, id) for every ATX heading, with GitHub-style ids (duplicates get -1, -2 … like GitHub)."""
    seen: dict[str, int] = {}
    out = []
    for m in re.finditer(r"^(#{1,6}) (.+?)\s*$", md_text, re.M):
        text = m.group(2).strip()
        base = github_slug(re.sub(r"`", "", text))
        n = seen.get(base, 0)
        seen[base] = n + 1
        out.append((len(m.group(1)), text, base if n == 0 else f"{base}-{n}"))
    return out


def md_to_html(md_text: str, ver: str) -> str:
    import markdown
    from markdown.extensions.toc import TocExtension

    body = markdown.markdown(md_text, extensions=["tables", "sane_lists", "fenced_code", TocExtension(slugify=github_slug)],
                             output_format="html5")
    # the first h1 belongs on the cover; the manual's own "Sumário:" list becomes the table of contents
    body = re.sub(r"^<h1[^>]*>.*?</h1>\s*", "", body, count=1, flags=re.S)
    body, n = re.subn(r"<p>Sumário:</p>\s*<ol>", '<h2 id="sumario">Sumário</h2>\n<ol class="sumario">', body, count=1)
    body = re.sub(r'<h2 id="(1-|4-)', r'<h2 class="quebra" id="\1', body)   # a new page before the first and the longest section
    if n != 1:
        print("AVISO: lista 'Sumário:' não encontrada; o PDF sai sem sumário", file=sys.stderr)
    tree = f"{REPO_URL}/blob/v{ver}"

    def link(m):
        href, text = m.group(1), m.group(2)
        if href.startswith("#"):
            return m.group(0)
        if href.startswith(("http://", "https://")):
            return m.group(0) if html.unescape(text) == href else f'<a class="ext" href="{href}">{text}</a>'
        name = Path(href).name                                      # METODO.md, ../README.md, ../CITATION.cff
        return f'<span class="doc" title="{tree}/{href.replace("../", "")}">{html.escape(name)}</span>'
    return re.sub(r'<a href="([^"]+)">(.*?)</a>', link, body, flags=re.S)


def build_html(md_text: str, ver: str, date: dt.date) -> str:
    doi = concept_doi()
    body = md_to_html(md_text, ver)
    date_txt = date.strftime("%d/%m/%Y")
    cover = f"""
<section class="cover">
  <h1>anotador SINAN</h1>
  <div class="sub">Manual do usuário</div>
  <div class="meta">
    <p><strong>Versão {html.escape(ver)}</strong> · gerado em {date_txt} a partir de <span class="doc">docs/MANUAL.md</span></p>
    <p>Código-fonte, versões e relato de problemas: {REPO_URL}</p>
    {"<p>DOI (todas as versões): https://doi.org/" + html.escape(doi) + "</p>" if doi else ""}
    <p>Documentos citados no texto (<span class="doc">METODO.md</span>, <span class="doc">duplicidades_definicoes_manuais.md</span>,
       <span class="doc">README.md</span>, <span class="doc">CITATION.cff</span>): {REPO_URL}/tree/v{html.escape(ver)}</p>
    <p>Licença MIT · Copyright (c) 2026 Carlos Garcia Filho</p>
  </div>
  <div class="aviso"><strong>Sigilo.</strong> O programa não desidentifica: o xlsx gerado copia todos os campos do DBF, inclusive
    nome, nome da mãe, nascimento e endereço, e as abas de duplicidades trazem o nome do paciente. Trate o xlsx como trata o DBF.
    Nunca anexe DBF ou xlsx, nem trechos deles, a uma issue.</div>
</section>
"""
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>anotador SINAN v{html.escape(ver)} — Manual do usuário</title>
<meta name="author" content="Carlos Garcia Filho">
<meta name="description" content="Manual do anotador SINAN: como rodar, como ler o xlsx e as regras de duplicidade, agravo por agravo.">
<style>{CSS % {"version": html.escape(ver)}}</style>
</head><body>{cover}{body}</body></html>
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Gera o manual em PDF a partir de docs/MANUAL.md")
    ap.add_argument("--saida", help="pasta ou arquivo de saída (padrão: build/dist/MANUAL_anotador_sinan_v<versão>.pdf)")
    ap.add_argument("--html", action="store_true", help="grava também o HTML intermediário ao lado do PDF")
    ap.add_argument("--data", help="data impressa na capa, AAAA-MM-DD (padrão: hoje)")
    a = ap.parse_args(argv)
    ver = version()
    date = dt.date.fromisoformat(a.data) if a.data else dt.date.today()
    out = Path(a.saida) if a.saida else ROOT / "build" / "dist"
    if out.suffix.lower() != ".pdf":
        out = out / f"MANUAL_anotador_sinan_v{ver}.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)

    md_text = MANUAL.read_text(encoding="utf-8")
    ids = {i for _, _, i in headings_with_ids(md_text)}
    broken = [h for h in re.findall(r"\]\(#([^)]+)\)", md_text) if h not in ids]
    if broken:
        sys.exit(f"ERRO: links do sumário sem título correspondente: {broken}")
    doc_html = build_html(md_text, ver, date)
    if a.html:
        out.with_suffix(".html").write_text(doc_html, encoding="utf-8")

    from weasyprint import HTML
    HTML(string=doc_html, base_url=str(MANUAL.parent)).write_pdf(str(out))
    print(f"{out} ({out.stat().st_size:,} bytes)".replace(",", "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
