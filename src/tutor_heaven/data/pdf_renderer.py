"""Renderizado de Markdown a PDF con estilo similar a Obsidian.

Convierte archivos .md a .pdf usando WeasyPrint para obtener una
calidad de impresión profesional con soporte completo de Unicode.
"""

from pathlib import Path

import markdown
from weasyprint import HTML

# CSS inspirado en el estilo de Obsidian.
_OBSIDIAN_CSS = """\
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    font-size: 12pt;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 40px auto;
    padding: 0 20px;
}

h1 {
    font-size: 24pt;
    font-weight: 700;
    border-bottom: 2px solid #333;
    padding-bottom: 8px;
    margin-top: 0;
}

h2 {
    font-size: 18pt;
    font-weight: 600;
    margin-top: 28px;
    color: #1a1a1a;
}

h3 {
    font-size: 14pt;
    font-weight: 600;
    margin-top: 20px;
    color: #2a2a2a;
}

p {
    margin: 8px 0;
}

strong {
    font-weight: 600;
}

em {
    font-style: italic;
}

ul, ol {
    padding-left: 24px;
    margin: 8px 0;
}

li {
    margin-bottom: 4px;
}

code {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    background-color: #f0f0f0;
    padding: 2px 4px;
    border-radius: 3px;
    font-size: 10pt;
}

pre {
    background-color: #f5f5f5;
    padding: 12px;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 10pt;
    line-height: 1.4;
}

pre code {
    background-color: transparent;
    padding: 0;
}

blockquote {
    border-left: 4px solid #ddd;
    margin: 8px 0;
    padding: 4px 16px;
    color: #666;
}

hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 16px 0;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
}

th, td {
    border: 1px solid #ddd;
    padding: 8px 12px;
    text-align: left;
}

th {
    background-color: #f5f5f5;
    font-weight: 600;
}
"""


def render_markdown_to_pdf(md_content: str, output_path: Path) -> None:
    """Convierte contenido Markdown a un archivo PDF.

    Usa WeasyPrint para renderizar HTML con CSS, obteniendo una
    calidad similar a la exportación de Obsidian.
    """
    html_body = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "sane_lists"],
    )

    full_html = (
        "<!DOCTYPE html>\n"
        "<html><head>"
        f"<style>{_OBSIDIAN_CSS}</style>"
        "</head><body>"
        f"{html_body}"
        "</body></html>"
    )

    HTML(string=full_html).write_pdf(str(output_path))
