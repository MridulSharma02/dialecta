from __future__ import annotations
import os
from typing import Any

from jinja2 import Environment, FileSystemLoader

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


def generate_pdf_report(report: dict[str, Any]) -> bytes:
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
        overview=report.get("overview", {}),
        summary=report.get("summary", {}),
        topic_decomposition=report.get("topic_decomposition", []),
        sub_debates=report.get("sub_debates", []),
        improvement_log=report.get("improvement_log", []),
        meta_evaluation=report.get("meta_evaluation", {}),
        final_verdict=report.get("final_verdict", {}),
        transcript=report.get("transcript", []),
    )

    pdf_bytes = WeasyprintHTML(string=rendered_html).write_pdf()
    return pdf_bytes