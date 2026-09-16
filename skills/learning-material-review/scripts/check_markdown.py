#!/usr/bin/env python3
"""检查学习资料中常见的 Markdown 兼容性和结构问题。

该脚本只提供可复现的线索，不代替人工审查教学质量。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HTML_RE = re.compile(r"</?(?:details|summary|strong)(?:\s[^>]*)?>", re.I)
LATEX_RE = re.compile(r"(?<!\\)\$\$?|\\\(|\\\)|\\\[|\\\]")
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def markdown_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix.lower() == ".md" else []
    return sorted(p for p in target.rglob("*.md") if ".git" not in p.parts)


def local_target(raw: str) -> str | None:
    value = raw.strip().strip("<>").split(maxsplit=1)[0]
    if not value or value.startswith(("#", "http://", "https://", "mailto:")):
        return None
    return value.split("#", 1)[0]


def inspect(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    issues: list[tuple[int, str]] = []
    previous_heading = 0
    fence_marker: str | None = None

    for number, line in enumerate(lines, 1):
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            marker = fence.group(1)
            if fence_marker is None:
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                fence_marker = None
            continue
        if fence_marker is not None:
            continue

        # 行内代码中的 Skill 名、命令或字面符号不是数学定界符。
        prose = re.sub(r"`+[^`]*`+", "", line)
        if HTML_RE.search(prose):
            issues.append((number, "包含可能被预览器原样显示的 HTML 标签"))
        if LATEX_RE.search(prose):
            issues.append((number, "包含可能不被目标预览器渲染的 LaTeX 定界符"))

        heading = re.match(r"^(#{1,6})\s+", line)
        if heading:
            level = len(heading.group(1))
            if previous_heading and level > previous_heading + 1:
                issues.append((number, f"标题层级从 H{previous_heading} 跳到 H{level}"))
            previous_heading = level
            if number > 1 and lines[number - 2].strip():
                issues.append((number, "标题前缺少空行"))
            if number < len(lines) and lines[number].strip():
                issues.append((number, "标题后缺少空行"))

        for match in list(LINK_RE.finditer(line)) + list(IMAGE_RE.finditer(line)):
            target = local_target(match.group(1))
            if target:
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    issues.append((number, f"本地链接目标不存在: {target}"))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 Markdown 学习资料的常见机械问题")
    parser.add_argument("target", type=Path, help="Markdown 文件或包含 Markdown 的目录")
    args = parser.parse_args()
    target = args.target.resolve()
    if not target.exists():
        print(f"目标不存在: {target}", file=sys.stderr)
        return 2

    files = markdown_files(target)
    issue_count = 0
    for path in files:
        for line, message in inspect(path):
            issue_count += 1
            print(f"{path}:{line}: {message}")

    print(f"已检查 {len(files)} 个 Markdown 文件，发现 {issue_count} 条线索。")
    return 1 if issue_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
