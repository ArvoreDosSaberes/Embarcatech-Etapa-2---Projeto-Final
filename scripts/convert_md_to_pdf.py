#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import re
import signal
import struct
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Protocol, Sequence, Tuple

import yaml
from markdown import markdown

try:
    from weasyprint import HTML
    from weasyprint.document import DocumentMetadata
except ModuleNotFoundError as import_error:  # pragma: no cover - execução defensiva
    HTML = None  # type: ignore[assignment]
    DocumentMetadata = None  # type: ignore[assignment]
    WEASYPRINT_IMPORT_ERROR = import_error
else:
    WEASYPRINT_IMPORT_ERROR = None

if TYPE_CHECKING:  # pragma: no cover - anotação para mypy/pylance
    from weasyprint.document import DocumentMetadata as DocumentMetadataType
else:
    DocumentMetadataType = Any

PDF_STYLES = """
@page {
    margin: 2cm;
}

body {
    margin: 0;
    font-family: "Helvetica", "Arial", sans-serif;
    font-size: 12pt;
}

table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
}

thead tr,
tbody tr {
    page-break-inside: avoid;
}

th,
td {
    border: 1px solid #000000;
    padding: 0.4rem;
    text-align: justify;
    vertical-align: top;
    word-break: break-word;
}

caption {
    caption-side: top;
    text-align: center;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

img {
    max-width: 100%;
    height: auto;
}

.image-portrait {
    text-align: center;
    page-break-inside: avoid;
    break-inside: avoid;
}

.image-portrait img {
    /*
     * A4 (portrait) = 29,7cm de altura.
     * Margens de 2cm em cima + 2cm em baixo => 25,7cm úteis.
     * Usamos max-height em cm para evitar casos em que porcentagem/vh não é
     * resolvida como esperado e a imagem acaba sendo cortada no PDF.
     */
    max-height: 25.7cm;
    object-fit: contain;
}

@page image-landscape {
    size: A4 landscape;
    margin: 2cm;
}

.image-landscape-page {
    page: image-landscape;
    page-break-before: always;
    page-break-after: always;
    text-align: center;
    page-break-inside: avoid;
    break-inside: avoid;
    display: flex;
    align-items: center;
    justify-content: center;
}

.image-landscape-page img {
    /*
     * A4 (landscape) = 21cm de altura e 29,7cm de largura.
     * Margens de 2cm em cada lado => altura útil 17cm e largura útil 25,7cm.
     */
    max-width: 25.7cm;
    max-height: 17cm;
    object-fit: contain;
}
"""

SLIDE_PDF_STYLES = """
@page {
    size: 1280px 720px;
    margin: 0;
}

html, body {
    margin: 0;
    padding: 0;
    font-family: "Segoe UI", "Roboto", "Helvetica Neue", "Arial", sans-serif;
    font-size: 24pt;
    line-height: 1.4;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: #ffffff;
}

.slide {
    width: 1280px;
    min-height: 720px;
    box-sizing: border-box;
    padding: 60px 80px;
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    position: relative;
}

.slide:last-child {
    page-break-after: avoid;
}

.slide-title {
    width: 1280px;
    height: 720px;
    box-sizing: border-box;
    padding: 0 80px;
    page-break-after: always;
    page-break-inside: avoid;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 50%, #16213e 100%);
}

.slide-title h1 {
    font-size: 56pt;
    font-weight: 700;
    margin: 0 0 30px 0;
    color: #e94560;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.slide-title .subtitle {
    font-size: 28pt;
    color: #a0d2db;
    margin-bottom: 40px;
}

.slide-title .authors {
    font-size: 22pt;
    color: #c4c4c4;
    margin-top: 20px;
}

.slide-title .date {
    font-size: 18pt;
    color: #888888;
    margin-top: 30px;
}

.slide h1 {
    font-size: 40pt;
    font-weight: 600;
    margin: 0 0 40px 0;
    color: #e94560;
    border-bottom: 3px solid #e94560;
    padding-bottom: 15px;
}

.slide h2 {
    font-size: 32pt;
    font-weight: 600;
    margin: 0 0 30px 0;
    color: #a0d2db;
}

.slide h3 {
    font-size: 28pt;
    font-weight: 500;
    margin: 0 0 20px 0;
    color: #a0d2db;
}

.slide p {
    font-size: 24pt;
    margin: 0 0 20px 0;
    text-align: left;
}

.slide ul, .slide ol {
    font-size: 22pt;
    margin: 0 0 20px 40px;
    padding: 0;
}

.slide li {
    margin-bottom: 15px;
    line-height: 1.5;
}

.slide li::marker {
    color: #e94560;
}

.slide code {
    font-family: "Fira Code", "Consolas", "Monaco", monospace;
    font-size: 18pt;
    background: rgba(0, 0, 0, 0.4);
    padding: 4px 10px;
    border-radius: 6px;
    color: #a0d2db;
}

.slide pre {
    background: rgba(0, 0, 0, 0.5);
    padding: 25px 30px;
    border-radius: 12px;
    overflow: hidden;
    margin: 20px 0;
    border-left: 4px solid #e94560;
}

.slide pre code {
    font-size: 16pt;
    background: transparent;
    padding: 0;
    line-height: 1.6;
}

.slide blockquote {
    border-left: 5px solid #e94560;
    margin: 20px 0;
    padding: 15px 30px;
    background: rgba(233, 69, 96, 0.1);
    border-radius: 0 12px 12px 0;
    font-style: italic;
    color: #c4c4c4;
}

.slide table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-size: 18pt;
    page-break-inside: auto;
}

.slide thead {
    display: table-header-group;
}

.slide tbody {
    display: table-row-group;
}

.slide tr {
    page-break-inside: avoid;
    page-break-after: auto;
}

.slide th {
    background: rgba(233, 69, 96, 0.3);
    color: #ffffff;
    padding: 15px 20px;
    text-align: left;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.slide td {
    padding: 12px 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(0, 0, 0, 0.2);
}

.slide tr:nth-child(even) td {
    background: rgba(0, 0, 0, 0.3);
}

.slide img {
    max-width: 100%;
    max-height: 500px;
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.slide strong {
    color: #e94560;
}

.slide em {
    color: #a0d2db;
}

.slide a {
    color: #a0d2db;
    text-decoration: none;
    border-bottom: 2px dotted #a0d2db;
}

.slide hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent 0%, #e94560 20%, #a0d2db 50%, #e94560 80%, transparent 100%);
    margin: 25px 0;
}

.slide-number {
    position: absolute;
    bottom: 20px;
    right: 40px;
    font-size: 14pt;
    color: rgba(255, 255, 255, 0.4);
}

.slide-footer {
    position: absolute;
    bottom: 20px;
    left: 40px;
    font-size: 12pt;
    color: rgba(255, 255, 255, 0.3);
}
"""

ABNT_PDF_STYLES = """
@page {
    size: A4;
    margin-top: 3cm;
    margin-right: 2cm;
    margin-bottom: 2cm;
    margin-left: 3cm;
}

body {
    margin: 0;
    font-family: "Times New Roman", serif;
    font-size: 12pt;
    line-height: 1.5;
    text-align: justify;
}

p {
    text-indent: 1.25cm;
    margin: 0 0 0.75em 0;
}

p:first-child {
    text-indent: 0;
}

ul,
ol {
    margin: 0 0 0.75em 1.25cm;
}

.abnt-cover {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    min-height: 100vh;
    text-transform: uppercase;
    text-align: center;
}

.abnt-cover .institution,
.abnt-cover .course {
    font-weight: bold;
}

.abnt-cover .institution {
    margin-top: 2cm;
}

.abnt-cover .students {
    margin-top: 2cm;
}

.abnt-cover .title {
    margin-top: 2cm;
    font-weight: bold;
    font-size: 14pt;
}

.abnt-cover .nature-block {
    margin: 0 3cm;
    text-align: justify;
    text-transform: none;
    line-height: 1.5;
}

.abnt-cover .advisor-block {
    margin-top: 1cm;
    text-transform: none;
}

.abnt-cover .footer {
    margin-bottom: 2cm;
}

.abnt-cover .footer span {
    display: block;
}

.page-break {
    page-break-before: always;
}

.abnt-content h1,
.abnt-content h2,
.abnt-content h3,
.abnt-content h4,
.abnt-content h5,
.abnt-content h6 {
    text-transform: uppercase;
    text-align: left;
    margin: 2em 0 1em 0;
}

.abnt-content h1 {
    font-size: 12pt;
}

.abnt-content h2 {
    font-size: 12pt;
    font-weight: bold;
}

.abnt-content table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1.5em;
}

.abnt-content th,
.abnt-content td {
    border: 1px solid #000000;
    padding: 0.5rem;
    text-align: left;
}

.abnt-content caption {
    caption-side: top;
    text-align: center;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

img {
    max-width: 100%;
    height: auto;
}

.image-portrait {
    text-align: center;
    page-break-inside: avoid;
    break-inside: avoid;
}

.image-portrait img {
    /*
     * A4 (portrait) = 29,7cm de altura.
     * ABNT usa margem superior 3cm e inferior 2cm => 24,7cm úteis.
     */
    max-height: 24.7cm;
    object-fit: contain;
}

@page image-landscape {
    size: A4 landscape;
    margin: 2cm;
}

.image-landscape-page {
    page: image-landscape;
    page-break-before: always;
    page-break-after: always;
    text-align: center;
    page-break-inside: avoid;
    break-inside: avoid;
    display: flex;
    align-items: center;
    justify-content: center;
}

.image-landscape-page img {
    /*
     * A4 (landscape) = 21cm de altura e 29,7cm de largura.
     * Margens de 2cm em cada lado => altura útil 17cm e largura útil 25,7cm.
     */
    max-width: 25.7cm;
    max-height: 17cm;
    object-fit: contain;
}
"""

PLACEHOLDER_WITH_SEPARATOR_PATTERN = re.compile(r"_{2,}(?:\s*[/-]\s*_{2,})+")
PLACEHOLDER_SEGMENT_PATTERN = re.compile(r"_{3,}")
SLIDE_SEPARATOR_PATTERN = re.compile(r"^---+\s*$", re.MULTILINE)

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT_DIR / "docs"
DEFAULT_OUTPUT = ROOT_DIR / "docs.temp"


INTERRUPTED = False
_LAST_SIGNAL: int | None = None


def _handle_termination(signum: int, frame: Any | None) -> None:
    del frame
    global INTERRUPTED, _LAST_SIGNAL
    _LAST_SIGNAL = signum
    if not INTERRUPTED:
        print(
            f"[docs/conversion] 😌 Interrupção solicitada (sinal {signum}). Concluindo tarefas pendentes...",
            file=sys.stderr,
        )
    INTERRUPTED = True


def _register_signal_handlers() -> None:
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handle_termination)
        except (AttributeError, ValueError):  # pragma: no cover - compatibilidade entre plataformas/threads
            continue


class PdfRenderer(Protocol):
    name: str

    def render(self, *, front_matter: dict[str, Any], body_html: str, markdown_file: Path) -> str:
        ...

    @property
    def styles(self) -> str:
        ...


class StandardPdfRenderer:
    name = "standard"

    @property
    def styles(self) -> str:
        return PDF_STYLES

    def render(
        self,
        *,
        front_matter: dict[str, Any],
        body_html: str,
        markdown_file: Path,
    ) -> str:
        del front_matter  # unused para este renderer
        return f"""<!DOCTYPE html>
<html lang=\"pt-BR\">
<head>
<meta charset=\"utf-8\">
<style>{self.styles}</style>
</head>
<body>
{body_html}
</body>
</html>
"""


class SlidePdfRenderer:
    """
    Renderizador de slides em PDF a partir de Markdown.
    
    Converte arquivos Markdown em apresentações PDF com layout landscape 16:9.
    Os slides são separados por linhas contendo apenas '---' ou por headings H1.
    
    Atributos:
        name: Identificador do renderer.
        use_heading_separator: Se True, também separa slides em headings H1.
    """
    
    name = "slide"
    use_heading_separator = True

    @property
    def styles(self) -> str:
        """Retorna os estilos CSS para slides."""
        return SLIDE_PDF_STYLES

    def render(
        self,
        *,
        front_matter: dict[str, Any],
        body_html: str,
        markdown_file: Path,
    ) -> str:
        """
        Renderiza o conteúdo Markdown como slides HTML.
        
        Args:
            front_matter: Metadados YAML do documento.
            body_html: Conteúdo HTML convertido do Markdown (não utilizado diretamente).
            markdown_file: Caminho do arquivo Markdown original.
        
        Returns:
            String HTML completa com todos os slides formatados.
        """
        markdown_text = markdown_file.read_text(encoding="utf-8")
        _, body = parse_front_matter(markdown_text)
        
        slides_html = self._build_slides(body, front_matter, markdown_file)
        
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<style>{self.styles}</style>
</head>
<body>
{slides_html}
</body>
</html>
"""

    def _build_slides(self, body: str, front_matter: dict[str, Any], markdown_file: Path) -> str:
        """
        Constrói os slides a partir do corpo do Markdown.
        
        Args:
            body: Corpo do documento Markdown (sem front matter).
            front_matter: Metadados do documento.
            markdown_file: Arquivo fonte.
        
        Returns:
            HTML com todos os slides.
        """
        title_slide = self._build_title_slide(front_matter, markdown_file)
        
        raw_slides = SLIDE_SEPARATOR_PATTERN.split(body)
        slides_html = []
        slide_number = 1
        
        if title_slide:
            slides_html.append(title_slide)
            slide_number += 1
        
        for raw_slide in raw_slides:
            content = raw_slide.strip()
            if not content:
                continue
            
            if self.use_heading_separator:
                sub_slides = self._split_by_headings(content)
            else:
                sub_slides = [content]
            
            for sub_content in sub_slides:
                if sub_content.strip():
                    slide_html = self._render_single_slide(sub_content, slide_number)
                    slides_html.append(slide_html)
                    slide_number += 1
        
        return "\n".join(slides_html)

    def render_from_files(
        self,
        files: Sequence[Path],
        directory_name: str,
    ) -> str:
        """
        Renderiza múltiplos arquivos Markdown como slides (um arquivo = um slide).
        
        Args:
            files: Lista de arquivos Markdown ordenados.
            directory_name: Nome do diretório (usado como título se não houver index).
        
        Returns:
            String HTML completa com todos os slides.
        """
        slides_html = []
        slide_number = 1
        front_matter_global: dict[str, Any] = {}
        
        # Procura por arquivo index.md ou 00-*.md para metadados do título
        for md_file in files:
            name_lower = md_file.stem.lower()
            if name_lower == "index" or name_lower.startswith("00"):
                markdown_text = md_file.read_text(encoding="utf-8")
                front_matter_global, _ = parse_front_matter(markdown_text)
                break
        
        # Slide de título
        if front_matter_global.get("title"):
            title_slide = self._build_title_slide(front_matter_global, files[0])
            if title_slide:
                slides_html.append(title_slide)
                slide_number += 1
        else:
            # Título baseado no nome do diretório
            title_escaped = html.escape(directory_name.replace("-", " ").replace("_", " ").title())
            slides_html.append(f"""
<div class="slide-title">
  <h1>{title_escaped}</h1>
</div>
""")
            slide_number += 1
        
        # Cada arquivo como um slide
        for md_file in files:
            name_lower = md_file.stem.lower()
            # Pula index.md pois já foi usado para título
            if name_lower == "index":
                continue
            
            markdown_text = md_file.read_text(encoding="utf-8")
            front_matter, body = parse_front_matter(markdown_text)
            
            content = body.strip() if body.strip() else markdown_text.strip()
            if not content:
                continue
            
            # Renderiza o conteúdo do arquivo como slide
            # No modo diretório, não divide por ---, trata como <hr>
            slide_html = self._render_single_slide(content, slide_number, split_by_separator=False)
            slides_html.append(slide_html)
            slide_number += 1
        
        all_slides = "\n".join(slides_html)
        
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<style>{self.styles}</style>
</head>
<body>
{all_slides}
</body>
</html>
"""

    def _split_by_headings(self, content: str) -> list[str]:
        """
        Divide o conteúdo por headings H1 (linhas iniciando com # ).
        
        Args:
            content: Texto Markdown a ser dividido.
        
        Returns:
            Lista de segmentos de conteúdo.
        """
        heading_pattern = re.compile(r"^(?=# [^#])", re.MULTILINE)
        parts = heading_pattern.split(content)
        return [p.strip() for p in parts if p.strip()]

    def _build_title_slide(self, front_matter: dict[str, Any], markdown_file: Path) -> str:
        """
        Constrói o slide de título a partir dos metadados.
        
        Args:
            front_matter: Metadados YAML do documento.
            markdown_file: Arquivo fonte (fallback para título).
        
        Returns:
            HTML do slide de título ou string vazia se não houver título.
        """
        title = front_matter.get("title", "")
        if not title:
            return ""
        
        subtitle = front_matter.get("subtitle", "") or front_matter.get("description", "")
        authors = front_matter.get("authors", [])
        if isinstance(authors, str):
            authors = [authors]
        date = front_matter.get("date", "")
        
        title_escaped = html.escape(str(title))
        subtitle_html = f'<div class="subtitle">{html.escape(str(subtitle))}</div>' if subtitle else ""
        
        authors_text = ", ".join(html.escape(str(a)) for a in authors) if authors else ""
        authors_html = f'<div class="authors">{authors_text}</div>' if authors_text else ""
        
        date_str = str(date) if date else ""
        date_html = f'<div class="date">{html.escape(date_str)}</div>' if date_str else ""
        
        return f"""
<div class="slide-title">
  <h1>{title_escaped}</h1>
  {subtitle_html}
  {authors_html}
  {date_html}
</div>
"""

    def _render_single_slide(
        self,
        content: str,
        slide_number: int,
        *,
        split_by_separator: bool = True,
    ) -> str:
        """
        Renderiza um único slide.
        
        Args:
            content: Conteúdo Markdown do slide.
            slide_number: Número do slide para exibição.
            split_by_separator: Se False, mantém '---' como <hr> (modo diretório).
        
        Returns:
            HTML do slide formatado.
        """
        content = preserve_placeholder_underscores(content)
        html_content = markdown(
            content,
            extensions=["extra", "toc", "sane_lists", "codehilite"],
            output_format="html5",
        )
        
        return f"""
<div class="slide">
  {html_content}
  <div class="slide-number">{slide_number}</div>
</div>
"""


class AbntPdfRenderer:
    name = "abnt"
    _required_fields = (
        "institution",
        "course",
        "nature",
        "city",
        "state",
        "year",
    )

    @property
    def styles(self) -> str:
        return ABNT_PDF_STYLES

    def render(
        self,
        *,
        front_matter: dict[str, Any],
        body_html: str,
        markdown_file: Path,
    ) -> str:
        abnt_config = self._extract_abnt_config(front_matter)
        missing_fields = [field for field in self._required_fields if not abnt_config.get(field)]
        if missing_fields:
            joined = ", ".join(missing_fields)
            raise ValueError(
                """
É necessário informar os campos obrigatórios para formatação ABNT no bloco 'abnt' do front matter: {fields}
                """.strip().format(fields=joined),
            )

        title = self._escape((front_matter.get("title") or markdown_file.stem).upper())
        authors = self._build_authors(front_matter)

        cover_html = self._build_cover_html(abnt_config, title, authors)
        return f"""<!DOCTYPE html>
<html lang=\"pt-BR\">
<head>
<meta charset=\"utf-8\">
<style>{self.styles}</style>
</head>
<body>
{cover_html}
<div class=\"abnt-content\">
{body_html}
</div>
</body>
</html>
"""

    def _extract_abnt_config(self, front_matter: dict[str, Any]) -> dict[str, Any]:
        abnt_section = front_matter.get("abnt")
        if isinstance(abnt_section, dict):
            return abnt_section
        raise ValueError(
            """
Para utilizar o modo ABNT é necessário definir um bloco 'abnt' no front matter com os metadados exigidos.
            """.strip(),
        )

    def _build_authors(self, front_matter: dict[str, Any]) -> list[str]:
        authors_field = front_matter.get("authors")
        if isinstance(authors_field, str):
            return [self._escape(authors_field)]
        if isinstance(authors_field, Iterable):
            return [self._escape(str(item)) for item in authors_field]
        return []

    def _build_cover_html(self, config: dict[str, Any], title: str, authors: list[str]) -> str:
        institution = self._escape(config.get("institution", ""))
        course = self._escape(config.get("course", ""))
        campus = self._escape(config.get("campus")) if config.get("campus") else ""
        department = self._escape(config.get("department")) if config.get("department") else ""
        discipline = self._escape(config.get("discipline")) if config.get("discipline") else ""
        nature = self._escape(config.get("nature", ""))
        nature_details = config.get("natureDetails")
        if nature_details:
            nature += f" {self._escape(nature_details)}"

        advisor_block = self._build_person_block(config.get("advisor"), label="Orientador")
        coadvisor_block = self._build_person_block(config.get("coAdvisor"), label="Coorientador")

        student_id = self._escape(config.get("studentId")) if config.get("studentId") else ""
        city = self._escape(config.get("city", ""))
        state = self._escape(config.get("state", ""))
        year = self._escape(config.get("year", ""))

        students_html = "".join(f"<div>{author}</div>" for author in authors) or ""
        if student_id:
            students_html += f"<div>{student_id}</div>"

        advisor_html = ""
        if advisor_block:
            advisor_html += f"<div>{advisor_block}</div>"
        if coadvisor_block:
            advisor_html += f"<div>{coadvisor_block}</div>"

        additional_lines = ""
        for label, value in ("Campus", campus), ("Departamento", department), ("Disciplina", discipline):
            if value:
                additional_lines += f"<div class=\"supplement\">{label}: {value}</div>"

        return f"""
<div class=\"abnt-cover\">
  <div class=\"institution\">{institution}</div>
  {additional_lines}
  <div class=\"course\">{course}</div>
  <div class=\"students\">{students_html}</div>
  <div class=\"title\">{title}</div>
  <div class=\"nature-block\">{nature}</div>
  <div class=\"advisor-block\">{advisor_html}</div>
  <div class=\"footer\">
    <span>{city} - {state}</span>
    <span>{year}</span>
  </div>
</div>
<div class=\"page-break\"></div>
"""

    def _build_person_block(self, person_data: Any, *, label: str) -> str:
        if not person_data:
            return ""
        if isinstance(person_data, str):
            return f"{label}: {self._escape(person_data)}"
        if isinstance(person_data, dict):
            name = self._escape(person_data.get("name", ""))
            title = self._escape(person_data.get("title")) if person_data.get("title") else ""
            institution = self._escape(person_data.get("institution")) if person_data.get("institution") else ""
            segments = [segment for segment in (label + ": " + name if name else "", title, institution) if segment]
            return " - ".join(segments)
        return label

    def _escape(self, value: Any) -> str:
        return html.escape(str(value))


STANDARD_RENDERER = StandardPdfRenderer()
ABNT_RENDERER = AbntPdfRenderer()
SLIDE_RENDERER = SlidePdfRenderer()

def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Markdown files to PDF and store them under docs.temp/",
    )
    parser.add_argument(
        "sources",
        nargs="*",
        default=[str(DEFAULT_SOURCE)],
        help="Markdown files or directories to convert. Defaults to the docs/ directory.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Destination directory for generated PDFs. Defaults to docs.temp/.",
    )
    parser.add_argument(
        "--abnt",
        action="store_true",
        help="Gera os PDFs no formato ABNT com capa e metadados provenientes do bloco 'abnt'.",
    )
    parser.add_argument(
        "--slide",
        action="store_true",
        help="Converte Markdown em slides PDF (formato 16:9). Use '---' para separar slides ou passe um diretório onde cada arquivo .md é um slide.",
    )
    parser.add_argument(
        "--slide-name",
        default="",
        help="Nome do arquivo PDF de slides quando usado com diretório. Padrão: nome do diretório.",
    )
    return parser.parse_args(argv)


def discover_markdown_files(sources: Iterable[str], *, slide_mode: bool = False) -> Sequence[Tuple[Path, Path]]:
    """
    Descobre arquivos Markdown nas fontes especificadas.
    
    Args:
        sources: Lista de caminhos (arquivos ou diretórios).
        slide_mode: Se True, não faz busca recursiva em diretórios (para modo slide de diretório).
    
    Returns:
        Lista de tuplas (raiz, arquivo_md).
    """
    discovered: list[Tuple[Path, Path]] = []
    for src in sources:
        source_path = Path(src).expanduser().resolve()
        if source_path.is_dir():
            if slide_mode:
                # No modo slide, apenas arquivos .md diretamente no diretório (não recursivo)
                md_files = sorted(source_path.glob("*.md"))
            else:
                md_files = sorted(source_path.rglob("*.md"))
            for md_file in md_files:
                if md_file.is_file():
                    discovered.append((source_path, md_file))
        elif source_path.is_file() and source_path.suffix.lower() == ".md":
            discovered.append((source_path.parent, source_path))
        else:
            print(f"[docs/conversion] ⚠️ Ignoring invalid path: {source_path}", file=sys.stderr)
    return discovered


def discover_slide_directories(sources: Iterable[str]) -> list[Path]:
    """
    Identifica diretórios nas fontes especificadas (para modo slide de diretório).
    
    Args:
        sources: Lista de caminhos.
    
    Returns:
        Lista de diretórios encontrados.
    """
    directories: list[Path] = []
    for src in sources:
        source_path = Path(src).expanduser().resolve()
        if source_path.is_dir():
            directories.append(source_path)
    return directories


def ensure_output_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def parse_front_matter(markdown_text: str) -> tuple[dict[str, Any], str]:
    stripped = markdown_text.lstrip()
    if not stripped.startswith("---"):
        return {}, markdown_text

    lines = markdown_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, markdown_text

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            front_matter_text = "\n".join(lines[1:index])
            body_lines = lines[index + 1 :]
            body = "\n".join(body_lines)
            try:
                data = yaml.safe_load(front_matter_text) or {}
            except yaml.YAMLError:
                print("[docs/conversion] ⚠️ Falha ao interpretar o front matter YAML.", file=sys.stderr)
                return {}, markdown_text

            if isinstance(data, dict):
                return data, body
            return {}, body
    return {}, markdown_text


def preserve_placeholder_underscores(text: str) -> str:
    def escape(match: re.Match[str]) -> str:
        return match.group(0).replace("_", "\\_")

    updated = PLACEHOLDER_WITH_SEPARATOR_PATTERN.sub(escape, text)
    return PLACEHOLDER_SEGMENT_PATTERN.sub(escape, updated)


def _read_png_dimensions(image_path: Path) -> tuple[int, int] | None:
    """Lê dimensões (width, height) de um PNG sem dependências externas."""
    try:
        with image_path.open("rb") as handler:
            signature = handler.read(8)
            if signature != b"\x89PNG\r\n\x1a\n":
                return None
            _length = handler.read(4)
            chunk_type = handler.read(4)
            if chunk_type != b"IHDR":
                return None
            data = handler.read(8)
    except OSError:
        return None

    if len(data) != 8:
        return None
    width, height = struct.unpack(">II", data)
    return int(width), int(height)


def _read_jpeg_dimensions(image_path: Path) -> tuple[int, int] | None:
    """Lê dimensões (width, height) de um JPEG sem dependências externas."""
    try:
        with image_path.open("rb") as handler:
            if handler.read(2) != b"\xff\xd8":
                return None
            while True:
                marker_prefix = handler.read(1)
                if not marker_prefix:
                    return None
                if marker_prefix != b"\xff":
                    continue
                marker = handler.read(1)
                if not marker or marker == b"\xd9":
                    return None

                while marker == b"\xff":
                    marker = handler.read(1)
                    if not marker:
                        return None

                if marker in {b"\xc0", b"\xc1", b"\xc2", b"\xc3", b"\xc5", b"\xc6", b"\xc7", b"\xc9", b"\xca", b"\xcb", b"\xcd", b"\xce", b"\xcf"}:
                    segment_length_raw = handler.read(2)
                    if len(segment_length_raw) != 2:
                        return None
                    _segment_length = struct.unpack(">H", segment_length_raw)[0]
                    precision = handler.read(1)
                    if not precision:
                        return None
                    height_width = handler.read(4)
                    if len(height_width) != 4:
                        return None
                    height, width = struct.unpack(">HH", height_width)
                    return int(width), int(height)

                segment_length_raw = handler.read(2)
                if len(segment_length_raw) != 2:
                    return None
                segment_length = struct.unpack(">H", segment_length_raw)[0]
                if segment_length < 2:
                    return None
                handler.seek(segment_length - 2, 1)
    except OSError:
        return None


def _read_image_dimensions(image_path: Path) -> tuple[int, int] | None:
    """Lê dimensões de PNG/JPEG a partir do arquivo local."""
    suffix = image_path.suffix.lower()
    if suffix == ".png":
        return _read_png_dimensions(image_path)
    if suffix in {".jpg", ".jpeg"}:
        return _read_jpeg_dimensions(image_path)
    return None


def _postprocess_images_html(body_html: str, *, base_dir: Path) -> str:
    """Ajusta imagens no HTML para caber na página e cria página landscape para imagens horizontais."""
    img_pattern = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)

    def replace(match: re.Match[str]) -> str:
        img_tag = match.group(0)
        src = match.group(1).strip()
        if not src or src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
            return f'<div class="image-portrait">{img_tag}</div>'

        image_path = (base_dir / src).resolve() if not Path(src).is_absolute() else Path(src)
        dims = _read_image_dimensions(image_path)
        if not dims:
            return f'<div class="image-portrait">{img_tag}</div>'

        width, height = dims
        if width > height:
            return f'<div class="image-landscape-page">{img_tag}</div>'
        return f'<div class="image-portrait">{img_tag}</div>'

    return img_pattern.sub(replace, body_html)


def build_pdf_metadata(front_matter: dict[str, Any], fallback_title: str) -> DocumentMetadataType | None:
    if not front_matter:
        return None

    title = front_matter.get("title") or fallback_title

    authors_field = front_matter.get("authors")
    if isinstance(authors_field, str):
        authors = [authors_field]
    elif isinstance(authors_field, Iterable):
        authors = [str(item) for item in authors_field]
    else:
        authors = None

    subject = front_matter.get("summary") or front_matter.get("description")

    keywords_field = front_matter.get("tags") or front_matter.get("keywords")
    if isinstance(keywords_field, str):
        keywords = [keywords_field]
    elif isinstance(keywords_field, Iterable):
        keywords = [str(item) for item in keywords_field]
    else:
        keywords = None

    created_value = front_matter.get("date") or front_matter.get("created")
    created_iso = None
    if isinstance(created_value, datetime):
        created_iso = created_value.isoformat()
    elif isinstance(created_value, str):
        try:
            created_iso = datetime.fromisoformat(created_value).isoformat()
        except ValueError:
            created_iso = created_value

    language = front_matter.get("language")

    metadata_kwargs: dict[str, Any] = {"title": title}
    if authors:
        metadata_kwargs["authors"] = authors
    if subject:
        metadata_kwargs["description"] = subject
    if keywords:
        metadata_kwargs["keywords"] = keywords
    if created_iso:
        metadata_kwargs["created"] = created_iso
    if language:
        metadata_kwargs["lang"] = language

    if len(metadata_kwargs) == 1 or DocumentMetadata is None:
        return None

    return DocumentMetadata(**metadata_kwargs)


def convert_markdown_file(
    markdown_file: Path,
    output_dir: Path,
    root: Path,
    *,
    renderer: PdfRenderer,
) -> Path:
    relative_path = markdown_file.relative_to(root)
    target_pdf = output_dir.joinpath(relative_path).with_suffix(".pdf")
    ensure_output_directory(target_pdf.parent)

    markdown_text = markdown_file.read_text(encoding="utf-8")
    front_matter, body = parse_front_matter(markdown_text)
    metadata = build_pdf_metadata(front_matter, markdown_file.stem)

    source_markdown = body if body.strip() else markdown_text
    source_markdown = preserve_placeholder_underscores(source_markdown)
    html_content = markdown(
        source_markdown,
        extensions=["extra", "toc", "sane_lists"],
        output_format="html5",
    )

    html_content = _postprocess_images_html(html_content, base_dir=markdown_file.parent)

    styled_html = renderer.render(
        front_matter=front_matter,
        body_html=html_content,
        markdown_file=markdown_file,
    )

    if HTML is None:
        raise RuntimeError("Dependência 'weasyprint' indisponível no ambiente atual.")

    html = HTML(string=styled_html, base_url=str(markdown_file.parent))
    document = html.render()

    if metadata:
        document.metadata = metadata

    document.write_pdf(str(target_pdf))
    return target_pdf


def convert_all(
    files: Sequence[Tuple[Path, Path]],
    output_dir: Path,
    *,
    renderer: PdfRenderer,
) -> Tuple[int, list[tuple[Path, str]]]:
    converted = 0
    failures: list[tuple[Path, str]] = []

    for root, markdown_file in files:
        if INTERRUPTED:
            print(
                "[docs/conversion] 😴 Conversão interrompida. Finalizando processamento restante com segurança...",
                file=sys.stderr,
            )
            break
        try:
            pdf_path = convert_markdown_file(
                markdown_file,
                output_dir,
                root,
                renderer=renderer,
            )
        except Exception as error:  # pragma: no cover - fluxo de erro operacional
            failures.append((markdown_file, str(error)))
            print(
                f"[docs/conversion] ❌ Erro ao converter '{markdown_file}': {error}",
                file=sys.stderr,
            )
            continue

        converted += 1
        print(f"[docs/conversion] ✅ {markdown_file} -> {pdf_path}")

    return converted, failures


def main(argv: Sequence[str] | None = None) -> int:
    _register_signal_handlers()
    args = parse_args(argv or sys.argv[1:])
    files = discover_markdown_files(args.sources)

    if not files:
        print("[docs/conversion] ❌ Nenhum arquivo Markdown encontrado para conversão.", file=sys.stderr)
        return 1

    output_dir = Path(args.output).expanduser().resolve()
    ensure_output_directory(output_dir)

    if HTML is None:
        install_hint = "pip install weasyprint"
        import_detail = f" Detalhe: {WEASYPRINT_IMPORT_ERROR}" if WEASYPRINT_IMPORT_ERROR else ""
        print(
            f"[docs/conversion] ❌ Dependência ausente: 'weasyprint'. Instale-a executando: {install_hint}.{import_detail}",
            file=sys.stderr,
        )
        return 2

    if args.slide:
        renderer = SLIDE_RENDERER
        
        # Verifica se há diretórios nas fontes (modo diretório de slides)
        slide_dirs = discover_slide_directories(args.sources)
        
        if slide_dirs:
            # Modo diretório: combina múltiplos arquivos em um único PDF
            converted_count = 0
            failures: list[tuple[Path, str]] = []
            
            for slide_dir in slide_dirs:
                if INTERRUPTED:
                    break
                
                # Descobre arquivos .md no diretório (não recursivo)
                dir_files = discover_markdown_files([str(slide_dir)], slide_mode=True)
                if not dir_files:
                    print(f"[docs/conversion] ⚠️ Nenhum arquivo .md em '{slide_dir}'", file=sys.stderr)
                    continue
                
                # Ordena arquivos por nome
                md_files = sorted([f[1] for f in dir_files], key=lambda p: p.name)
                
                # Nome do PDF
                pdf_name = args.slide_name if args.slide_name else slide_dir.name
                target_pdf = output_dir / f"{pdf_name}.pdf"
                ensure_output_directory(target_pdf.parent)
                
                try:
                    styled_html = renderer.render_from_files(md_files, slide_dir.name)
                    
                    html_doc = HTML(string=styled_html, base_url=str(slide_dir))
                    document = html_doc.render()
                    document.write_pdf(str(target_pdf))
                    
                    converted_count += 1
                    print(f"[docs/conversion] ✅ {slide_dir}/ ({len(md_files)} slides) -> {target_pdf}")
                except Exception as error:
                    failures.append((slide_dir, str(error)))
                    print(f"[docs/conversion] ❌ Erro ao converter '{slide_dir}': {error}", file=sys.stderr)
            
            print(f"[docs/conversion] 📊 Total de PDFs de slides gerados: {converted_count}")
            
            if failures:
                print(
                    f"[docs/conversion] ⚠️ Conversões com falha: {len(failures)}.",
                    file=sys.stderr,
                )
                return 3
            return 0
        
        # Modo arquivo único: processa normalmente
        files = discover_markdown_files(args.sources)
    elif args.abnt:
        renderer = ABNT_RENDERER
    else:
        renderer = STANDARD_RENDERER

    converted_count, failures = convert_all(files, output_dir, renderer=renderer)
    print(f"[docs/conversion] 📊 Total de PDFs gerados: {converted_count}")

    if failures:
        print(
            f"[docs/conversion] ⚠️ Conversões com falha: {len(failures)}. Consulte os logs acima para detalhes.",
            file=sys.stderr,
        )
        return 3

    if INTERRUPTED:
        signal_note = f" (sinal {_LAST_SIGNAL})" if _LAST_SIGNAL is not None else ""
        print(
            f"[docs/conversion] 🙂 Execução concluída após pedido de interrupção{signal_note}.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
