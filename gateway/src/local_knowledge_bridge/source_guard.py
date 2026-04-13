from __future__ import annotations

from pathlib import Path

from .config import gateway_local_path
from .paths import gateway_root


def ensure_gateway_output_path(value: str | Path) -> Path:
    path = gateway_local_path(value)
    root = gateway_root().resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"Refusing to use output path outside gateway: {path}") from exc
    return path


def ensure_readable_directory(value: str | Path, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.exists():
        raise SystemExit(f"{label} does not exist: {path}")
    if not path.is_dir():
        raise SystemExit(f"{label} is not a directory: {path}")
    return path


def ensure_readable_file(value: str | Path, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.exists():
        raise SystemExit(f"{label} does not exist: {path}")
    if not path.is_file():
        raise SystemExit(f"{label} is not a file: {path}")
    return path


def validate_obsidian_vault(value: str) -> Path:
    return ensure_readable_directory(value, "Obsidian vault")


def endnote_data_dir(library_path: str | Path) -> Path:
    library = Path(library_path).expanduser()
    if library.suffix.lower() == ".enl":
        return library.with_suffix(".Data")
    return Path(str(library) + ".Data")


def resolve_endnote_components(library_path: str | Path) -> dict[str, Path | str]:
    library = ensure_readable_file(library_path, "EndNote library")
    data_dir = endnote_data_dir(library)
    if not data_dir.exists():
        raise SystemExit(f"EndNote data directory does not exist: {data_dir}")

    modern_db = data_dir / "sdb" / "sdb.eni"
    legacy_db = data_dir / "rdb" / "sdb.eni"
    pdf_dir = data_dir / "PDF"

    if modern_db.exists():
        return {
            "layout": "modern",
            "library": library,
            "data_dir": data_dir,
            "db_path": modern_db,
            "pdf_dir": pdf_dir,
        }
    if legacy_db.exists():
        return {
            "layout": "legacy",
            "library": library,
            "data_dir": data_dir,
            "db_path": legacy_db,
            "pdf_dir": pdf_dir,
        }
    return {
        "layout": "pdf_only",
        "library": library,
        "data_dir": data_dir,
        "db_path": Path(),
        "pdf_dir": pdf_dir,
    }
