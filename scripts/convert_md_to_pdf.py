#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import re
import signal
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
"""

PLACEHOLDER_WITH_SEPARATOR_PATTERN = re.compile(r"_{2,}(?:\s*[/-]\s*_{2,})+")
PLACEHOLDER_SEGMENT_PATTERN = re.compile(r"_{3,}")

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
    return parser.parse_args(argv)


def discover_markdown_files(sources: Iterable[str]) -> Sequence[Tuple[Path, Path]]:
    discovered: list[Tuple[Path, Path]] = []
    for src in sources:
        source_path = Path(src).expanduser().resolve()
        if source_path.is_dir():
            for md_file in sorted(source_path.rglob("*.md")):
                if md_file.is_file():
                    discovered.append((source_path, md_file))
        elif source_path.is_file() and source_path.suffix.lower() == ".md":
            discovered.append((source_path.parent, source_path))
        else:
            print(f"[docs/conversion] ⚠️ Ignoring invalid path: {source_path}", file=sys.stderr)
    return discovered


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

    renderer = ABNT_RENDERER if args.abnt else STANDARD_RENDERER

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
