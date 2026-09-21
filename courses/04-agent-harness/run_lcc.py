"""Run one vendored Learn Claude Code chapter in a separate working directory.

Usage from this directory:
    python run_lcc.py s11
    python run_lcc.py s11_background_tasks

This wrapper loads .env from the course directory, locates the requested
chapter, and changes cwd to runtime-workspace before executing code.py.
Changing cwd reduces accidental writes to the course snapshot, but it is not
an OS sandbox and cannot stop absolute-path access from generated commands.
"""

from __future__ import annotations

import os
import runpy
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv


COURSE_ROOT = Path(__file__).resolve().parent
LCC_ROOT = COURSE_ROOT / "learn-claude-code"
RUNTIME_ROOT = COURSE_ROOT / "runtime-workspace"


def resolve_code(argument: str) -> Path:
    candidate = Path(argument)
    if candidate.is_file():
        return candidate.resolve()

    direct = LCC_ROOT / argument
    if direct.is_dir() and (direct / "code.py").is_file():
        return direct / "code.py"

    prefix = argument.split("_", 1)[0].lower()
    if len(prefix) == 3 and prefix.startswith("s") and prefix[1:].isdigit():
        matches = sorted(LCC_ROOT.glob(f"{prefix}_*/code.py"))
        if len(matches) == 1:
            return matches[0]

    raise SystemExit(f"找不到章节：{argument}")


def prepare_runtime() -> None:
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    source_skills = LCC_ROOT / "skills"
    if source_skills.is_dir():
        shutil.copytree(source_skills, RUNTIME_ROOT / "skills", dirs_exist_ok=True)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("用法：python run_lcc.py <章节>，例如 s11")

    load_dotenv(COURSE_ROOT / ".env", override=True)
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("缺少 ANTHROPIC_API_KEY：先复制 .env.example 为 .env 并填写")
    if not os.getenv("MODEL_ID"):
        raise SystemExit("缺少 MODEL_ID：请在 .env 中填写实际支持的模型")

    code = resolve_code(sys.argv[1].replace("\\", "/"))
    prepare_runtime()
    os.environ.setdefault("PYTHONUTF8", "1")
    os.chdir(RUNTIME_ROOT)
    print(f"[run_lcc] chapter={code.parent.name} cwd={RUNTIME_ROOT}")
    runpy.run_path(str(code), run_name="__main__")


if __name__ == "__main__":
    main()
