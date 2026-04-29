from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from .paths import logs_root


InputFunc = Callable[[str], str]
PrintFunc = Callable[..., None]


@dataclass
class CommandResult:
    args: list[str]
    returncode: int
    elapsed_seconds: float
    log_path: Path

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class TerminalUI:
    def __init__(
        self,
        *,
        input_func: InputFunc | None = None,
        print_func: PrintFunc = print,
        stream: Any | None = None,
    ) -> None:
        self.input = input_func or input
        self.print = print_func
        self.stream = stream or sys.stdout

    def title(self, text: str) -> None:
        self.print("")
        self.print("=" * len(text))
        self.print(text)
        self.print("=" * len(text))

    def section(self, text: str) -> None:
        self.print("")
        self.print(f"-- {text}")

    def item(self, text: str, *, indent: int = 1) -> None:
        self.print(f"{'  ' * indent}- {text}")

    def menu(self, title: str, items: Iterable[tuple[str, str]]) -> None:
        self.section(title)
        for key, label in items:
            self.print(f"  {key}. {label}")

    def status(self, label: str, value: str | bool | int | None) -> None:
        self.print(f"  {label:<18} {value}")

    def prompt(self, label: str, default: str | None = None) -> str:
        suffix = f" [{default}]" if default is not None else ""
        value = self.input(f"{label}{suffix}: ").strip()
        if not value and default is not None:
            return default
        return value

    def confirm(self, label: str, *, default: bool = False) -> bool:
        suffix = "[Y/n]" if default else "[y/N]"
        value = self.input(f"{label} {suffix}: ").strip().lower()
        if not value:
            return default
        return value in {"y", "yes"}

    def start(self, label: str) -> float:
        self.print(f"[RUNNING] {label}")
        return time.monotonic()

    def done(self, label: str, started_at: float) -> None:
        self.print(f"[DONE] {label} ({time.monotonic() - started_at:.1f}s)")

    def failed(self, label: str, started_at: float, detail: str = "") -> None:
        suffix = f" - {detail}" if detail else ""
        self.print(f"[FAILED] {label} ({time.monotonic() - started_at:.1f}s){suffix}")

    def run_task(self, label: str, func: Callable[[], Any]) -> Any:
        started_at = self.start(label)
        try:
            result = func()
        except Exception as exc:
            self.failed(label, started_at, str(exc).strip() or exc.__class__.__name__)
            raise
        self.done(label, started_at)
        return result


def wizard_log_path() -> Path:
    return logs_root() / "wizard.log"


def _command_line(args: list[str]) -> str:
    return " ".join(args)


def run_logged_command(
    args: list[str],
    *,
    label: str,
    cwd: str | Path | None = None,
    log_path: Path | None = None,
    ui: TerminalUI | None = None,
) -> CommandResult:
    ui = ui or TerminalUI()
    log_path = log_path or wizard_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    started_at = ui.start(label)
    with log_path.open("a", encoding="utf-8", errors="replace") as log:
        log.write("\n")
        log.write(f"=== {time.strftime('%Y-%m-%d %H:%M:%S')} {label} ===\n")
        log.write(f"$ {_command_line(args)}\n")
        log.flush()
        try:
            completed = subprocess.run(
                args,
                cwd=str(cwd) if cwd is not None else None,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            returncode = int(completed.returncode)
        except Exception as exc:
            elapsed = time.monotonic() - started_at
            log.write(f"[exception] {exc}\n")
            ui.failed(label, started_at, f"{exc}. log: {log_path}")
            return CommandResult(args=args, returncode=1, elapsed_seconds=elapsed, log_path=log_path)
    elapsed = time.monotonic() - started_at
    result = CommandResult(args=args, returncode=returncode, elapsed_seconds=elapsed, log_path=log_path)
    if result.ok:
        ui.done(label, started_at)
    else:
        ui.failed(label, started_at, f"exit {result.returncode}; log: {result.log_path}")
    return result
