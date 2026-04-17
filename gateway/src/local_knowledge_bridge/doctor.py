from __future__ import annotations

import time
from pathlib import Path

from .config import enabled_endnote_libraries, load_config
from .paths import version_path
from .retrieval import index_status
from .source_guard import endnote_data_dir, resolve_endnote_components, validate_obsidian_vault
from .versioning import get_version_status, load_app_version


def _safe_detail_message(exc: BaseException) -> str:
    return str(exc).strip() or exc.__class__.__name__


def _obsidian_source_status(config: dict) -> dict:
    obsidian_path = str(config.get("obsidian_vault", "") or "").strip()
    if not obsidian_path:
        return {
            "configured": False,
            "available": False,
            "compatible": False,
            "suggest_update": False,
            "detail": "Obsidian vault is not configured.",
        }
    try:
        validate_obsidian_vault(obsidian_path)
    except SystemExit as exc:
        return {
            "configured": True,
            "available": False,
            "compatible": False,
            "suggest_update": False,
            "detail": _safe_detail_message(exc),
        }
    return {
        "configured": True,
        "available": True,
        "compatible": True,
        "suggest_update": False,
        "detail": "Obsidian vault is configured and readable.",
    }


def _endnote_source_status(config: dict) -> tuple[dict, dict]:
    libraries = enabled_endnote_libraries(config)
    auth_status = {
        "authorized": True,
        "status": "not_applicable",
        "detail": "Local Knowledge Bridge does not implement EndNote licensing.",
    }
    if not libraries:
        return (
            {
                "configured": False,
                "available": False,
                "compatible": False,
                "suggest_update": False,
                "authorized": True,
                "detail": "EndNote library is not configured.",
            },
            auth_status,
        )

    details: list[str] = []
    available = True
    compatible = True
    suggest_update = False
    for item in libraries:
        library_name = item["name"]
        try:
            components = resolve_endnote_components(item["path"])
        except SystemExit as exc:
            available = False
            compatible = False
            details.append(f"{library_name}: {_safe_detail_message(exc)}")
            continue

        layout = str(components["layout"])
        if layout == "modern":
            details.append(f"{library_name}: EndNote database schema is readable and matches expected fields.")
        elif layout == "legacy":
            compatible = True
            suggest_update = True
            details.append(f"{library_name}: legacy EndNote layout detected; metadata support is limited and PDF-first fallback may be used.")
        else:
            suggest_update = True
            details.append(f"{library_name}: EndNote data directory is readable but no database was found; PDF-only indexing will be used if PDFs exist.")

    return (
        {
            "configured": True,
            "available": available,
            "compatible": compatible,
            "suggest_update": suggest_update,
            "authorized": True,
            "detail": " | ".join(details),
        },
        auth_status,
    )


def get_source_compatibility_status(config: dict, force_refresh: bool = False) -> dict:
    del force_refresh
    obsidian_status = _obsidian_source_status(config)
    endnote_status, _ = _endnote_source_status(config)
    return {
        "obsidian": obsidian_status,
        "endnote": endnote_status,
    }


def _obsidian_change_status(config: dict, build_timestamp: float | None) -> tuple[bool, bool, int]:
    obsidian_path = str(config.get("obsidian_vault", "") or "").strip()
    if not obsidian_path:
        return False, False, 0
    try:
        vault = validate_obsidian_vault(obsidian_path)
    except SystemExit:
        return False, False, 0

    exclude_dirs = set(config.get("exclude_dirs", []) or [])
    changed_count = 0
    for path in vault.rglob("*.md"):
        if any(part in exclude_dirs for part in path.parts):
            continue
        if build_timestamp and path.stat().st_mtime > build_timestamp:
            changed_count += 1

    if build_timestamp is None:
        return True, False, changed_count

    threshold = int(config.get("index", {}).get("obsidian_stale_note_threshold", 3))
    if changed_count >= threshold:
        return True, False, changed_count
    if changed_count > 0:
        return False, True, changed_count
    return False, False, 0


def _endnote_change_status(config: dict, build_timestamp: float | None) -> tuple[bool, bool, int]:
    libraries = enabled_endnote_libraries(config)
    if not libraries:
        return False, False, 0

    changed_pdfs = 0
    db_changed = False
    for item in libraries:
        try:
            components = resolve_endnote_components(item["path"])
        except SystemExit:
            return True, False, 0
        db_path = Path(components["db_path"]) if components["db_path"] else None
        pdf_dir = Path(components["pdf_dir"])
        if build_timestamp is None:
            if db_path and db_path.exists():
                db_changed = True
            if pdf_dir.exists():
                changed_pdfs += sum(1 for path in pdf_dir.rglob("*.pdf"))
            continue
        if db_path and db_path.exists() and db_path.stat().st_mtime > build_timestamp:
            db_changed = True
        if pdf_dir.exists():
            changed_pdfs += sum(1 for path in pdf_dir.rglob("*.pdf") if path.stat().st_mtime > build_timestamp)

    if build_timestamp is None:
        return True, False, changed_pdfs

    pdf_threshold = int(config.get("index", {}).get("endnote_stale_pdf_count_threshold", 5))
    if db_changed or changed_pdfs >= pdf_threshold:
        return True, False, changed_pdfs
    if changed_pdfs > 0:
        return False, True, changed_pdfs
    return False, False, 0


def _normalized_index_status(config: dict, source_status: dict) -> dict:
    status = index_status(config)
    meta = status.get("meta", {})
    completed_at = meta.get("last_build_completed_at")
    if isinstance(completed_at, str):
        try:
            completed_at = float(completed_at)
        except ValueError:
            completed_at = None
    stale_age_days = None
    if completed_at:
        stale_age_days = round((time.time() - float(completed_at)) / 86400.0, 3)

    obsidian_stale, obsidian_minor_change, obsidian_changed_notes = _obsidian_change_status(config, completed_at)
    endnote_stale, endnote_minor_change, endnote_changed_pdfs = _endnote_change_status(config, completed_at)

    warning_after_days = float(config.get("index", {}).get("stale_warning_after_days", 7))
    if stale_age_days is not None and stale_age_days >= warning_after_days:
        if source_status.get("obsidian", {}).get("configured"):
            obsidian_stale = True
        if source_status.get("endnote", {}).get("configured"):
            endnote_stale = True

    return {
        **status,
        "obsidian_available": bool(source_status.get("obsidian", {}).get("available")),
        "endnote_available": bool(source_status.get("endnote", {}).get("available")),
        "obsidian_stale": bool(obsidian_stale),
        "endnote_stale": bool(endnote_stale),
        "obsidian_minor_change": bool(obsidian_minor_change),
        "endnote_minor_change": bool(endnote_minor_change),
        "stale_age_days": stale_age_days,
        "obsidian_changed_notes": obsidian_changed_notes,
        "endnote_changed_pdfs": endnote_changed_pdfs,
    }


def diagnose_gateway(config: dict | None = None, *, force_refresh: bool = False) -> dict:
    config = config or load_config()
    version_status = get_version_status(force_refresh=force_refresh)
    source_status = get_source_compatibility_status(config, force_refresh=force_refresh)
    endnote_status, auth_status = _endnote_source_status(config)
    source_status["endnote"] = endnote_status

    configured_sources = {
        "obsidian": bool(str(config.get("obsidian_vault", "") or "").strip()),
        "endnote": len(enabled_endnote_libraries(config)) > 0,
    }
    usable_sources = [
        name
        for name, item in source_status.items()
        if name in {"obsidian", "endnote"}
        and isinstance(item, dict)
        and item.get("configured")
        and item.get("available")
        and item.get("compatible")
    ]
    needs_update = bool(version_status.get("update_available")) or any(
        item.get("configured") and item.get("available") and not item.get("compatible")
        for item in source_status.values()
        if isinstance(item, dict)
    )
    index_info = _normalized_index_status(config, source_status)

    return {
        "app_version": load_app_version(),
        "configured_sources": configured_sources,
        "usable_sources": usable_sources,
        "needs_update": needs_update,
        "version_status": version_status,
        "source_status": source_status,
        "authorization_status": {"endnote": auth_status},
        "index_status": index_info,
    }


def render_doctor(report: dict, service_health: dict | None = None) -> str:
    lines = [f"APP VERSION: {report['app_version']}", ""]

    version_status = report.get("version_status") or {}
    lines.append("VERSION:")
    lines.append(f"- current: {version_status.get('current_version')}")
    lines.append(f"- latest: {version_status.get('latest_version')}")
    lines.append(f"- update_available: {bool(version_status.get('update_available'))}")
    lines.append(f"- source: {version_status.get('source')}")
    if version_status.get("error"):
        lines.append(f"- error: {version_status.get('error')}")
    lines.append("")

    lines.append("SOURCES:")
    source_status = report.get("source_status") or {}
    for key in ("obsidian", "endnote"):
        item = source_status.get(key) or {}
        lines.append(
            f"- {key}: configured={bool(item.get('configured'))}"
            f" | available={bool(item.get('available'))}"
            f" | compatible={bool(item.get('compatible'))}"
            f" | suggest_update={bool(item.get('suggest_update'))}"
        )
        if item.get("detail"):
            lines.append(f"  detail: {item.get('detail')}")
        if key == "endnote":
            lines.append(f"  authorized: {bool(item.get('authorized', True))}")
    lines.append("")

    lines.append("AUTHORIZATION:")
    auth_status = (report.get("authorization_status") or {}).get("endnote") or {}
    lines.append(f"- endnote_authorized: {bool(auth_status.get('authorized', True))}")
    lines.append(f"- endnote_status: {auth_status.get('status')}")
    if auth_status.get("detail"):
        lines.append(f"- endnote_detail: {auth_status.get('detail')}")
    lines.append("")

    lines.append("INDEX:")
    index_info = report.get("index_status") or {}
    for key in (
        "exists",
        "obsidian_available",
        "endnote_available",
        "obsidian_stale",
        "endnote_stale",
        "obsidian_minor_change",
        "endnote_minor_change",
    ):
        if key in index_info:
            lines.append(f"- {key}: {index_info.get(key)}")
    if "stale_age_days" in index_info:
        lines.append(f"- stale_age_days: {index_info.get('stale_age_days')}")
    if index_info.get("db_path"):
        lines.append(f"- db_path: {index_info.get('db_path')}")
    for table_name, count in (index_info.get("counts") or {}).items():
        lines.append(f"- {table_name}: {count}")
    lines.append("")

    lines.append("SERVICE:")
    service = service_health or {"running": False}
    lines.append(f"- running: {bool(service.get('running'))}")
    if service.get("service"):
        info = service["service"]
        lines.append(f"- host: {info.get('host')}")
        lines.append(f"- port: {info.get('port')}")
    if service.get("started_at"):
        lines.append(f"- started_at: {service.get('started_at')}")

    return "\n".join(lines)


def doctor_report(config: dict, service_health: dict | None = None, *, force_refresh: bool = False) -> dict:
    report = diagnose_gateway(config, force_refresh=force_refresh)
    report["service"] = service_health or {"running": False}
    report["obsidian"] = {
        "configured": report["source_status"]["obsidian"]["configured"],
        "path": str(config.get("obsidian_vault", "") or ""),
        "exists": report["source_status"]["obsidian"]["available"],
    }
    report["endnote"] = [
        {
            "id": item["id"],
            "name": item["name"],
            "path": item["path"],
            "library_exists": Path(item["path"]).exists(),
            "data_dir_exists": endnote_data_dir(item["path"]).exists(),
            "enabled": item.get("enabled", True),
        }
        for item in enabled_endnote_libraries(config)
    ]
    return report
