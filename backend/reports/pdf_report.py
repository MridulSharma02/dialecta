from __future__ import annotations
import os
from typing import Any

from jinja2 import Environment, FileSystemLoader

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


def generate_pdf_report(report: dict[str, Any]) -> bytes:
    """
    Renders report.html via Jinja2 then converts to PDF with WeasyPrint.
    WeasyPrint requires GTK on Windows — works natively on Linux/Render.
    """

    # Lazy import so Windows dev server doesn't crash if GTK is missing
    try:
        from weasyprint import HTML as WeasyprintHTML
    except Exception as e:
        raise RuntimeError(
            "WeasyPrint could not load. On Windows, install GTK3 runtime from "
            "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer "
            f"Original error: {e}"
        )

    env = Environment(
        loader=FileSystemLoader(_TEMPLATES_DIR),
        autoescape=True,
    )
    template = env.get_template("report.html")

    rendered_html = template.render(
        report_id=report["report_id"],
        generated_at=report["generated_at"],
        debate=report["debate"],
        summary=report["summary"],
        sub_debates=report.get("sub_debates", []),
        agent_events=report.get("agent_events", []),
    )

    pdf_bytes = WeasyprintHTML(string=rendered_html).write_pdf()
    return pdf_bytes