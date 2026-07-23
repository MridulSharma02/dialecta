from __future__ import annotations
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, JSONResponse

from core.security import get_current_user
from core.errors import DialectaError, ErrorCode
from db.supabase_client import supabase_admin
from reports.generator import assemble_report
from reports.pdf_report import generate_pdf_report
from reports.json_report import generate_json_report
from reports.markdown_report import generate_markdown_report

router = APIRouter(prefix="/reports", tags=["reports"])


# ── Helper: verify debate belongs to user ───────────────────────
async def _get_debate_or_404(debate_id: str, user_id: str) -> dict:
    row = (
        supabase_admin
        .from_("debates")
        .select("*")
        .eq("debate_id", debate_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not row.data:
        raise HTTPException(status_code=404, detail="Debate not found.")
    if row.data.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail="Report only available for completed debates."
        )
    return row.data


# ── GET /reports/history ────────────────────────────────────────
@router.get("/history")
async def get_report_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """
    Returns a paginated list of the user's completed debates
    that have reports available.
    """
    user_id = current_user["user_id"]
    offset = (page - 1) * limit

    rows = (
        supabase_admin
        .from_("debates")
        .select("debate_id, topic, status, winner, quality_score, created_at, completed_at, total_rounds")
        .eq("user_id", user_id)
        .eq("status", "completed")
        .order("completed_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return {
        "page": page,
        "limit": limit,
        "debates": rows.data or [],
    }


# ── GET /reports/{debate_id}/download?format=pdf|json|markdown ──
@router.get("/{debate_id}/download")
async def download_report(
    debate_id: str,
    format: str = Query("pdf", pattern="^(pdf|json|markdown)$"),
    current_user: dict = Depends(get_current_user),
):
    """
    Assembles and streams the report in the requested format.
    Supports: pdf, json, markdown
    """
    user_id = current_user["user_id"]

    # Verify ownership + completion
    await _get_debate_or_404(debate_id, user_id)

    # Assemble the full report data
    report = await assemble_report(debate_id, user_id)

    # ── PDF ──────────────────────────────────────────────────────
    if format == "pdf":
        pdf_bytes = generate_pdf_report(report)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="dialecta_report_{debate_id[:8]}.pdf"'
            },
        )

    # ── JSON ─────────────────────────────────────────────────────
    if format == "json":
        json_str = generate_json_report(report)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="dialecta_report_{debate_id[:8]}.json"'
            },
        )

    # ── Markdown ─────────────────────────────────────────────────
    if format == "markdown":
        md_str = generate_markdown_report(report)
        return Response(
            content=md_str,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="dialecta_report_{debate_id[:8]}.md"'
            },
        )


# ── GET /reports/{debate_id}/preview ────────────────────────────
@router.get("/{debate_id}/preview")
async def preview_report(
    debate_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Returns a lightweight JSON preview of the report
    (summary + sub-debate winners) for the UI report panel.
    No full transcript included.
    """
    user_id = current_user["user_id"]

    await _get_debate_or_404(debate_id, user_id)
    report = await assemble_report(debate_id, user_id)

    preview = {
        "report_id": report["report_id"],
        "generated_at": report["generated_at"],
        "debate": report["debate"],
        "summary": report["summary"],
        "sub_debate_winners": [
            {
                "sub_topic": s.get("sub_topic"),
                "winner": s.get("winner"),
                "rounds_run": s.get("rounds_run"),
            }
            for s in report.get("sub_debates", [])
        ],
    }

    return preview