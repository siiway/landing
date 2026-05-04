#!/usr/bin/env python3
"""Patch python_modules/asgi.py to avoid destroying a pending ASGI task.

This script searches for `asgi.py` under the current repository (or an optional root
path) and updates the request lifecycle so the ASGI background task is awaited
instead of destroyed.

Usage:
    python patch_asgi.py
    python patch_asgi.py /path/to/repo
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

OLD_TASK_DECLARATION = re.compile(
    r"^([ \t]*# Create task to run the application in the background\s*\n)"
    r"([ \t]*app_task\s*=\s*create_proxy\(create_task\(run_app\(\)\)\)\s*\n)"
    r"([ \t]*from workers import wait_until\s*\n)"
    r"([ \t]*wait_until\(app_task\)\s*\n)"
    r"([ \t]*try:\s*\n)"
    r"([ \t]*return await result\s*\n)"
    r"([ \t]*finally:\s*\n)"
    r"([ \t]*app_task\.destroy\(\)\s*\n)",
    re.MULTILINE,
)

REPLACEMENT_BLOCK = (
    "# Create task to run the application in the background\n"
    "    task = create_task(run_app())\n"
    "    app_task = create_proxy(task)\n\n"
    "    from workers import wait_until\n\n"
    "    wait_until(app_task)\n\n"
    "    try:\n"
    "        return await result\n"
    "    finally:\n"
    "        if not task.done():\n"
    "            await task\n"
)

GENERIC_DESTROY_RE = re.compile(
    r"^([ \t]*finally:\s*\n)([ \t]*app_task\.destroy\(\)\s*\n)",
    re.MULTILINE,
)

TASK_DECLARATION_RE = re.compile(
    r"^([ \t]*# Create task to run the application in the background\s*\n)"
    r"([ \t]*app_task\s*=\s*create_proxy\(create_task\(run_app\(\)\)\)\s*\n)"
    r"([ \t]*from workers import wait_until\s*\n)"
    r"([ \t]*wait_until\(app_task\)\s*\n)",
    re.MULTILINE,
)


def find_asgi_files(root: Path) -> Iterable[Path]:
    search_root = root / "python_modules"
    if not search_root.exists():
        search_root = root

    for path in sorted(search_root.rglob("asgi.py")):
        if any(part in {"venv", ".venv", "env", "site-packages", "__pycache__"} for part in path.parts):
            continue
        yield path


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")

    if "app_task.destroy()" not in text:
        return False

    text, count = OLD_TASK_DECLARATION.subn(REPLACEMENT_BLOCK, text)
    if count > 0:
        path.write_text(text, encoding="utf-8")
        return True

    # fallback: only replace the destroy call and task declaration separately if needed.
    text, count_decl = TASK_DECLARATION_RE.subn(
        "# Create task to run the application in the background\n"
        "    task = create_task(run_app())\n"
        "    app_task = create_proxy(task)\n\n"
        "    from workers import wait_until\n\n"
        "    wait_until(app_task)\n",
        text,
    )
    text, count_destroy = GENERIC_DESTROY_RE.subn(
        "    finally:\n"
        "        if not task.done():\n"
        "            await task\n",
        text,
    )

    if count_decl or count_destroy:
        path.write_text(text, encoding="utf-8")
        return True

    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch asgi.py to avoid destroying ASGI tasks.")
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Repository root or folder to search for asgi.py files.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Error: root path does not exist: {root}")
        return 1

    patched = []
    for path in find_asgi_files(root):
        if patch_file(path):
            patched.append(path)

    if not patched:
        print("No matching asgi.py file needed patching.")
        return 0

    print("Patched the following files:")
    for path in patched:
        print(f" - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
